import azure.functions as func
import logging
import pandas as pd
import io,os 
import pyodbc
from azure.core.credentials import AzureKeyCredential  
from openai import AzureOpenAI

app = func.FunctionApp()

# OpenAI API credentials
AZURE_OPENAI_SERVICE = os.getenv("AZURE_OPENAI_SERVICE")
AZURE_OPENAI_GPT_DEPLOYMENT = os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT","gpt-4o")
AZURE_OPENAI_SERVICE_KEY = os.getenv("AZURE_OPENAI_SERVICE_KEY")
FORCE_REWRITE = os.getenv("FORCE_REWRITE", False)
conn_str = os.environ["SQL_CONNECTION_STRING"]

openai_client = AzureOpenAI (
            api_version="2023-07-01-preview",
            api_key=AZURE_OPENAI_SERVICE_KEY,
            azure_endpoint=f"https://{AZURE_OPENAI_SERVICE}.openai.azure.com"
        )

def create_table_ifnotexists(conn):
        # Check for table existence
    cursor = conn.cursor()    
    table_name = 'survey_data'

    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = ?
        """, (table_name,))
    result = cursor.fetchone()

    if result[0] == 1:
        logging.info(f"Table '{table_name}' exists.")
    else:
        logging.info(f"Table '{table_name}' does not exist.")
        # Create table if it does not exist
        cursor.execute("""
                CREATE TABLE [survey_data] (
                [ID] [int] IDENTITY(1,1) PRIMARY KEY,
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
                ) ON [PRIMARY]"""
            ) 
        conn.commit()
        logging.info(f"Table '{table_name}' created.")

        cursor.execute("""
            -- Single Column Index on 'Score'
            CREATE INDEX idx_score ON survey_data (Score);

            -- Single Column Index on 'Survey_Location'
            CREATE INDEX idx_survey_location ON survey_data (Survey_Location);

            -- Composite Index on both 'Score' and 'Survey_Location'
            CREATE INDEX idx_score_location ON survey_data (Score, Survey_Location);
            """)
        conn.commit()
        logging.info(f"Indexes created.")

# Function to check if a comment exists in the database
def comment_exists(text, file_name, conn):
    
    cursor = conn.cursor()
    
    if ( len(text) > 800 ):
        text = text[:800] + "%"

    # SQL query to check if the comment exists
    query = "SELECT TOP 1 * FROM survey_data WHERE Comment LIKE ? and File_Name = ?"
    
    # Execute the query with the comment
    cursor.execute(query, (text, file_name, ))
    
    # Fetch the result
    results = cursor.fetchone()
    
    if results is None:
        return -1
    else:
        return results[0]  #return ID
    
def send_message(messages, model_name, max_response_tokens=150):
    try:
        response = openai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.0,
            max_tokens=max_response_tokens,
            top_p=0.9,
            frequency_penalty=0,
            presence_penalty=0,
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.warning(f"An error occurred: {e}")
        return ''


def summarize_text(text):

    SUMMARIZE_TEMPLATE_V2 = """ 
        Identify the main themes in these customer survey responses. 
        Remove words like articles and prepositions.
        Capture in key themes sentiment of the feedback and preserve or add words that describe sentiment and adjectives like Less, Lack, More, Great etc.
        Topics should be in English even if feedback is in different language

        Make it concise list of 3 most important themes/key topics in customer feedback sperated by ';'
        Make each topic short - few words" and informative without too much explanation. For example:    'service'; 'product'; "great support"; "slow access"; "technical issue", "software training issue"

        Enclose topics in ', Separate each topic with ';'. **Do not** use bullets or lists in the response. 
        Do not use any other characters or words aside from the topics.

        If not sufficient information for extraction, answer with empty topic ''
    """

    SENTIMENT_TEMPLATE = """
        Evaluate the sentiment in these feedback comments from survey responses. Classify the text into: neutral, negative, mixed or positive; unknown if sentiment is not clear.

        For example:  
        Feedback is: Service was as expected. I am planning another order from WSP. I liked the quality of what I bought.  
        Answer: positive

        Feedback is : Lack of effective support and void in local technical leadership for Horizon transition. No improvements 6 weeks into transition - still can't see budgets or project to date spent, etc
        Answer: negative

        Feedback is: Yes
        Answer: positive

        Feedback is: I am not sure what you are asking
        Answer: uknown

        Do not provide exaplantion. Only category from the set: neutral, negative, mixed, positive or unknown.
        Provide just one overall sentiment for the entire feedback. Do not include quotes or explanation.
    """

    logging.info(f"Summarizing text: {text}")
    # check if its Nan
    if text is None:
        return ""
    #print(f"Summarizing text: {text}")
    messages=[
                    {"role": "system", "content": SUMMARIZE_TEMPLATE_V2 },
                    {"role": "user", "content": text}
             ]
    response = send_message(messages, model_name=AZURE_OPENAI_GPT_DEPLOYMENT, max_response_tokens=500)

    logging.info(f"Summarized text: {response}")


    messages=[
                    {"role": "system", "content": SENTIMENT_TEMPLATE },
                    {"role": "user", "content": text}
             ]
    sentiment = send_message(messages, model_name=AZURE_OPENAI_GPT_DEPLOYMENT, max_response_tokens=500)
    # if sentiment is not part of [unknown, positive , mixed], set it to unknown
    if sentiment not in ["unknown", "positive", "mixed", "negative", "neutral"]:
        sentiment = "unknown"

    logging.info(f"Sentiment: {sentiment}")

    return f"{response}", f"{sentiment}"


#####  FUNCTION        

@app.blob_trigger(arg_name="myblob", path="surveydata",
                               connection="Monitor_STORAGE") 
def blob_trigger(myblob: func.InputStream):
    logging.info(f"Python blob trigger function processed blob"
                f"Name: {myblob.name}"
                f"Blob Size: {myblob.length} bytes")
    # Read blob content into a DataFrame
    blob_data = myblob.read()  # Read blob content
    data_bytes = io.BytesIO(blob_data)  # Convert to BytesIO object
    df = pd.read_excel(data_bytes)  # Load data into DataFrame assuming Excel format

    # Log DataFrame info 
    logging.info(f"DataFrame loaded with {len(df)} rows and {len(df.columns)} columns")
    logging.info( df.columns)
    # Drop columns that start with 'Unnamed'
    df = df.loc[:, ~df.columns.str.startswith('Unnamed')]
    logging.info(df.columns)

  
     # Connect to the SQL database
    conn = pyodbc.connect(conn_str)
    create_table_ifnotexists(conn)

    # Insert data into the table
    cursor = conn.cursor()
    cursor.fast_executemany = True

    batch_size = 25  # Number of rows to insert in each batch
    batch_data = []
    for index, row in df.iterrows():
        ## SUMMARIZE DATA
        try:
            comment = row['Comment'] if pd.notna(row['Comment']) else ''
            comment_id = comment_exists(text = comment,file_name=myblob.name,conn=conn)
            if comment == '' or comment_id != -1:
                logging.info(f"Comment exists in the database: {index}")
                continue
            # Summarize_text is a function that summarizes the 'Comment' column
            summarized_text, sentiment = summarize_text(row['Comment']) if pd.notna(row['Comment']) else ('','')
        except Exception as e:
            logging.warning(f"An error occurred trying to summarize the data: {e} {row['Comment']}") 
            summarized_text = ''
            sentiment = ''
        
        # Prepare the data tuple for insertion
        score = float(row['Score']) if pd.notna(row['Score']) else 0.0
        topics = row['Topics'] if pd.notna(row['Topics']) else ''
        data_tuple = (row['Comment'], row['Round Date'], row['Question'], score, row['Group'], row['Driver/Value'], topics, row['Survey Location'], summarized_text, sentiment, myblob.name)
        
        ## INSERT TO SQL DATA
        try:
            # Add the current row's data tuple to the batch
            batch_data.append(data_tuple)
            # When batch size is reached, execute insert for the batch
            if len(batch_data) == batch_size:
                cursor.executemany("""
                    INSERT INTO survey_data ([Comment], [Date], [Question], [Score], [Group_Name], [Driver_Value], [Topics], [Survey_Location], [Labels], [Sentiment], [File_Name])
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", batch_data)
                conn.commit()  # Commit the transaction
                logging.info(f"Inserted batch of {batch_size} rows")
                batch_data = []  # Reset the batch data list
        except Exception as e:
            logging.warning(f"An error occurred trying to insert the data: {e}")  
            batch_data = []  # Reset the batch data list      
            continue

    try:
        # Insert any remaining rows in the last batch
        if batch_data:
            cursor.executemany("""
                INSERT INTO survey_data ([Comment], [Date], [Question], [Score], [Group_Name], [Driver_Value], [Topics], [Survey_Location], [Labels], [Sentiment], [File_Name])
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", batch_data)
            conn.commit()
            logging.info(f"Inserted final batch of {len(batch_data)} rows")
    except Exception as e:        
        logging.warning(f"An error occurred trying to insert the final batch of data: {e}")        
        
    logging.info("All rows have been inserted.")
