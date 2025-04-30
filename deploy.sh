#!/bin/bash

# Load environment variables from .env file using dotenv
if [ -f .env ]; then
    echo "Loading environment variables from .env file using dotenv..."
    if ! dotenv -f .env list > /dev/null 2>&1; then
        echo "❌ ERROR: Invalid syntax in .env file. Please check for invalid lines or characters."
        exit 1
    fi
    export $(dotenv -f .env list | xargs)
else
    echo ".env file not found. Exiting..."
    exit 1
fi

# Check if ACR credentials are set
if [ -z "$ACR_USERNAME" ] || [ -z "$ACR_PASSWORD" ]; then
    echo "❌ ERROR: ACR_USERNAME or ACR_PASSWORD is not set in the .env file."
    exit 1
fi

# Check if necessary environment variables are set
if [ -z "$SECRET_KEY" ] || [ -z "$MONGODB_URI" ]; then
    echo "❌ ERROR: SECRET_KEY or MONGODB_URI is not set in the .env file."
    exit 1
fi

# Define variables
RESOURCE_GROUP="PodManager"
REGISTRY_NAME="podmanageracr3container"
IMAGE_NAME="podmanagerlive:latest"
WEBAPP_NAME="podmanager"
APP_SERVICE_PLAN="podmanagersp"
LOCATION="northeurope" # e.g., "eastus"

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

# Step 3: Clean up old Docker image in ACR
echo "Cleaning up old Docker images in ACR..."
docker rmi $REGISTRY_NAME.azurecr.io/$IMAGE_NAME || true
az acr repository delete --name $REGISTRY_NAME --image $IMAGE_NAME --yes

# clear cache for docker
docker builder prune --all --force

# Step 4: Log in to Azure Container Registry (ACR) using Managed Identity
echo "Logging in to ACR '$REGISTRY_NAME' using Managed Identity..."
az acr login --name $REGISTRY_NAME

# Step 5: Build Docker Image
echo "Building Docker image '$IMAGE_NAME'..."
docker build --no-cache -t $IMAGE_NAME .

# Step 6: Tag Docker Image for ACR
echo "Tagging Docker image '$IMAGE_NAME' with ACR tag..."
docker tag $IMAGE_NAME $REGISTRY_NAME.azurecr.io/$IMAGE_NAME

# Step 7: Push Docker Image to ACR
echo "Pushing Docker image to ACR..."
docker push $REGISTRY_NAME.azurecr.io/$IMAGE_NAME

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
    az webapp create --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --name $WEBAPP_NAME --deployment-container-image-name $REGISTRY_NAME.azurecr.io/$IMAGE_NAME --output none
else
    echo "Web App '$WEBAPP_NAME' already exists."
fi

# Step 10: Configure Web App to use ACR with credentials
echo "Configuring Web App to use Docker image from ACR with credentials..."
az webapp config container set --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP \
  --container-registry-url https://$REGISTRY_NAME.azurecr.io \
  --container-image-name $REGISTRY_NAME.azurecr.io/$IMAGE_NAME \
  --container-registry-user "$ACR_USERNAME" \
  --container-registry-password "$ACR_PASSWORD"

# Step 11: Restart Web App to trigger image pull from ACR
echo "Restarting Web App '$WEBAPP_NAME' to trigger image pull from ACR..."
az webapp restart --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP

# Step 12: Check the status of the Web App
echo "Web App '$WEBAPP_NAME' is deployed successfully. Checking the status..."
az webapp show --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP --output table
