from azure.storage.blob import BlobServiceClient, BlobClient, ContentSettings # Import ContentSettings
from azure.core.exceptions import ResourceNotFoundError, AzureError # Import specific exceptions
import os
import logging
import tempfile
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename

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

def upload_file_to_blob(container_name, blob_path, file, content_type=None): # Added content_type parameter
    blob_service_client = get_blob_service_client() # Get client instance
    if not blob_service_client:
        logger.error("BlobServiceClient not initialized. Cannot upload file.")
        return None

    try:
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)
        
        current_content_settings = None
        if content_type:
            current_content_settings = ContentSettings(content_type=content_type)

        # Best Practice: Check if file is a path or stream
        if isinstance(file, str) and os.path.exists(file):
             with open(file, "rb") as data:
                  blob_client.upload_blob(data, overwrite=True, content_settings=current_content_settings) # Use ContentSettings object
        else:
             # Assume it's a file-like object (stream)
             file.seek(0) # Ensure stream is at the beginning
             blob_client.upload_blob(file, overwrite=True, content_settings=current_content_settings) # Use ContentSettings object

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

def get_blob_content(container_name, blob_path):
    """
    Read a blob directly from Azure Blob Storage without downloading to a file
    
    Args:
        container_name (str): The name of the Azure Blob Storage container.
        blob_path (str): The path of the blob to read.
        
    Returns:
        bytes: The content of the blob or None if an error occurs.
    """
    blob_service_client = get_blob_service_client()
    if not blob_service_client:
        logger.error("BlobServiceClient not initialized. Cannot read blob.")
        return None

    try:
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)
        
        # Check if blob exists before trying to download
        if not blob_client.exists():
            logger.error(f"Blob '{blob_path}' not found in container '{container_name}'.")
            return None
        
        # Download blob content directly to memory
        download_stream = blob_client.download_blob()
        content = download_stream.readall()
        
        logger.info(f"Successfully read blob: {blob_path}")
        return content
        
    except ResourceNotFoundError:
        logger.error(f"Blob '{blob_path}' not found in container '{container_name}'.", exc_info=True)
        return None
    except AzureError as ae:
        logger.error(f"Azure error during blob read: {ae}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Failed to read blob '{blob_path}' from container '{container_name}': {e}", exc_info=True)
        return None


def upload_episode_cover_art_to_blob(file_stream, user_id, podcast_id, episode_id=None, original_filename="cover.jpg"):
    """
    Uploads episode cover art and returns the string URL or None.
    Path for new: users/<user_id>/podcasts/<podcast_id>/episodes/artwork/new_<timestamp>_<filename>
    Path for existing: users/<user_id>/podcasts/<podcast_id>/episodes/<episode_id>/artwork/<timestamp>_<filename>
    """
    logger = current_app.logger
    # Ensure AZURE_STORAGE_CONTAINER_NAME is set in your environment, e.g., "podmanagerstorage"
    container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "podmanagerstorage") 
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    
    safe_original_filename = secure_filename(original_filename)
    name_part, file_extension = os.path.splitext(safe_original_filename)
    if not file_extension: 
        # Default to .jpg if no extension is found, or consider raising an error/logging a warning
        file_extension = '.jpg' 

    filename_with_ts = f"{timestamp}_{name_part}{file_extension}" if name_part else f"{timestamp}_artwork{file_extension}"

    if episode_id:
        # Path for existing episode (update)
        blob_path = f"users/{user_id}/podcasts/{podcast_id}/episodes/{episode_id}/artwork/{filename_with_ts}"
    else:
        # Path for new episode (create) - episode_id not yet known
        blob_path = f"users/{user_id}/podcasts/{podcast_id}/episodes/artwork/new_{filename_with_ts}"

    content_type = getattr(file_stream, 'content_type', 'application/octet-stream')
    
    if content_type == 'application/octet-stream' or not content_type: 
        if file_extension.lower() in ['.jpg', '.jpeg']:
            content_type = 'image/jpeg'
        elif file_extension.lower() == '.png':
            content_type = 'image/png'
        elif file_extension.lower() == '.webp':
            content_type = 'image/webp'
        else:
            # Fallback if extension is not recognized, or log a warning
            content_type = 'application/octet-stream' 
            
    logger.info(f"Preparing to upload episode cover. Path: {container_name}/{blob_path}, Content-Type: {content_type}")
    
    # This calls the generic upload_file_to_blob function
    uploaded_url = upload_file_to_blob(container_name, blob_path, file_stream, content_type)
    
    if uploaded_url:
        logger.info(f"Episode cover art upload successful. Blob URL: {uploaded_url}")
    else:
        logger.error(f"Episode cover art upload failed for path: {container_name}/{blob_path}")
        
    return uploaded_url

def upload_file_to_blob(container_name, blob_path, file_stream, content_type=None):
    logger = current_app.logger
    try:
        # Ensure AZURE_STORAGE_CONNECTION_STRING is set in your environment
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not connection_string:
            logger.error("AZURE_STORAGE_CONNECTION_STRING is not set.")
            return None

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(
            container=container_name, blob=blob_path
        )

        if hasattr(file_stream, 'seek'):
            file_stream.seek(0)

        content_settings_to_apply = None
        if content_type:
            content_settings_to_apply = ContentSettings(content_type=content_type)
            logger.info(f"Uploading with ContentSettings: {content_type} for blob: {blob_path}")
        else:
            logger.info(f"Uploading without explicit ContentSettings for blob: {blob_path}")

        blob_client.upload_blob(file_stream, overwrite=True, content_settings=content_settings_to_apply)
        
        blob_url = blob_client.url
        logger.info(f"File uploaded successfully. Blob URL: {blob_url}")
        return blob_url
    except Exception as e:
        logger.error(f"Failed to upload to Azure Blob Storage: {e}", exc_info=True)
        return None