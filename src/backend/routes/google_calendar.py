from flask import Blueprint, redirect, url_for, session, request
from google_auth_oauthlib.flow import Flow
from backend.database.mongo_connection import collection
from bson import ObjectId
import os
from dotenv import load_dotenv
import json

google_calendar_bp = Blueprint('google_calendar_bp', __name__)

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_AUTH_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

# Create the client_secret.json file dynamically
client_secret_data = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uris": [GOOGLE_REDIRECT_URI],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
}

with open('client_secret.json', 'w') as json_file:
    json.dump(client_secret_data, json_file)

flow = Flow.from_client_secrets_file(
    'client_secret.json',
    scopes=['https://www.googleapis.com/auth/calendar'],
    redirect_uri=GOOGLE_REDIRECT_URI
)

@google_calendar_bp.route('/connect_google_calendar')
def connect_google_calendar():
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    session['state'] = state
    return redirect(authorization_url)

@google_calendar_bp.route('/oauth2callback')
def oauth2callback():
    user_id = session.get("user_id")
    if not user_id:
        return "User not authenticated", 401

    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    token_data = credentials_to_dict(credentials)

    # Save to MongoDB
    collection.database.Accounts.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"googleCredentials": token_data}}
    )

    session['credentials'] = token_data
    return redirect(url_for('dashboard_bp.dashboard'))

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
