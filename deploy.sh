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

# Check if AZ_SUB_ID and AZ_OBJ_ID are set in the .env file
if [ -z "${AZ_SUB_ID:-}" ] || [ -z "${AZ_OBJ_ID:-}" ]; then
    echo "❌ ERROR: AZ_SUB_ID or AZ_OBJ_ID not set in .env file."
    exit 1
fi

# Set the correct Azure Subscription
echo "🔑 Setting the Azure subscription to $AZ_SUB_ID..."
az account set --subscription "$AZ_SUB_ID"

# Define variables
RESOURCE_GROUP="PodManager"
REGISTRY_NAME="podmanageracr3container"
IMAGE_NAME="podmanagerlive:latest"
WEBAPP_NAME="podmanager"
APP_SERVICE_PLAN="podmanagersp"
LOCATION="northeurope" # e.g., "eastus"
SKU="P0v3"  # Correct App Service plan SKU

# Step 1: Check if Resource Group exists (skip if it exists)
echo "🔍 Checking if Resource Group '$RESOURCE_GROUP' exists..."
if ! az group exists --name $RESOURCE_GROUP; then
    echo "📁 Creating Resource Group '$RESOURCE_GROUP' in $LOCATION..."
    az group create --name $RESOURCE_GROUP --location $LOCATION --output none
else
    echo "✅ Resource Group '$RESOURCE_GROUP' already exists."
fi

# Step 2: Check if Azure Container Registry (ACR) exists (skip if it exists)
echo "🔍 Checking if Azure Container Registry '$REGISTRY_NAME' exists..."
if ! az acr show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --output none; then
    echo "📦 Creating Azure Container Registry '$REGISTRY_NAME'..."
    az acr create --resource-group $RESOURCE_GROUP --name $REGISTRY_NAME --sku Basic --output none
else
    echo "✅ Azure Container Registry '$REGISTRY_NAME' already exists."
fi

# Step 3: Clean up old Docker image in ACR (only if image exists)
echo "🧹 Cleaning up old Docker images in ACR..."
if az acr repository show-tags --name $REGISTRY_NAME --repository podmanagerlive | grep -q "$IMAGE_NAME"; then
    # Delete the image tag
    docker rmi $REGISTRY_NAME.azurecr.io/$IMAGE_NAME || true
    az acr repository delete --name $REGISTRY_NAME --image $IMAGE_NAME --yes
    echo "✅ Image '$IMAGE_NAME' deleted from ACR."
else
    echo "✅ No image '$IMAGE_NAME' found in ACR."
fi

# Now, delete the repository (if empty)
echo "🧹 Cleaning up the repository (if empty)..."
az acr repository delete --name $REGISTRY_NAME --repository podmanagerlive --yes --if-empty

# Step 4: Prune builder cache to avoid unused layers during build
docker builder prune --all --force

# Step 5: Log in to Azure Container Registry (ACR) using Managed Identity (reuse credentials)
echo "🔐 Logging into ACR '$REGISTRY_NAME' using Managed Identity..."
az acr login --name $REGISTRY_NAME

# Step 6: Build Docker Image (only if necessary)
echo "🐳 Building Docker image '$IMAGE_NAME'..."
# Skip rebuild if image already exists
if docker images -q $IMAGE_NAME; then
    echo "✅ Docker image '$IMAGE_NAME' already exists, skipping build."
else
    docker build --no-cache -t $IMAGE_NAME .
fi

# Step 7: Tag Docker Image for ACR
echo "🏷️ Tagging Docker image '$IMAGE_NAME' with ACR tag..."
docker tag $IMAGE_NAME $REGISTRY_NAME.azurecr.io/$IMAGE_NAME

# Step 8: Push Docker Image to ACR (skip if the image is already there)
echo "📤 Pushing Docker image to ACR..."
if ! az acr repository show-tags --name $REGISTRY_NAME --repository podmanagerlive | grep -q "$IMAGE_NAME"; then
    docker push $REGISTRY_NAME.azurecr.io/$IMAGE_NAME
else
    echo "✅ Docker image '$IMAGE_NAME' is already pushed to ACR."
fi

# Step 9: Check if App Service Plan exists (skip if it exists)
echo "🔍 Checking if App Service Plan '$APP_SERVICE_PLAN' exists..."
if ! az appservice plan show --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --output none; then
    echo "🛠️ Creating App Service Plan '$APP_SERVICE_PLAN' with SKU $SKU..."
    az appservice plan create --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --sku $SKU --is-linux --output none
else
    echo "✅ App Service Plan '$APP_SERVICE_PLAN' already exists."
fi

# Step 10: Check if Web App exists (skip if it exists)
echo "🔍 Checking if Web App '$WEBAPP_NAME' exists..."
if ! az webapp show --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP --output none; then
    echo "🚀 Creating Web App '$WEBAPP_NAME' for container deployment..."
    az webapp create --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --name $WEBAPP_NAME --deployment-container-image-name $REGISTRY_NAME.azurecr.io/$IMAGE_NAME --output none
else
    echo "✅ Web App '$WEBAPP_NAME' already exists."
fi

# Step 11: Assign `AcrPull` role to Web App's Managed Identity (if not already assigned)
echo "🔒 Checking if `AcrPull` role is assigned to Web App's Managed Identity..."
WEBAPP_ID=$(az webapp identity show --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP --query principalId -o tsv)
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Check if `AcrPull` role is already assigned
ROLE_EXISTS=$(az role assignment list --assignee $WEBAPP_ID --role AcrPull --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerRegistry/registries/$REGISTRY_NAME --query "[0]" -o tsv)

if [ "$ROLE_EXISTS" == "" ]; then
    echo "📜 Assigning `AcrPull` role to Web App's Managed Identity..."
    az role assignment create --assignee $WEBAPP_ID --role AcrPull --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerRegistry/registries/$REGISTRY_NAME
else
    echo "✅ `AcrPull` role already assigned to Web App's Managed Identity."
fi

# Step 12: Restart Web App to apply new image (if any change)
echo "🔄 Restarting Web App '$WEBAPP_NAME' to apply new image..."
az webapp restart --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP

# Step 13: Check the status of the Web App
echo "📡 Checking Web App status..."
az webapp show --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP --output table

echo "✅ Deployment complete!"
