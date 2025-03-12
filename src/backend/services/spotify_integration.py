import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

def get_spotify_access_token():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")
    if not client_id or not client_secret or not refresh_token:
        raise ValueError("Saknar Spotify-uppgifter i .env")
    token_url = 'https://accounts.spotify.com/api/token'
    auth_str = f"{client_id}:{client_secret}"
    headers = {
        'Authorization': f'Basic {base64.b64encode(auth_str.encode()).decode()}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    response = requests.post(token_url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception(f"Misslyckades hämta access token: {response.content}")

def upload_episode_to_spotify(episode_data):
    access_token = get_spotify_access_token()
    api_endpoint = 'https://api.spotify.com/v1/podcasts'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    response = requests.post(api_endpoint, headers=headers, json=episode_data)
    return response
