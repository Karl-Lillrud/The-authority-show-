#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Variables
RESOURCE_GROUP="PodManager" # Replace with your Azure resource group
ACR_NAME="podmanager"             # Replace with your Azure Container Registry name
APP_NAME="podmanager"     # Replace with your Azure App Service name
DOCKER_IMAGE_NAME="podmanagerlive""
DOCKER_TAG=$(git rev-parse --short HEAD) # Use the latest Git commit hash as the tag

# Build Docker image
echo "Building Docker image..."
docker build -t $DOCKER_IMAGE_NAME .
s
# Tag Docker image for Azure Container Registry
echo "Tagging Docker image..."
docker tag $DOCKER_IMAGE_NAME $ACR_NAME.azurecr.io/$DOCKER_IMAGE_NAME:$DOCKER_TAG

# Login to Azure Container Registry
echo "Logging in to Azure Container Registry..."
az acr login --name $ACR_NAME

# Push Docker image to Azure Container Registry
echo "Pushing Docker image to Azure Container Registry..."
docker push $ACR_NAME.azurecr.io/$DOCKER_IMAGE_NAME:$DOCKER_TAG

# Deploy Docker image to Azure App Service
echo "Deploying Docker image to Azure App Service..."
az webapp config container set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name $ACR_NAME.azurecr.io/$DOCKER_IMAGE_NAME:$DOCKER_TAG

# Restart the Azure App Service to apply changes
echo "Restarting Azure App Service..."
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP

echo "Deployment completed successfully!"
