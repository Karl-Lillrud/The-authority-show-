#!/bin/bash
set -euo pipefail

# Load environment variables from .env file using dotenv
if [ -f .env ]; then
    echo "📦 Loading environment variables from .env file..."
    if ! dotenv -f .env list > /dev/null 2>&1; then
        echo "❌ ERROR: Invalid syntax in .env file. Please check for invalid lines or characters."
        exit 1
    fi
    export $(dotenv -f .env list | xargs)
else
    echo "❌ .env file not found. Exiting..."
    exit 1
fi

# Check if ACR credentials are set
if [ -z "${ACR_USERNAME:-}" ] || [ -z "${ACR_PASSWORD:-}" ]; then
    echo "❌ WARNING: ACR_USERNAME or ACR_PASSWORD are not set. Using Managed Identity for authentication."
fi

# Define variables
RESOURCE_GROUP="PodManager"
REGISTRY_NAME="podmanageracr3container"
IMAGE_NAME="podmanagerlive:latest"
WEBAPP_NAME="podmanager"
APP_SERVICE_PLAN="podmanagersp"
LOCATION="northeurope"

# Show current Azure account
echo "🔑 Azure account info:"
az account show --output table

# Step 1: Resource Group
echo "🔍 Checking if Resource Group '$RESOURCE_GROUP' exists..."
if ! az group exists --name $RESOURCE_GROUP; then
    echo "📁 Creating Resource Group '$RESOURCE_GROUP' in $LOCATION..."
    az group create --name $RESOURCE_GROUP --location $LOCATION
else
    echo "✅ Resource Group '$RESOURCE_GROUP' already exists."
fi

# Step 2: Azure Container Registry (ACR)
echo "🔍 Checking if Azure Container Registry '$REGISTRY_NAME' exists..."
if ! az acr show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP > /dev/null 2>&1; then
    echo "📦 Creating Azure Container Registry '$REGISTRY_NAME'..."
    az acr create --resource-group $RESOURCE_GROUP --name $REGISTRY_NAME --sku Basic
else
    echo "✅ Azure Container Registry '$REGISTRY_NAME' already exists."
fi

# Step 3: Clean old Docker image (optional)
echo "🧹 Cleaning up old Docker images (if any)..."
docker rmi $REGISTRY_NAME.azurecr.io/$IMAGE_NAME || true
az acr repository delete --name $REGISTRY_NAME --image $IMAGE_NAME --yes || true

# Step 4: Prune builder cache
docker builder prune --all --force

# Step 5: Login to ACR
echo "🔐 Logging into Azure Container Registry..."
if ! az acr login --name $REGISTRY_NAME; then
    echo "❌ ERROR: Failed to login to ACR"
    exit 1
fi

# Step 6: Build Docker Image
echo "🐳 Building Docker image '$IMAGE_NAME'..."
if ! docker build --no-cache -t $IMAGE_NAME .; then
    echo "❌ ERROR: Docker build failed. Aborting deployment."
    exit 1
fi

# Step 6.5: Ensure image was built
if ! docker images | grep -q "${IMAGE_NAME%%:*}"; then
    echo "❌ ERROR: Docker image '$IMAGE_NAME' not found after build."
    exit 1
fi

# Step 7: Tag Docker Image
echo "🏷️ Tagging Docker image..."
docker tag $IMAGE_NAME $REGISTRY_NAME.azurecr.io/$IMAGE_NAME

# Step 8: Push Docker Image
echo "📤 Pushing image to ACR..."
docker push $REGISTRY_NAME.azurecr.io/$IMAGE_NAME

# Step 9: App Service Plan
echo "🔍 Checking if App Service Plan '$APP_SERVICE_PLAN' exists..."
if ! az appservice plan show --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP > /dev/null 2>&1; then
    echo "🛠️ Creating App Service Plan '$APP_SERVICE_PLAN'..."
    az appservice plan create --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --sku B1 --is-linux
else
    echo "✅ App Service Plan '$APP_SERVICE_PLAN' already exists."
fi

# Step 10: Web App
echo "🔍 Checking if Web App '$WEBAPP_NAME' exists..."
if ! az webapp show --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP > /dev/null 2>&1; then
    echo "🚀 Creating Web App '$WEBAPP_NAME'..."
    az webapp create --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN \
        --name $WEBAPP_NAME --deployment-container-image-name $REGISTRY_NAME.azurecr.io/$IMAGE_NAME
else
    echo "✅ Web App '$WEBAPP_NAME' already exists."
fi

# Step 11: Enable Managed Identity for Web App
echo "🔑 Enabling Managed Identity for Web App..."
az webapp identity assign --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP

# Step 12: Assign AcrPull role to Managed Identity
echo "🔒 Assigning AcrPull role to Web App's Managed Identity..."
WEBAPP_ID=$(az webapp identity show --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP --query principalId -o tsv)
SUBSCRIPTION_ID=$(az account show --query id -o tsv)  # Fetch the current subscription ID

az role assignment create --assignee $WEBAPP_ID --role AcrPull --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerRegistry/registries/$REGISTRY_NAME

# Step 13: Configure Web App to pull from ACR with Managed Identity
echo "⚙️ Configuring Web App to pull from ACR using Managed Identity..."
az webapp config container set --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP \
    --container-registry-url https://$REGISTRY_NAME.azurecr.io \
    --container-image-name $REGISTRY_NAME.azurecr.io/$IMAGE_NAME

# Step 14: Restart Web App to trigger pull from ACR
echo "🔄 Restarting Web App to trigger image pull from ACR..."
az webapp restart --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP

# Step 15: Final status check
echo "📡 Checking Web App status..."
az webapp show --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP --output table

echo "✅ Deployment complete!"
