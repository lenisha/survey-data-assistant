import os
import pathlib
import pyodbc
from sqlalchemy import create_engine
import urllib
from openai import AzureOpenAI
import pandas as pd
from promptflow.tracing import trace
import json
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from .system_message import system_message

from typing import TypedDict
class Result(TypedDict):
    data: dict
    error: str
    query: str
    execution_time: float

# Callable class with @trace decorator on the __call__ method
class SurveyDataInsights:

    """
    SurveyDataInsights tool. You can use this tool as a standalone flow to retrieve sales data
    with natural language queries. In this example, it's also called by the assistant API for a
    full end-to-end assistant experience.
    """

    def __init__(self, model_type="azure_openai"):
        self.model_type = model_type

    @trace
    def __call__(self, *, question: str, **kwargs) -> Result:

        if self.model_type == "azure_openai":
            client = AzureOpenAI(
                                api_key = os.getenv("OPENAI_API_KEY"),
                                azure_endpoint = os.getenv("OPENAI_API_BASE"),
                                api_version = os.getenv("OPENAI_API_VERSION")
                            )
        else:
            endpoint = os.getenv(f"AZUREAI_{self.model_type.upper()}_URL")
            key = os.getenv(f"AZUREAI_{self.model_type.upper()}_KEY")
            print("endpoint", endpoint)
            print("key", key)
            client = ChatCompletionsClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(key),
            )
        # Code to get time to execute the function
        import time
        start = time.time()
        
        print("getting survey data insights")
        print("question", question)

        if self.model_type == "azure_openai":
            messages = [{"role": "system", "content": system_message}]
        
            messages.append({"role": "user", "content": f"{question}\nGive only the query in SQL format"})

            response = client.chat.completions.create(
                model= os.getenv("OPENAI_ANALYST_CHAT_MODEL"),
                messages=messages, 
                max_tokens=800,
                temperature=0.0,
                top_p=0.95
            )
        elif self.model_type.lower() == "phi3_mini":
            combined_message = UserMessage(content=f"{system_message}\n\n{question}\nGive only the query in SQL format")
            messages = [combined_message]
            response = client.create(messages=messages, temperature=0, max_tokens=1000)
        elif self.model_type.lower() == "phi3_medium":
            combined_message = UserMessage(content=f"{system_message}\n\n{question}\nGive only the query in SQL format")
            messages = [combined_message]
            response = client.create(messages=messages, temperature=0, max_tokens=1000)
        else:
            system_message_obj = SystemMessage(content=system_message)
            user_message_obj = UserMessage(content=f"{question}\nGive only the query in SQL format")
            messages = [system_message_obj, user_message_obj]
            response = client.create(messages=messages, temperature=0, max_tokens=1000)

        message = response.choices[0].message

        query :str = message.content

        if query.startswith("```sql") and query.endswith("```"):
            query = query[6:-3].strip()

        try:
            print("*****  Executing SQL query:", query)
            data = self.query_db(query)
        except Exception as e:
            end = time.time()
            execution_time = round(end - start, 2)
            print("Execution time:", execution_time)
            print(e)
            return {"data": None, "error": f"{e}", "query": query, "execution_time": execution_time}

        end = time.time()
        execution_time = round(end - start, 2)

        print(f"retrieved records {len(data)}")

        return {"data": data, "error": str(None), "query": query, "execution_time": execution_time}
    
    @trace
    def query_db(self, query: str) -> dict:
        # Connection string
        conn_str = os.getenv("SQL_CONNECTION_STRING")
        # Create the connection string
        params = urllib.parse.quote_plus(conn_str)
        # Create the SQLAlchemy engine
        sql_connection = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
        # Create the connection        
        #sql_connection = pyodbc.connect(conn_str)

        # Use pandas to execute the query and return a DataFrame
        df = pd.read_sql(query, sql_connection)

        return df.to_dict(orient='records')

 
if __name__ == "__main__":

    models = ["azure_openai", "phi3_mini", "phi3_medium", "cohere_chat", "mistral_small", "mistral_large", "llama3"]
    for model in models:
        print("="*50)
        print("model", model)
        sdi = SurveyDataInsights(model_type=model)
        result = sdi(question="for March 2024 Query the average number of responses grouped by Score")
        result["data"] = None
        print("execution_time:", result['execution_time'])
        print("query", result['query'])
