import os
import base64
import requests
from dotenv import load_dotenv
from flask import redirect, url_for, request

load_dotenv()

# Spotify Configuration from .env file
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SPOTIFY_REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")

def get_spotify_access_token():
    """
    Get a fresh access token using the refresh token stored in .env
    """
    url = "https://accounts.spotify.com/api/token"
    auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": SPOTIFY_REFRESH_TOKEN,
    }

    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        access_token = response.json().get("access_token")
        return access_token
    else:
        print(f"Failed to get access token: {response.status_code}")
        return None

def handle_spotify_oauth_callback(request):
    """
    Handle the Spotify OAuth callback and exchange the code for tokens.
    """
    code = request.args.get("code")
    
    if code:
        access_token, refresh_token = exchange_code_for_tokens(code)
        
        if access_token and refresh_token:
            # Save tokens securely and store them in session or database
            print("Successfully authenticated with Spotify.")
            return redirect(url_for('your_next_route'))  # Replace with your next route
        else:
            print("Failed to exchange authorization code for tokens.")
            return {"error": "Failed to exchange authorization code for tokens."}
    else:
        return {"error": "No code provided."}

def exchange_code_for_tokens(code):
    """
    Exchange authorization code for access and refresh tokens
    """
    url = "https://accounts.spotify.com/api/token"
    auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
    }

    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        os.environ["SPOTIFY_REFRESH_TOKEN"] = refresh_token  # Save refresh token securely
        return access_token, refresh_token
    return None, None
