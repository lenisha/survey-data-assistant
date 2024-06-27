#!/bin/bash

# Input arguments
RESOURCE_GROUP=$1
WEB_APP_NAME=$2

OPENAI_API_BASE=""
OPENAI_API_KEY=""
OPENAI_ASSISTANT_ID=""
OPENAI_ASSISTANT_MODEL=""
APPINSIGHTS_CONNECTION_STRING=""
SQL_CONNECTION_STRING=""


echo " App Service and Plan configuration"
az webapp config set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --startup-file "chainlit run app.py --port 8000 --host 0.0.0.0"

echo " App Service and Plan settings"
az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME \
 --settings OPENAI_API_BASE=$OPENAI_API_BASE OPENAI_API_KEY=$OPENAI_API_KEY OPENAI_ASSISTANT_ID=$OPENAI_ASSISTANT_ID OPENAI_ASSISTANT_MODEL=$OPENAI_ASSISTANT_MODEL OPENAI_ANALYST_CHAT_MODEL=$OPENAI_ASSISTANT_MODEL APPINSIGHTS_CONNECTION_STRING=$APPINSIGHTS_CONNECTION_STRING SQL_CONNECTION_STRING=$SQL_CONNECTION_STRING @appsettings.json


echo "create ZIP file"

pushd ../src
zip -r deploy.zip  * assistant_flow/* survey_data_insights/* -x **__pycache__\* **/**/__pycache__\*  **/.chainlit\*

echo "ZIP Deploy"
az webapp deploy --resource-group $RESOURCE_GROUP  --name $WEB_APP_NAME --src-path deploy.zip

popd

echo "Setup complete."
