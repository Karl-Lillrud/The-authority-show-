import requests
import base64
import os
import boto3
from werkzeug.utils import secure_filename
import logging
from dotenv import load_dotenv
from flask import Blueprint, redirect, send_file, abort, request
from bson.objectid import ObjectId
import io  # Add this import for BytesIO


# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Initialize R2 client (AWS S3-compatible)
s3 = boto3.client(
    's3',
    endpoint_url='https://8dd08def3e3e74358dcbf2fec09bf125.r2.cloudflarestorage.com',  # Correct Cloudflare R2 endpoint URL,
    aws_access_key_id=os.getenv('CLOUDFLARE_R2_ACCESS_KEY'),  # R2 Access Key
    aws_secret_access_key=os.getenv('CLOUDFLARE_R2_SECRET_KEY'),  # R2 Secret Key
)

# Get the upload folder path from environment variables
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')  # Default is 'uploads'

def get_spotify_access_token():
    """
    Get a fresh access token using the refresh token stored in .env
    """
    # Retrieve Spotify credentials from .env
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    refresh_token = os.getenv('SPOTIFY_REFRESH_TOKEN')

    # Prepare the request for the Spotify token endpoint
    token_url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Authorization': f'Basic {base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }

    # Make the POST request to get the access token
    response = requests.post(token_url, headers=headers, data=data)
    
    # Check if the request was successful
    if response.status_code == 200:
        access_token = response.json().get('access_token')
        logger.info(f"Spotify access token retrieved successfully: {access_token[:10]}...")  # Log partial token
        return access_token
    else:
        logger.error(f"Failed to retrieve Spotify access token: {response.status_code} - {response.text}")
        return None

def upload_episode_to_spotify(access_token, episode):
    """
    Submit the RSS feed URL to Spotify for the podcast.
    """
    # Ensure the show ID is present in the episode data
    show_id = episode.get('podcast_id')  # Correct way to get the podcast_id from episode
    if not show_id:
        logger.error("Podcast ID (show ID) is missing in the episode data.")
        return False

    # Correct Spotify API endpoint for submitting RSS feed
    spotify_api_url = f"https://api.spotify.com/v1/shows/{show_id}/rss"
    logger.info(f"Submitting RSS feed to Spotify using URL: {spotify_api_url}")  # Debugging line

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Ensure the RSS feed URL is valid
    rss_feed_url = episode.get('rss_feed_url')
    if not rss_feed_url:
        logger.error("RSS feed URL is missing in the episode data.")
        return False

    logger.info("Spotify does not provide an API for RSS feed submission.")
    logger.info(f"Please submit the RSS feed URL manually via Spotify for Podcasters: {rss_feed_url}")
    return False

def save_uploaded_files(files):
    """
    Save uploaded files to Cloudflare R2 and generate URLs for them.
    """
    saved_files = []
    for file in files:
        logger.info(f"Processing file: {file.filename}")  # Log file name
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            try:
                # Wrap the file in a BytesIO buffer to ensure it remains open
                file_buffer = io.BytesIO(file.read())
                file_buffer.seek(0)  # Reset the buffer pointer to the beginning

                # Upload to Cloudflare R2 (equivalent of AWS S3)
                s3.upload_fileobj(
                    file_buffer,
                    os.getenv('CLOUDFLARE_R2_BUCKET_NAME'),  # Use the correct bucket name
                    filename,
                    ExtraArgs={'ACL': 'public-read'}  # Ensure the file is publicly accessible
                )
                # Construct the public URL
                file_url = f"{os.getenv('CLOUDFLARE_R2_BUCKET_URL')}/{filename}"
                saved_files.append({"filename": filename, "url": file_url})
                logger.info(f"File uploaded successfully: {file_url}")
            except Exception as e:
                logger.error(f"Failed to upload file {filename}: {e}")
                logger.error(f"Error details: {e}")
    return saved_files

def allowed_file(filename):
    """
    Check if the uploaded file is of an allowed type (mp3, mp4).
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mp3', 'mp4'}

file_bp = Blueprint("file_bp", __name__)
# Flask Blueprint to handle file serving
file_bp = Blueprint("file_bp", __name__)

# Route to serve the file from Cloudflare R2 (publicly accessible)
@file_bp.route("/files/<filename>", methods=["GET"])
def serve_file(filename):
    """
    Serve the file stored in Cloudflare R2 for public access.
    """
    try:
        # Construct the public URL
        file_url = f"https://<account_id>.r2.cloudflarestorage.com/mediastorage/{filename}"
        return redirect(file_url)
    except Exception as e:
        logger.error(f"Failed to fetch file: {e}")
        abort(404)  # Return a 404 if the file is not found