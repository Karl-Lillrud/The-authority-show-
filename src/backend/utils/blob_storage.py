from azure.storage.blob import BlobServiceClient, BlobClient # Import BlobClient
from azure.core.exceptions import ResourceNotFoundError, AzureError # Import specific exceptions
import os
import logging
import tempfile

logger = logging.getLogger(__name__)

# Best Practice: Use a function to get the client, allowing for retry/error handling during init
def get_blob_service_client():
    """Initializes and returns a BlobServiceClient instance."""
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not connection_string:
        logger.error("AZURE_STORAGE_CONNECTION_STRING environment variable not set.")
        return None
    try:
        # Best Practice: Specify API version if needed, otherwise defaults work
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        # Optional: Test connection (e.g., list containers) - can add overhead
        # blob_service_client.list_containers(max_results=1)
        logger.info("BlobServiceClient initialized successfully.")
        return blob_service_client
    except ValueError as ve:
        logger.error(f"Invalid connection string format: {ve}", exc_info=True)
        return None
    except AzureError as ae:
        logger.error(f"Azure connection error during BlobServiceClient initialization: {ae}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error during BlobServiceClient initialization: {e}", exc_info=True)
        return None

def upload_file_to_blob(container_name, blob_path, file):
    """
    Uploads a file to Azure Blob Storage.
    Args:
        container_name (str): The name of the Azure Blob Storage container.
        blob_path (str): The path within the container where the file will be stored.
        file: The file object or path to upload.
    Returns:
        str: The URL of the uploaded file or None on failure.
    """
    blob_service_client = get_blob_service_client() # Get client instance
    if not blob_service_client:
        logger.error("BlobServiceClient not initialized. Cannot upload file.")
        return None

    try:
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)
        # Best Practice: Check if file is a path or stream
        if isinstance(file, str) and os.path.exists(file):
             with open(file, "rb") as data:
                  blob_client.upload_blob(data, overwrite=True)
        else:
             # Assume it's a file-like object (stream)
             file.seek(0) # Ensure stream is at the beginning
             blob_client.upload_blob(file, overwrite=True)

        # Best Practice: Construct URL reliably
        account_name = blob_service_client.account_name
        if not account_name: # Try extracting from connection string if needed (more complex)
             logger.warning("Could not determine storage account name for URL construction.")
             blob_url = blob_client.url # Fallback to client's URL property
        else:
             blob_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_path}"

        logger.info(f"File uploaded successfully to {blob_url}")
        return blob_url
    except ResourceNotFoundError:
        logger.error(f"Container '{container_name}' not found.", exc_info=True)
        return None
    except AzureError as ae:
         logger.error(f"Azure error during blob upload: {ae}", exc_info=True)
         return None
    except Exception as e:
        logger.error(f"Failed to upload file to blob storage: {e}", exc_info=True)
        return None # Return None on failure

def download_blob_to_tempfile(container_name, blob_path):
    """
    Downloads a blob from Azure Blob Storage to a temporary file.
    Args:
        container_name (str): The name of the Azure Blob Storage container.
        blob_path (str): The path of the blob to download.
    Returns:
        str: The path to the temporary file containing the blob content, or None if error.
    """
    blob_service_client = get_blob_service_client() # Get client instance
    if not blob_service_client:
        logger.error("BlobServiceClient not initialized. Cannot download blob.")
        return None

    temp_db_file = None # Initialize outside try
    try:
        blob_client: BlobClient = blob_service_client.get_blob_client(container=container_name, blob=blob_path)

        # Create a temporary file securely
        temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db", prefix="blobdownload_")

        logger.info(f"Attempting to download blob '{blob_path}' from container '{container_name}' to {temp_db_file.name}")

        # Download in chunks
        with open(temp_db_file.name, "wb") as download_file:
            stream = blob_client.download_blob()
            chunk_size = 4 * 1024 * 1024
            total_bytes = 0
            while True:
                chunk = stream.read(chunk_size)
                if not chunk:
                    break
                download_file.write(chunk)
                total_bytes += len(chunk)
            logger.info(f"Downloaded {total_bytes} bytes.")

        logger.info(f"Blob downloaded successfully to temporary file: {temp_db_file.name}")
        return temp_db_file.name

    except ResourceNotFoundError:
        logger.error(f"Blob '{blob_path}' not found in container '{container_name}'.", exc_info=True)
        if temp_db_file and os.path.exists(temp_db_file.name):
             os.remove(temp_db_file.name)
        return None
    except AzureError as ae:
        logger.error(f"Azure error during blob download: {ae}", exc_info=True)
        if temp_db_file and os.path.exists(temp_db_file.name):
             os.remove(temp_db_file.name)
        return None
    except Exception as e:
        logger.error(f"Failed to download blob '{blob_path}' from container '{container_name}': {e}", exc_info=True)
        if temp_db_file and os.path.exists(temp_db_file.name):
             os.remove(temp_db_file.name)
        return None