import requests
import base64
import os
from werkzeug.utils import secure_filename
from bson import Binary
import logging
from dotenv import load_dotenv
from backend.database.mongo_connection import get_fs

load_dotenv()

logger = logging.getLogger(__name__)
fs = get_fs()

UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')  # Define the upload folder

def get_spotify_access_token():
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    refresh_token = os.getenv('SPOTIFY_REFRESH_TOKEN')

    token_url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Authorization': f'Basic {base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }

    response = requests.post(token_url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json().get('access_token')
    logger.error(f"Failed to retrieve Spotify access token: {response.status_code} - {response.text}")
    return None

def upload_episode_to_spotify(access_token, episode):
    spotify_api_url = f"https://api.spotify.com/v1/shows/{episode['podcast_id']}/episodes"  # Correct endpoint
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Ensure audioUrl is a valid URL
    audio_url = episode.get('audioUrl')  # This now contains the full path

    if not audio_url:
        logger.error("Audio URL is missing in the episode data.")
        return False

    episode_data = {
        "title": episode['title'],
        "description": episode['description'],
        "audio_url": audio_url,  # Use the full audio URL
        "publish_date": episode['publishDate'].isoformat() if episode.get('publishDate') else None,
        "duration_ms": episode['duration'] * 1000 if episode.get('duration') else None,
    }

    logger.info(f"Uploading episode to Spotify with data: {episode_data}")

    response = requests.post(spotify_api_url, headers=headers, json=episode_data)
    if response.status_code == 201:
        logger.info("Episode uploaded successfully to Spotify.")
        return True
    elif response.status_code == 405:
        logger.error(f"Failed to upload episode to Spotify: {response.status_code} - Method Not Allowed")
        return False
    else:
        logger.error(f"Failed to upload episode to Spotify: {response.status_code} - {response.text}")
        return False

def save_uploaded_files(files):
    saved_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_id = fs.put(file.stream, filename=filename)
            
            # Construct the Anchor URL format for the MP3 file
            # You can adjust the URL format as per your requirements
            file_url = f"https://anchor.fm/s/fd781dd0/podcast/play/{file_id}/{filename}"  # Adjust this URL pattern as needed
            
            saved_files.append({"filename": filename, "url": file_url})
    return saved_files


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mp3', 'mp4'}
