#!/bin/bash

# Input arguments
RESOURCE_GROUP=
REGISTRY=
WEB_APP_NAME=



#echo " App Service and Plan settings"
#az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME \
#            --settings @appsettings.json


echo "create docker image"

pushd ../src_vanna
az acr build --resource-group $RESOURCE_GROUP --registry $REGISTRY --image survey-assist:latest .

echo "Restart"
az webapp restart --resource-group $RESOURCE_GROUP  --name $WEB_APP_NAME 

popd

echo "Setup complete."
