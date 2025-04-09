from google.cloud import storage
import os

# Initialize Google Cloud Storage client
storage_client = storage.Client.from_service_account_json(
    os.getenv("GOOGLE_CLOUD_SERVICE_ACCOUNT_KEY")
)
bucket_name = os.getenv("GOOGLE_CLOUD_BUCKET_NAME")


def upload_rss_to_google_cloud(rss_feed, filename):
    """
    Upload the generated RSS feed to Google Cloud Storage.
    """
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(f"rss_feeds/{filename}")
    blob.upload_from_string(rss_feed, content_type="application/xml")
    # Construct the public URL without using blob.make_public()
    file_url = f"https://storage.googleapis.com/{bucket_name}/rss_feeds/{filename}"
    return file_url
