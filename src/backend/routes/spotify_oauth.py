from flask import Blueprint, request, jsonify
import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

spotify_oauth_bp = Blueprint("spotify_oauth", __name__)

@spotify_oauth_bp.route('/callback', methods=['GET'])
def callback():
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "Ingen kod skickades."}), 400

    try:
        access_token, refresh_token = exchange_code_for_tokens(code)
        # Här kan du spara tokens i databasen eller .env
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def exchange_code_for_tokens(code):
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
    
    token_url = 'https://accounts.spotify.com/api/token'
    auth_str = f"{client_id}:{client_secret}"
    auth_base64 = base64.b64encode(auth_str.encode()).decode()

    headers = {
        'Authorization': f'Basic {auth_base64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri
    }

    response = requests.post(token_url, headers=headers, data=data)

    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data['access_token']
        refresh_token = token_data['refresh_token']
        return access_token, refresh_token
    else:
        raise Exception(f"Fel vid tokenhämtning: {response.content}")