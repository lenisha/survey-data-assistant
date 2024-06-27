#!/bin/bash

# Input arguments
RESOURCE_GROUP=$2
REGION=$3
SUBSCRIPTION_ID=$1

# VNet and Subnet configuration
VNET_NAME="MyVNet"
SUBNET_NAME="MySubnet"
VNET_INTEGRATION_SUBNET="MyWebAppSubnet"
PRIVATE_ENDPOINT_NAME="MyPrivateEndpoint-wsp-en"
PRIVATE_DNS_ZONE="privatelink.database.windows.net"

# App Service and Plan configuration
APP_SERVICE_PLAN="MyAppServicePlan"
WEB_APP_NAME="MyWebApp-wsp-en"
PYTHON_VERSION="3.12"

# Database configuration
SQL_SERVER_NAME="MySqlServer-eneros"
SQL_DATABASE_NAME="MySqlDatabase"
SQL_ADMIN_USER="sqlAdmin"
SQL_ADMIN_PASSWORD="ChangeYourPassword123!"

echo "Create Resource Group"
az group create --name $RESOURCE_GROUP --location $REGION

echo "Create Virtual Network and Subnets"
az network vnet create --name $VNET_NAME --resource-group $RESOURCE_GROUP --location $REGION --address-prefixes 10.0.0.0/16 --subnet-name $SUBNET_NAME --subnet-prefix 10.0.1.0/24

echo "Create a subnet for Web App VNet integration"
az network vnet subnet create --vnet-name $VNET_NAME --resource-group $RESOURCE_GROUP --name $VNET_INTEGRATION_SUBNET --address-prefix 10.0.2.0/24

echo "Create App Service Plan"
az appservice plan create --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --is-linux --sku B1 --location $REGION

echo "Create Web App with Python runtime"
az webapp create --name $WEB_APP_NAME --plan $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --runtime "PYTHON|$PYTHON_VERSION"


echo "Integrate Web App with VNet"
az webapp vnet-integration add --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP --vnet $VNET_NAME --subnet $VNET_INTEGRATION_SUBNET

echo "Create SQL Server"
az sql server create --name $SQL_SERVER_NAME --resource-group $RESOURCE_GROUP --location $REGION --admin-user $SQL_ADMIN_USER --admin-password $SQL_ADMIN_PASSWORD

echo " Create SQL Database"
az sql db create --resource-group $RESOURCE_GROUP --server $SQL_SERVER_NAME --name $SQL_DATABASE_NAME --service-objective Basic

echo " Create Private Endpoint"
az network private-endpoint create \
  --name $PRIVATE_ENDPOINT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $REGION \
  --subnet $SUBNET_NAME \
  --vnet-name $VNET_NAME \
  --private-connection-resource-id "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Sql/servers/$SQL_SERVER_NAME" \
  --group-id sqlServer \
  --connection-name "$SQL_SERVER_NAME-Connection"

# Create Private DNS Zone
az network private-dns zone create --resource-group $RESOURCE_GROUP --name $PRIVATE_DNS_ZONE

# Link VNet to the Private DNS Zone
az network private-dns link vnet create --resource-group $RESOURCE_GROUP --zone-name $PRIVATE_DNS_ZONE --name "${VNET_NAME}-link" --virtual-network $VNET_NAME --registration-enabled false

# Get NIC ID and Private IP of Private Endpoint
NIC_ID=$(az network private-endpoint show --name $PRIVATE_ENDPOINT_NAME --resource-group $RESOURCE_GROUP --query 'networkInterfaces[0].id' -o tsv)
PRIVATE_IP=$(az network nic show --ids $NIC_ID --query 'ipConfigurations[0].privateIpAddress' -o tsv)

echo "Private IP: $PRIVATE_IP"
# Create DNS record for SQL Server in Private DNS Zone
az network private-dns record-set a add-record --record-set-name $SQL_SERVER_NAME --zone-name $PRIVATE_DNS_ZONE --resource-group $RESOURCE_GROUP --ipv4-address $PRIVATE_IP

echo "Setup complete."
