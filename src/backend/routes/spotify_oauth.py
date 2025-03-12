from flask import Blueprint, request, jsonify, redirect
from backend.services.spotify_oauth import get_spotify_access_token
import os
import requests

spotify_oauth_bp = Blueprint("spotify_oauth", __name__)

@spotify_oauth_bp.route('/callback', methods=['GET'])
def callback():
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "Ingen kod skickades"}), 400
    
    # Byt ut koden mot ett access token
    try:
        token_data = exchange_code_for_token(code)
        return jsonify({
            "access_token": token_data.get('access_token'),
            "refresh_token": token_data.get('refresh_token')
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def exchange_code_for_token(code):
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
    
    token_url = 'https://accounts.spotify.com/api/token'
    auth_str = f"{client_id}:{client_secret}"
    headers = {
        'Authorization': f'Basic {base64.b64encode(auth_str.encode()).decode()}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    return response.json()  # Return access and refresh tokens
