#!/bin/bash

# Input arguments
RESOURCE_GROUP=$1
WEB_APP_NAME=$2


echo " App Service and Plan settings"
az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME \
            --settings @./function_appsettings.json


#echo "create ZIP file"
zip -r deploy.zip  function_app.py host.json requirements.txt

echo "Deploy Function App"
az functionapp deployment source config-zip -g $RESOURCE_GROUP  -n $WEB_APP_NAME --src deploy.zip  --build-remote  true

echo "Setup complete."


#npm install -g azure-functions-core-tools@4
#func azure functionapp publish  $WEB_APP_NAME --no-zip -i
