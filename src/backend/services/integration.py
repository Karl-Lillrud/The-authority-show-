# services/integration.py
import requests
import base64
import os
from werkzeug.utils import secure_filename
from bson import Binary

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
    return None

def upload_episode_to_spotify(access_token, episode):
    spotify_api_url = "https://api.spotify.com/v1/podcasts"  # Just an example endpoint
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    episode_data = {
        "title": episode['title'],
        "description": episode['description'],
        "file_url": episode['audioUrl'],  # Assuming the episode has an audio file URL
    }

    response = requests.post(spotify_api_url, headers=headers, json=episode_data)
    return response.status_code == 201  # Assuming 201 indicates success

def save_uploaded_files(files):
    saved_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_data = Binary(file.read())
            saved_files.append({"filename": filename, "data": file_data})
    return saved_files

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mp3', 'mp4'}
