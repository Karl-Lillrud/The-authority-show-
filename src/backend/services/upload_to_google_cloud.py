from google.cloud import storage
import os
import logging

# Initialize Google Cloud Storage client
storage_client = storage.Client.from_service_account_json(
    os.getenv("GOOGLE_CLOUD_SERVICE_ACCOUNT_KEY")
)
bucket_name = os.getenv("GOOGLE_CLOUD_BUCKET_NAME")

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def upload_to_google_cloud(file_data, filename, folder="images"):
    """
    Upload a file to Google Cloud Storage and return its public URL.
    :param file_data: The binary data of the file to upload.
    :param filename: The name of the file.
    :param folder: The folder in the bucket where the file will be stored.
    :return: The public URL of the uploaded file.
    """
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(f"{folder}/{filename}")
        blob.upload_from_string(file_data)
        # Construct the public URL
        file_url = f"https://storage.googleapis.com/{bucket_name}/{folder}/{filename}"
        logger.info(f"File '{filename}' uploaded to Google Cloud Storage at: {file_url}")
        return file_url
    except Exception as e:
        logger.error(f"Failed to upload file '{filename}' to Google Cloud Storage: {e}")
        raise
