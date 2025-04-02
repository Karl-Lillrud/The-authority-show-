#!/bin/bash

# Variables
APP_NAME="your-app-name"
RESOURCE_GROUP="your-resource-group"
REGISTRY_NAME="your-registry-name"
DOCKER_IMAGE="your-image-name"
AZURE_APP_SERVICE_PLAN="your-app-service-plan"
DOCKER_TAG="latest"

# Build Docker image
docker build -t $DOCKER_IMAGE:$DOCKER_TAG .

# Log in to Azure
az login

# Log in to Azure Container Registry (if applicable)
az acr login --name $REGISTRY_NAME

# Push Docker image to Azure Container Registry (if applicable)
docker tag $DOCKER_IMAGE:$DOCKER_TAG $REGISTRY_NAME.azurecr.io/$DOCKER_IMAGE:$DOCKER_TAG
docker push $REGISTRY_NAME.azurecr.io/$DOCKER_IMAGE:$DOCKER_TAG

# Deploy to Azure App Service
az webapp config container set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name $REGISTRY_NAME.azurecr.io/$DOCKER_IMAGE:$DOCKER_TAG \
  --docker-registry-server-url https://$REGISTRY_NAME.azurecr.io