import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

# Hämta access token med hjälp av OAuth 2.0
def get_spotify_access_token():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")
    
    if not client_id or not client_secret or not refresh_token:
        raise ValueError("Spotify-uppgifter saknas i .env")
    
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
        raise Exception(f"Misslyckades att hämta access token: {response.content}")
    
# Generera auktoriseringslänk
def get_authorization_url():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
    scope = "playlist-read-private playlist-modify-public"  # Justera efter behov
    
    auth_url = f"https://accounts.spotify.com/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope={scope}"
    
    return auth_url
