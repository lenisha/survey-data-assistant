__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')


from vanna.flask import VannaFlaskApp
from vanna.openai import OpenAI_Chat
from openai import AzureOpenAI
from vanna.chromadb import ChromaDB_VectorStore
import os
from dotenv import load_dotenv
import chromadb

load_dotenv(override=True)


try:
    class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
        def __init__(self, config=None):
            ChromaDB_VectorStore.__init__(self, config=config)
            azure_client  = AzureOpenAI(
                api_key = os.getenv("OPENAI_API_KEY"),
                azure_endpoint = os.getenv("OPENAI_API_BASE"),
                api_version = os.getenv("OPENAI_API_VERSION")
            )
            OpenAI_Chat.__init__(self, client=azure_client, config=config) # Make sure to put your AzureOpenAI client here

    vn = MyVanna(config={'path': os.getenv("CHROMA_PATH") ,
                         'model': 'gpt-4o',
                         'temperature': 0.0,
                         'max_tokens': 1000,})
    vn.connect_to_mssql(odbc_conn_str=os.getenv("SQL_CONNECTION_STRING")) # You can use the ODBC connection string here

    #df_information_schema = vn.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS")
    # This will break up the information schema into bite-sized chunks that can be referenced by the LLM
    
    #plan = vn.get_training_plan_generic(df_information_schema)
    
    
    # The following are methods for adding training data. Make sure you modify the examples to match your database.

    # DDL statements are powerful because they specify table names, colume names, types, and potentially relationships
    vn.train(ddl="""
        CREATE TABLE survey_data (
                [ID] [int] IDENTITY(1,1) NOT NULL,
                [Comment] [nvarchar](4000) NULL,
                [Date] [date] NULL,
                [Question] [nvarchar](550) NULL,
                [Score] [float] NULL,
                [Group_Name] [nvarchar](550) NULL,
                [Driver_Value] [nvarchar](550) NULL,
                [Topics] [nvarchar](600) NULL,
                [Survey_Location] [nvarchar](250) NULL,
                [Labels] [nvarchar](950) NULL,
                [Sentiment] [nvarchar](650) NULL,
                [File_Name] [nvarchar](650) NULL,
            )
    """)

    # Sometimes you may want to add documentation about your business terminology or definitions.
    vn.train(documentation="Labels represent the main topics or themes described in the survey data. These are used to categorize the data for analysis. The labels columnm is a free-form text field that can contain multiple labels separated by semicolon.")

    # You can also add SQL queries to your training data. This is useful if you have some queries already laying around. You can just copy and paste those from your editor to begin generating new SQL.
    vn.train(sql="SELECT * FROM survey_data WHERE Score > 5")
    vn.train(documentation="""
                Follow these Instructions for creating syntactically correct SQL query:
                - In your reply only provide the SQL query with no extra formatting.
                - To avoid issues with apostrophes, when referring to labels, always use double-quotes, for instance:
                SELECT SUM(Scores) FROM survey_data WHERE Score = "9" AND Labels LIKE "Projectc'S Issue"
                - When asked about topics or themes use column Labels
                - Make sure to split labels by semicolon to provide separate topics (CROSS APPLY STRING_SPLIT(Labels, ';'). Filter out empty topic responses. 
                - **MUST** Double check SQL
             """)
    vn.train(sql="""
                    SELECT
                    value AS Topic,
                    COUNT(*) AS TopicCount
                    FROM
                    survey_data
                    CROSS APPLY
                    STRING_SPLIT(Labels, ";")
                    WHERE
                    value <> ""
                    GROUP BY
                    value
                    ORDER BY
                    TopicCount DESC;
             """)

    app = VannaFlaskApp(vn,
                        allow_llm_to_see_data=True,
                        sql=False, 
                        summarization=False, 
                        ask_results_correct=False,
                        redraw_chart=False,
                        title="Welcome to WSP Analytics")

    if __name__ == '__main__':
        app.run(debug=True)

except Exception as e:
    print(e)



