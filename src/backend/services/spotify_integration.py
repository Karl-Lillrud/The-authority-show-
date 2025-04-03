from google.cloud import storage
import os
import logging
from werkzeug.utils import secure_filename
import io
import requests
import base64
from dotenv import load_dotenv
from flask import Blueprint, redirect, abort, request

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Google Cloud Storage client
storage_client = storage.Client.from_service_account_json(
    os.getenv("GOOGLE_CLOUD_SERVICE_ACCOUNT_KEY")
)
bucket_name = os.getenv("GOOGLE_CLOUD_BUCKET_NAME")


def get_spotify_access_token():
    """
    Get a fresh access token using the refresh token stored in .env
    """
    # Retrieve Spotify credentials from .env
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")

    # Prepare the request for the Spotify token endpoint
    token_url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f'Basic {base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()}',
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}

    # Make the POST request to get the access token
    response = requests.post(token_url, headers=headers, data=data)

    # Check if the request was successful
    if response.status_code == 200:
        access_token = response.json().get("access_token")
        logger.info(
            f"Spotify access token retrieved successfully: {access_token[:10]}..."
        )  # Log partial token
        return access_token
    else:
        logger.error(
            f"Failed to retrieve Spotify access token: {response.status_code} - {response.text}"
        )
        return None


def upload_episode_to_spotify(access_token, episode):
    """
    Submit the RSS feed URL to Spotify for the podcast.
    """
    # Ensure the show ID is present in the episode data
    show_id = episode.get(
        "podcast_id"
    )  # Correct way to get the podcast_id from episode
    if not show_id:
        logger.error("Podcast ID (show ID) is missing in the episode data.")
        return False

    # Correct Spotify API endpoint for submitting RSS feed
    spotify_api_url = f"https://api.spotify.com/v1/shows/{show_id}/rss"
    logger.info(
        f"Submitting RSS feed to Spotify using URL: {spotify_api_url}"
    )  # Debugging line

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Ensure the RSS feed URL is valid
    rss_feed_url = episode.get("rss_feed_url")
    if not rss_feed_url:
        logger.error("RSS feed URL is missing in the episode data.")
        return False

    logger.info("Spotify does not provide an API for RSS feed submission.")
    logger.info(
        f"Please submit the RSS feed URL manually via Spotify for Podcasters: {rss_feed_url}"
    )
    return False


def save_uploaded_files(files):
    """
    Save uploaded files to Google Cloud Storage and generate URLs for them.
    """
    saved_files = []
    bucket = storage_client.bucket(bucket_name)

    for file in files:
        logger.info(f"Processing file: {file.filename}")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            try:
                blob = bucket.blob(f"mp3_files/{filename}")
                blob.upload_from_file(file, content_type=file.content_type)
                # Construct the public URL
                file_url = f"https://storage.googleapis.com/{bucket_name}/mp3_files/{filename}"
                saved_files.append({"filename": filename, "url": file_url})
                logger.info(f"File uploaded successfully: {file_url}")
            except Exception as e:
                logger.error(f"Failed to upload file {filename}: {e}")
    return saved_files


def allowed_file(filename):
    """
    Check if the uploaded file is of an allowed type (mp3, mp4).
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"mp3", "mp4"}


file_bp = Blueprint("file_bp", __name__)
# Flask Blueprint to handle file serving
file_bp = Blueprint("file_bp", __name__)


# Route to serve the file from Google Cloud Storage (publicly accessible)
@file_bp.route("/files/<filename>", methods=["GET"])
def serve_file(filename):
    """
    Serve the file stored in Google Cloud Storage for public access.
    """
    try:
        # Construct the public URL
        file_url = f"https://storage.googleapis.com/{bucket_name}/mp3_files/{filename}"
        return redirect(file_url)
    except Exception as e:
        logger.error(f"Failed to fetch file: {e}")
        abort(404)  # Return a 404 if the file is not found
