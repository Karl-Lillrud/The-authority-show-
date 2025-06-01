from azure.storage.blob import BlobServiceClient
import os
import logging
from flask import current_app

logger = logging.getLogger(__name__)

def verify_activation_file_exists():
    """Verify that the scraped.xml file exists and is readable in blob storage."""
    try:
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "podmanagerfiles")
        blob_path = "activate/scraped.xml"
        
        if not connection_string:
            logger.warning("AZURE_STORAGE_CONNECTION_STRING environment variable not set. Cannot verify activation file.")
            return False
            
        logger.info(f"Checking for activation file at {container_name}/{blob_path}")
        
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)
        
        # Check if blob exists
        if not blob_client.exists():
            logger.error(f"Activation file not found: {container_name}/{blob_path}")
            return False
            
        # Attempt to get blob properties to verify we can access it
        properties = blob_client.get_blob_properties()
        file_size = properties.size
        
        # Check minimal size - an empty file wouldn't be useful
        if file_size < 100:  # Arbitrary small size check
            logger.warning(f"Activation file exists but may be empty or too small: {file_size} bytes")
            return True
            
        logger.info(f"✅ Activation file verified: {container_name}/{blob_path} ({file_size} bytes)")
        return True
            
    except Exception as e:
        logger.error(f"Error verifying activation file: {str(e)}")
        return False
