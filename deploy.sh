#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Define variables
RESOURCE_GROUP="PodManager"
REGISTRY_NAME="podmanageracr"
IMAGE_NAME="podmanager"
WEBAPP_NAME="podmanager"
APP_SERVICE_PLAN="podmanagersp"
LOCATION="northeu" # e.g., "eastus"

# Step 1: Check if Resource Group exists
echo "Checking if Resource Group '$RESOURCE_GROUP' exists..."
if ! az group exists --name $RESOURCE_GROUP; then
    echo "Creating Resource Group '$RESOURCE_GROUP' in $LOCATION..."
    az group create --name $RESOURCE_GROUP --location $LOCATION --output none
else
    echo "Resource Group '$RESOURCE_GROUP' already exists."
fi

# Step 2: Check if Azure Container Registry (ACR) exists
echo "Checking if Azure Container Registry '$REGISTRY_NAME' exists..."
if ! az acr show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --output none; then
    echo "Creating Azure Container Registry '$REGISTRY_NAME'..."
    az acr create --resource-group $RESOURCE_GROUP --name $REGISTRY_NAME --sku Basic --output none
else
    echo "Azure Container Registry '$REGISTRY_NAME' already exists."
fi

# Step 3: Log in to Azure Container Registry (ACR) using credentials from .env
echo "Logging in to ACR '$REGISTRY_NAME' using credentials from .env..."
if [ -z "$ACR_USERNAME" ] || [ -z "$ACR_PASSWORD" ]; then
    echo "❌ ERROR: ACR_USERNAME or ACR_PASSWORD is not set in the .env file."
    exit 1
fi
echo "$ACR_PASSWORD" | docker login $REGISTRY_NAME.azurecr.io --username $ACR_USERNAME --password-stdin

# Step 4: Check if the "podmanagerlive" repository exists in ACR
echo "Checking if repository 'podmanagerlive' exists in ACR..."
if az acr repository show --name $REGISTRY_NAME --repository podmanagerlive --output none; then
    echo "Repository 'podmanagerlive' exists. Deleting repository and its contents..."
    az acr repository delete --name $REGISTRY_NAME --repository podmanagerlive --yes --output none
else
    echo "Repository 'podmanagerlive' does not exist. No need to delete."
fi

# Step 5: Build Docker Image
echo "Building Docker image '$IMAGE_NAME'..."
docker build -t $IMAGE_NAME .

# Step 6: Tag Docker Image for ACR
echo "Tagging Docker image '$IMAGE_NAME' with ACR tag..."
docker tag $IMAGE_NAME $REGISTRY_NAME.azurecr.io/$IMAGE_NAME:latest

# Step 7: Push Docker Image to ACR
echo "Pushing Docker image to ACR..."
docker push $REGISTRY_NAME.azurecr.io/$IMAGE_NAME:latest

# Step 8: Check if App Service Plan exists
echo "Checking if App Service Plan '$APP_SERVICE_PLAN' exists..."
if ! az appservice plan show --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --output none; then
    echo "Creating App Service Plan '$APP_SERVICE_PLAN'..."
    az appservice plan create --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --sku B1 --is-linux --output none
else
    echo "App Service Plan '$APP_SERVICE_PLAN' already exists."
fi

# Step 9: Check if Web App exists
echo "Checking if Web App '$WEBAPP_NAME' exists..."
if ! az webapp show --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP --output none; then
    echo "Creating Web App '$WEBAPP_NAME' for container deployment..."
    az webapp create --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --name $WEBAPP_NAME --deployment-container-image-name $REGISTRY_NAME.azurecr.io/$IMAGE_NAME:latest --output none
else
    echo "Web App '$WEBAPP_NAME' already exists."
fi

# Step 10: Configure Web App to use ACR with credentials from .env
echo "Configuring Web App to use Docker image from ACR..."
az webapp config container set --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP \
  --container-registry-url https://$REGISTRY_NAME.azurecr.io \
  --container-image-name $REGISTRY_NAME.azurecr.io/$IMAGE_NAME:latest \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password $ACR_PASSWORD

# Step 11: Check the status of the Web App
echo "Web App '$WEBAPP_NAME' is deployed successfully. Checking the status..."
az webapp show --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP --output table

# Step 12: Optionally, open the Web App in a browser
echo "Opening Web App in the default browser..."
open https://$WEBAPP_NAME.azurewebsites.net
