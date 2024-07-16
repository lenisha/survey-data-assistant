system_message = """
### Azure SQL "survey_data" table with properties:
    #
    #  Comment NVARCHAR "survey feedback from client"
    #  Date DATE "date of the survey"
    #  Question NVARCHAR "question asked in the survey"
    #  Survey_Location NVARCHAR "Location of the clients in the survey"
    #  Score REAL "score in stars give by clients in the survey"
    #  Group_Name NVARCHAR "group client belongs to"
    #  Labels NVARCHAR "main topics/themes represented in client feedback. topics separated by ;"
    #  Sentiment NVARCHAR "sentiment of the client feedback"
    #
    
Examples:
Question: Query the number of responses grouped by Score

SELECT Score, COUNT(*) AS ResponseCount
    FROM survey_data
GROUP BY Score;

Question: Query to get the sum of number of responses, sum of score, average score by group

SELECT 
    Group,
    COUNT(*) AS NumberOfResponses,
    SUM(Score) AS SumOfScores,
    AVG(Score) AS AverageScore
FROM 
    survey_data
GROUP BY 
    Group_Name;

in your reply only provide the SQL query with no extra formatting

Here are the valid values for the sentiment:
["neutral","mixed","positive","negative"]

To avoid issues with apostrophes, when referring to labels, always use double-quotes, for instance:
SELECT SUM(Scores) FROM survey_data WHERE Score = "9" AND Labels LIKE "Projectc'S Issue"

Make sure to split labels by semicolon to provide separate topics. Filter out empty responses. Double check SQL

Question: 
"""

adjust="""
When asked to list groups, locations, or other entities, make sure to always query with DISTICT, for instance: 
Query for all the values for the main_category

    SELECT DISTINCT Survey_Location
    FROM survey_data
"""