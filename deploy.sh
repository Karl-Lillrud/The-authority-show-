#!/bin/bash

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

# Define variables
RESOURCE_GROUP="PodManager"
REGISTRY_NAME="podmanageracr3container"
IMAGE_NAME="podmanagerlive:latest"
WEBAPP_NAME="podmanager"
APP_SERVICE_PLAN="podmanagersp"
LOCATION="northeurope" # e.g., "eastus"

# Step 1: Check if Resource Group exists
echo "🔍 Checking if Resource Group '$RESOURCE_GROUP' exists..."
if ! az group exists --name $RESOURCE_GROUP; then
    echo "📁 Creating Resource Group '$RESOURCE_GROUP' in $LOCATION..."
    az group create --name $RESOURCE_GROUP --location $LOCATION --output none
else
    echo "✅ Resource Group '$RESOURCE_GROUP' already exists."
fi

# Step 2: Check if Azure Container Registry (ACR) exists
echo "🔍 Checking if Azure Container Registry '$REGISTRY_NAME' exists..."
if ! az acr show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --output none; then
    echo "📦 Creating Azure Container Registry '$REGISTRY_NAME'..."
    az acr create --resource-group $RESOURCE_GROUP --name $REGISTRY_NAME --sku Basic --output none
else
    echo "✅ Azure Container Registry '$REGISTRY_NAME' already exists."
fi

# Step 3: Clean up old Docker image in ACR, but avoid if image is already cached
echo "🧹 Cleaning up old Docker images in ACR..."
if ! az acr repository show --name $REGISTRY_NAME --image $IMAGE_NAME --output none; then
    echo "📦 No image found in ACR, skipping cleanup."
else
    docker rmi $REGISTRY_NAME.azurecr.io/$IMAGE_NAME || true
    az acr repository delete --name $REGISTRY_NAME --image $IMAGE_NAME --yes
fi

# Clear Docker cache to improve speed
docker builder prune --all --force

# Step 4: Log in to Azure Container Registry (ACR) using Managed Identity
echo "🔐 Logging in to ACR '$REGISTRY_NAME' using Managed Identity..."
az acr login --name $REGISTRY_NAME

# Step 5: Build Docker Image, using cached layers when possible
echo "🐳 Building Docker image '$IMAGE_NAME' (leveraging cache)..."
docker build --build-arg CACHEBUST=$(date +%s) -t $IMAGE_NAME .

# Step 6: Tag Docker Image for ACR
echo "🏷️ Tagging Docker image '$IMAGE_NAME' with ACR tag..."
docker tag $IMAGE_NAME $REGISTRY_NAME.azurecr.io/$IMAGE_NAME

# Step 7: Push Docker Image to ACR
echo "📤 Pushing Docker image to ACR..."
docker push $REGISTRY_NAME.azurecr.io/$IMAGE_NAME

# Step 8: Check if App Service Plan exists
echo "🔍 Checking if App Service Plan '$APP_SERVICE_PLAN' exists..."
if ! az appservice plan show --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --output none; then
    echo "🛠️ Creating App Service Plan '$APP_SERVICE_PLAN'..."
    az appservice plan create --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --sku P0v3 --is-linux --output none
else
    echo "✅ App Service Plan '$APP_SERVICE_PLAN' already exists."
fi

# Step 9: Check if Web App exists, and update if necessary
echo "🔍 Checking if Web App '$WEBAPP_NAME' exists..."
if ! az webapp show --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP --output none; then
    echo "🚀 Creating Web App '$WEBAPP_NAME' for container deployment..."
    az webapp create --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --name $WEBAPP_NAME --deployment-container-image-name $REGISTRY_NAME.azurecr.io/$IMAGE_NAME --output none
else
    echo "✅ Web App '$WEBAPP_NAME' already exists. Redeploying container..."
    az webapp config container set --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP --container-image-name $REGISTRY_NAME.azurecr.io/$IMAGE_NAME --output none
fi

# Step 10: Configure SSH access for the web app if not already enabled
echo "🔑 Configuring SSH access for the web app..."
az webapp config set --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP --linux-fx-version "DOCKER|$REGISTRY_NAME.azurecr.io/$IMAGE_NAME" --output none
az webapp config appsettings set --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP --settings WEBSITES_ENABLE_APP_SERVICE_STORAGE=true --output none
az webapp config set --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP --remote-debugging-enabled true --output none

