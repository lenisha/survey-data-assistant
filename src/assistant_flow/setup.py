# this script creates an assistant with a code interpreter and a function tool 
# to do data analytics on sales data.

import json, yaml
from dotenv import load_dotenv
from openai import AzureOpenAI
import os

load_dotenv(override=True)

def show_json(obj):
    print(json.loads(obj.model_dump_json()))

def show_yaml(obj):
    print(yaml.dump(json.loads(obj.model_dump_json()), indent=4))

print("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
print("OPENAI_API_BASE", os.getenv("OPENAI_API_BASE"))
print("OPENAI_API_VERSION", os.getenv("OPENAI_API_VERSION"))
client  = AzureOpenAI(
    api_key = os.getenv("OPENAI_API_KEY"),
    azure_endpoint = os.getenv("OPENAI_API_BASE"),
    api_version = os.getenv("OPENAI_API_VERSION")
)

tools = [
    {
        "type": "code_interpreter"
    },
    {
        "type": "function",
        "function": {
            "name": "survey_data_insights",
            "description": """
   get some data insights about the survey data. This tool has tabluar information in the following structure:
      Comment NVARCHAR "survey feedback from client"
      Date DATE "date of the survey"
      Question NVARCHAR "question asked in the survey"
      Survey_Location NVARCHAR "Location of the clients in the survey"
      Score REAL "score in stars give by clients in the survey"
      Group_Name NVARCHAR "group client belongs to"
      Labels NVARCHAR "main topics/themes represented in client feedback. topics separated by ;"
      Sentiment NVARCHAR "sentiment of the client feedback"
  
  you can ask questions like:
  - what was the total number of responses in march 2024 by location
  - which location has the least average score
  - what are the topics with the negative sentiment
  If you are unsure of the data available, you can ask for a list of locations, scores, etc.
  - query for all the values for the table
  The data will be returned in a json format in the data property of the returned object with the query used 
  to get the data in the query property.
  If a query cannot be answered, the tool will return a message in the error property of the returned object. 
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question you want to ask the tool in plain English. e.g. 'what is the average score for each location'",
                    }
                },
                "required": ["question"],
            },
        },
    }
]

instructions="""
You are a helpful assistant that helps the user potentially with the help of some functions.

If you are using multiple tools to solve a user's task, make sure to communicate 
information learned from one tool to the next tool.
First, make a plan of how you will use the tools to solve the user's task and communicated
that plan to the user with the first response. Then execute the plan making sure to communicate
the required information between tools since tools only see the information passed to them;
They do not have access to the chat history.
If you think that tool use can be parallelized (e.g. to get weather data for multiple cities) 
make sure to use the multi_tool_use.parallel function to execute.

Only use a tool when it is necessary to solve the user's task. 
Don't use a tool if you can answer the user's question directly.
Only use the tools provided in the tools list -- don't make up tools!!
If you are not getting the right information from a tool, make sure to ask the user for clarification. 
Do not just return the wrong information. Do not make up information.

Anything that would benefit from a tabular presentation should be returned as markup table.
"""

assistant = client.beta.assistants.create(
    name="Survey Data Assistant",
    instructions=instructions,
    model=os.environ["OPENAI_ASSISTANT_MODEL"],
    tools=tools, temperature=0 
)
show_json(assistant)

print("Assistant created with id", assistant.id)
print("add the following to your .env file")
print(f'OPENAI_ASSISTANT_ID="{assistant.id}"')