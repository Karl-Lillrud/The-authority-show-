import boto3
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env


def upload_rss_to_cloudflare(rss_feed, filename):
    """
    Upload the generated RSS feed to Cloudflare R2.
    """
    # Initialize the R2 client (using boto3 to interact with Cloudflare R2)
    s3_client = boto3.client(
        "s3",
        endpoint_url=os.getenv("CLOUDFLARE_R2_BUCKET_URL"),
        aws_access_key_id=os.getenv("CLOUDFLARE_R2_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("CLOUDFLARE_R2_SECRET_KEY"),
        region_name="auto",  # Use a valid region name to avoid the InvalidRegionName error
    )

    # Define the bucket and the file name
    bucket_name = os.getenv("CLOUDFLARE_R2_BUCKET_NAME")
    file_path = f"rss_feeds/{filename}"  # Path where the file will be saved

    # Upload the file to Cloudflare R2
    s3_client.put_object(
        Bucket=bucket_name,
        Key=file_path,
        Body=rss_feed,
        ContentType="application/xml",  # Set content type to XML
        ACL="public-read",  # Ensure the file is publicly accessible
    )

    # Return the publicly accessible URL
    file_url = f"{os.getenv('CLOUDFLARE_R2_BUCKET_URL')}/{file_path}"
    return file_url
