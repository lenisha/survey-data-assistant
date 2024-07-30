#__import__('pysqlite3')
#import sys
#sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')


from vanna.flask import VannaFlaskApp
from vanna.openai import OpenAI_Chat
from openai import AzureOpenAI
from vanna.chromadb import ChromaDB_VectorStore
import os, json
from dotenv import load_dotenv
import chromadb
from vanna.utils import deterministic_uuid

load_dotenv(override=True)

   
class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):

    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        azure_client  = AzureOpenAI(
            api_key = os.getenv("OPENAI_API_KEY"),
            azure_endpoint = os.getenv("OPENAI_API_BASE"),
            api_version = os.getenv("OPENAI_API_VERSION")
        )
        OpenAI_Chat.__init__(self, client=azure_client, config=config) # Make sure to put your AzureOpenAI client here


def setup_training_data(vn: MyVanna, force_retrain = False):

    # training_data is DataFrame 
    training_data = vn.get_training_data()

    if len(training_data) > 0 and not force_retrain:
        print(" Trining data exists and not forced")
        return

    
    df_information_schema = vn.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS")
    # This will break up the information schema into bite-sized chunks that can be referenced by the LLM

    plan = vn.get_training_plan_generic(df_information_schema)
    vn.train(plan=plan)

    # The following are methods for adding training data. Make sure you modify the examples to match your database.

    # Sometimes you may want to add documentation about your business terminology or definitions.
    vn.train(documentation="Labels represent the main topics or themes described in the survey data. These are used to categorize the data for analysis.")

    # You can also add SQL queries to your training data. This is useful if you have some queries already laying around. You can just copy and paste those from your editor to begin generating new SQL.
    vn.train(sql="SELECT * FROM survey_data WHERE Score > 5")
    vn.train(sql="SELECT COUNT(Topics) AS TopicCount FROM survey_data WHERE Survey_Location LIKE '%UK%'")
    vn.train(documentation="""
                You are expert in SQL database queries. Given an input question, create a syntactically correct SQL query to run and return ONLY the generated Query and nothing else.
                Follow these Instructions for creating syntactically correct SQL query:
                - In your reply only provide the SQL query with no extra formatting.
                - When asked about topics or themes use column Label in "labels" table and join it with "survey_data" table using ID field
                - When retrieving most common or main occurrences of data, return only top 40 most frequent ( use sqldb syntax `select top 40` )
                - Find items that include term or related to term by comparing suitable field using SQL syntax LIKE '%term%'
                - If resulting query would return too much data attempt to aggregate and group data either by dates or by other category like Score or Survey Location
                - Filter out empty or null values or 'no topics' from the 'Labels'
                - Do not use SQL server keywords as table names or field aliases
                - Lables are the same as topics or themes
                - **MUST** Double check SQL syntax before sending the query
                """)



### INITIALIZING ---------------------------------------
vn = MyVanna(config={'path': os.getenv("CHROMA_PATH") ,
                        'model': 'gpt-4o',
                        'temperature': 0.0,
                        'max_tokens': 1000})
vn.connect_to_mssql(odbc_conn_str=os.getenv("SQL_CONNECTION_STRING")) # You can use the ODBC connection string here

setup_training_data(vn, os.getenv("FORCE_RETRAIN", False))

print("Starting Flask application")
vanna_app = VannaFlaskApp(vn,
                logo = "https://www.wsp.com/-/media/who-we-are/global/image/wsp-logo/img-png-wsp-black.png",
                allow_llm_to_see_data=True,
                sql=False, 
                summarization=False, 
                suggested_questions = True,
                ask_results_correct=False,
                redraw_chart=False,
                csv_download=False,
                followup_questions=True,
                title="Welcome to WSP Analytics")


# To expose it to gunicorn
app = vanna_app.flask_app
print(f"Starting Flask  {app}")

if __name__ == '__main__':
    vanna_app.run(debug=True)