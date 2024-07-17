#!/bin/bash

# Input arguments
RESOURCE_GROUP=WSP
WEB_APP_NAME=wsp-survey-en


echo " App Service and Plan configuration"
az webapp config set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME \
                    --startup-file "chainlit run app.py --port 8000 --host 0.0.0.0"

#echo " App Service and Plan settings"
#az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME \
#            --settings @appsettings.json


echo "create ZIP file"

pushd ../src
zip -r deploy.zip  * assistant_flow/* survey_data_insights/* -x **__pycache__\* **/**/__pycache__\*  **/.chainlit\*

echo "ZIP Deploy"
az webapp deploy --resource-group $RESOURCE_GROUP  --name $WEB_APP_NAME --src-path deploy.zip

popd

echo "Setup complete."
