from azure.storage.blob import BlobServiceClient
import os
import logging

logger = logging.getLogger(__name__)

# Initialize BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(
    os.getenv("AZURE_STORAGE_CONNECTION_STRING")
)

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
