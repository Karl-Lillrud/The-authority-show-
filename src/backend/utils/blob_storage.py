from azure.storage.blob import BlobServiceClient
import os
import logging
import tempfile # Import tempfile

logger = logging.getLogger(__name__)

# Initialize BlobServiceClient
connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
if not connection_string:
    logger.warning("AZURE_STORAGE_CONNECTION_STRING environment variable not set.")
    blob_service_client = None
else:
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

def upload_file_to_blob(container_name, blob_path, file):
    """
    Uploads a file to Azure Blob Storage.
    Args:
        container_name (str): The name of the Azure Blob Storage container.
        blob_path (str): The path within the container where the file will be stored.
        file: The file object to upload.
    Returns:
        str: The URL of the uploaded file.
    """
    try:
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)
        blob_client.upload_blob(file, overwrite=True)
        blob_url = f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net/{container_name}/{blob_path}"
        logger.info(f"File uploaded successfully to {blob_url}")
        return blob_url
    except Exception as e:
        logger.error(f"Failed to upload file to blob storage: {e}", exc_info=True)
        raise

def download_blob_to_tempfile(container_name, blob_path):
    """
    Downloads a blob from Azure Blob Storage to a temporary file.
    Args:
        container_name (str): The name of the Azure Blob Storage container.
        blob_path (str): The path of the blob to download.
    Returns:
        str: The path to the temporary file containing the blob content, or None if error.
    """
    if not blob_service_client:
        logger.error("BlobServiceClient not initialized. Cannot download blob.")
        return None

    try:
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)
        
        # Create a temporary file
        temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        
        logger.info(f"Attempting to download blob '{blob_path}' from container '{container_name}' to {temp_db_file.name}")
        
        with open(temp_db_file.name, "wb") as download_file:
            download_stream = blob_client.download_blob()
            download_file.write(download_stream.readall())
            
        logger.info(f"Blob downloaded successfully to temporary file: {temp_db_file.name}")
        return temp_db_file.name
        
    except Exception as e:
        logger.error(f"Failed to download blob '{blob_path}' from container '{container_name}': {e}", exc_info=True)
        # Clean up temp file if created but download failed
        if 'temp_db_file' in locals() and os.path.exists(temp_db_file.name):
             os.remove(temp_db_file.name)
        return None