# Step 11: Create startup script that cleans HF cache on container startup
echo "📝 Creating startup script with cache cleaning..."
STARTUP_SCRIPT=$(cat <<'EOF'
#!/bin/bash

# Define cache directories to clean
HF_CACHE_DIR="/root/.cache/huggingface"
TEMP_DIR="/tmp"

# Function to clean cache directories
clean_cache() {
    echo "$(date) - Starting cache cleanup" >> /home/LogFiles/cache_cleanup.log
    
    # Check disk space before cleanup
    df -h / >> /home/LogFiles/cache_cleanup.log
    
    # Clean Hugging Face cache
    if [ -d "$HF_CACHE_DIR" ]; then
        echo "$(date) - Cleaning Hugging Face cache..." >> /home/LogFiles/cache_cleanup.log
        find "$HF_CACHE_DIR" -type d -name "chunk-cache" -exec rm -rf {} +
        du -sh "$HF_CACHE_DIR" >> /home/LogFiles/cache_cleanup.log
    fi
    
    # Clean tmp directory
    echo "$(date) - Cleaning /tmp directory..." >> /home/LogFiles/cache_cleanup.log
    find "$TEMP_DIR" -type f -atime +1 -delete
    du -sh "$TEMP_DIR" >> /home/LogFiles/cache_cleanup.log
    
    # Check disk space after cleanup
    echo "$(date) - Disk space after cleanup:" >> /home/LogFiles/cache_cleanup.log
    df -h / >> /home/LogFiles/cache_cleanup.log
    echo "$(date) - Cache cleanup completed" >> /home/LogFiles/cache_cleanup.log
}

# Run initial cleanup
clean_cache

# Setup cron job for regular cleanup (every 6 hours)
if ! crontab -l | grep -q "clean_cache"; then
    (crontab -l 2>/dev/null; echo "0 */6 * * * /home/site/wwwroot/cleanup_cache.sh >> /home/LogFiles/cache_cleanup.log 2>&1") | crontab -
fi

# Start the main application
exec "$@"
EOF
)

# Create a temporary file for the startup script
TEMP_SCRIPT_FILE=$(mktemp)
echo "$STARTUP_SCRIPT" > "$TEMP_SCRIPT_FILE"

# Step 12: Create a separate cleanup script that will be run by cron
echo "📝 Creating cache cleanup script..."
CLEANUP_SCRIPT=$(cat <<'EOF'
#!/bin/bash

# Define cache directories to clean
HF_CACHE_DIR="/root/.cache/huggingface"
TEMP_DIR="/tmp"

echo "$(date) - Scheduled cache cleanup started" 

# Clean Hugging Face cache
if [ -d "$HF_CACHE_DIR" ]; then
    echo "$(date) - Cleaning Hugging Face cache..." 
    find "$HF_CACHE_DIR" -type d -name "chunk-cache" -exec rm -rf {} + 2>/dev/null
    echo "$(date) - HF cache size after cleanup: $(du -sh $HF_CACHE_DIR 2>/dev/null)"
fi

# Clean tmp directory
echo "$(date) - Cleaning /tmp directory..." 
find "$TEMP_DIR" -type f -atime +1 -delete 2>/dev/null
echo "$(date) - /tmp size after cleanup: $(du -sh $TEMP_DIR 2>/dev/null)"

# Check disk space
echo "$(date) - Current disk usage:" 
df -h /

echo "$(date) - Scheduled cache cleanup completed"
EOF
)

# Create a temporary file for the cleanup script
TEMP_CLEANUP_FILE=$(mktemp)
echo "$CLEANUP_SCRIPT" > "$TEMP_CLEANUP_FILE"

# Step 13: Configure the Web App to use the custom startup script
echo "⚙️ Configuring startup command and uploading cleanup scripts..."

# Upload the startup script to the web app
az webapp deploy --resource-group $RESOURCE_GROUP --name $WEBAPP_NAME --src-path "$TEMP_SCRIPT_FILE" --target-path "/home/site/wwwroot/startup.sh" --clean true

# Upload the cleanup script to the web app
az webapp deploy --resource-group $RESOURCE_GROUP --name $WEBAPP_NAME --src-path "$TEMP_CLEANUP_FILE" --target-path "/home/site/wwwroot/cleanup_cache.sh" --clean true

# Set the startup command to use our custom script
az webapp config set --resource-group $RESOURCE_GROUP --name $WEBAPP_NAME --startup-file "sh /home/site/wwwroot/startup.sh gunicorn --bind 0.0.0.0:8000 src.app:app"

# Delete temporary files
rm "$TEMP_SCRIPT_FILE"
rm "$TEMP_CLEANUP_FILE"

# Step 14: Configure Web App to run SSH commands for immediate cache cleanup
echo "🧹 Running immediate cache cleanup on the web app..."
az webapp ssh --resource-group $RESOURCE_GROUP --name $WEBAPP_NAME --command "
# Make scripts executable
chmod +x /home/site/wwwroot/startup.sh /home/site/wwwroot/cleanup_cache.sh

# Clean HF cache directory
echo 'Cleaning Hugging Face cache directory...'
find /root/.cache/huggingface -type d -name 'chunk-cache' -exec rm -rf {} + 2>/dev/null || true
echo 'Done cleaning Hugging Face cache'

# Display available disk space
df -h /"

# Step 15: Restart Web App to apply new settings
echo "🔄 Restarting Web App '$WEBAPP_NAME' to apply new settings..."
az webapp restart --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP

# Step 16: Check the status of the Web App
echo "📡 Checking Web App status..."
az webapp show --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP --output table

# Step 17: Set up disk monitoring alert (if doesn't exist)
echo "🚨 Setting up disk space monitoring..."
if ! az monitor alert list --resource-group $RESOURCE_GROUP --output json | grep -q "disk-space-alert"; then
    az monitor metrics alert create \
        --name "disk-space-alert" \
        --resource-group $RESOURCE_GROUP \
        --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$WEBAPP_NAME" \
        --condition "max FilesystemUsage > 85" \
        --description "Alert when disk usage exceeds 85%" \
        --evaluation-frequency 5m \
        --window-size 5m \
        --severity 2

    echo "✅ Disk space alert created"
else
    echo "✅ Disk space alert already exists"
fi

echo "✅ Deployment complete with cache management system in place!"
