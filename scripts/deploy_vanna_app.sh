#!/bin/bash

# Input arguments
RESOURCE_GROUP=WSP
WEB_APP_NAME=wsp-survey-en-vanna


echo " App Service and Plan configuration"
az webapp config set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME \
                    --startup-file "./startup.sh"

#echo " App Service and Plan settings"
#az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME \
#            --settings @appsettings.json


echo "create ZIP file"

pushd ../src_vanna
zip -r deploy.zip  app.py requirements.txt startup.sh

echo "ZIP Deploy"
az webapp deploy --resource-group $RESOURCE_GROUP  --name $WEB_APP_NAME --src-path deploy.zip 

popd

echo "Setup complete."
