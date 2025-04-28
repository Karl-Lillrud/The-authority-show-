#!/bin/bash

# Load environment variables from .env file using dotenv
if [ -f .env ]; then
    if ! dotenv -f .env list > /dev/null 2>&1; then
        echo "❌ ERROR: Invalid syntax in .env file."
        exit 1
    fi
    export $(dotenv -f .env list | xargs)
else
    echo ".env file not found. Exiting..."
    exit 1
fi

[ -z "$ACR_USERNAME" ] || [ -z "$ACR_PASSWORD" ] && echo "❌ ERROR: ACR_USERNAME or ACR_PASSWORD missing." && exit 1

RESOURCE_GROUP="PodManager"
REGISTRY_NAME="podmanageracr3container"
IMAGE_NAME="podmanagerlive:latest"
REPO_NAME="${IMAGE_NAME%%:*}"
WEBAPP_NAME="podmanager"
APP_SERVICE_PLAN="podmanagersp"
LOCATION="northeurope"

# ensure resource group
az group exists --name $RESOURCE_GROUP || az group create -n $RESOURCE_GROUP -l $LOCATION --output none

# ensure ACR
if ! az acr show -n $REGISTRY_NAME -g $RESOURCE_GROUP --output none; then
    az acr create -g $RESOURCE_GROUP -n $REGISTRY_NAME --sku Basic --output none
fi

# Login to ACR with credentials
echo "Logging in to ACR '$REGISTRY_NAME' using credentials..."
az acr login -n $REGISTRY_NAME --username "$ACR_USERNAME" --password "$ACR_PASSWORD"

# More thorough Docker cleanup
echo "Performing Docker cleanup..."
# Remove dangling images (untagged)
docker image prune -f
# Remove stopped containers
docker container prune -f
# Remove unused build cache
docker builder prune -f

# delete existing ACR repo
echo "Deleting existing ACR repository '$REPO_NAME' (if any)..."
az acr repository delete --name $REGISTRY_NAME --repository $REPO_NAME --yes --output none

# Force clean build and push
echo "Building Docker image with clean build..."
docker build --no-cache --pull -t $IMAGE_NAME .
docker tag     $IMAGE_NAME $REGISTRY_NAME.azurecr.io/$IMAGE_NAME
docker push    $REGISTRY_NAME.azurecr.io/$IMAGE_NAME

# ensure App Service Plan
az appservice plan show -n $APP_SERVICE_PLAN -g $RESOURCE_GROUP --output none || \
    az appservice plan create -n $APP_SERVICE_PLAN -g $RESOURCE_GROUP --sku B1 --is-linux --output none

# ensure Web App
if ! az webapp show -n $WEBAPP_NAME -g $RESOURCE_GROUP --output none; then
    az webapp create -g $RESOURCE_GROUP -p $APP_SERVICE_PLAN -n $WEBAPP_NAME \
      --deployment-container-image-name $REGISTRY_NAME.azurecr.io/$IMAGE_NAME --output none
fi

az webapp config container set -n $WEBAPP_NAME -g $RESOURCE_GROUP \
  --docker-registry-server-url https://$REGISTRY_NAME.azurecr.io \
  --docker-custom-image-name $REGISTRY_NAME.azurecr.io/$IMAGE_NAME \
  --docker-registry-server-user "$ACR_USERNAME" \
  --docker-registry-server-password "$ACR_PASSWORD"

# Restart webapp to ensure new container is pulled
echo "Restarting webapp to apply changes..."
az webapp restart -n $WEBAPP_NAME -g $RESOURCE_GROUP

echo "Deployment complete. Checking Web App status..."
az webapp show -n $WEBAPP_NAME -g $RESOURCE_GROUP --output table