from flask import Blueprint, redirect, url_for, session, request, jsonify
from google_auth_oauthlib.flow import Flow
from backend.database.mongo_connection import collection
from bson import ObjectId
import os
from dotenv import load_dotenv
import json
from backend.database.mongo_connection import collection
import logging
from backend.repository.user_repository import UserRepository
import datetime
import requests

google_calendar_bp = Blueprint('google_calendar_bp', __name__)
logger = logging.getLogger(__name__)

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
GOOGLE_AUTH_URL = os.getenv("GOOGLE_AUTH_URI")
GOOGLE_TOKEN_URL = os.getenv("GOOGLE_TOKEN_URI")

flow = Flow.from_client_config(
    {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uris": [GOOGLE_REDIRECT_URI],
            "auth_uri": GOOGLE_AUTH_URL,
            "token_uri": GOOGLE_TOKEN_URL,
        }
    },
    scopes=["https://www.googleapis.com/auth/calendar"],
    redirect_uri=GOOGLE_REDIRECT_URI,
)

@google_calendar_bp.route('/connect_google_calendar')
def connect_google_calendar():
    # Force prompt to ensure we get a refresh token
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Force consent screen to ensure refresh token
    )
    session['state'] = state
    
    # Store the current user ID in the session for the callback
    if 'user_id' in session:
        logger.info(f"Storing user_id {session['user_id']} for OAuth callback")
        session['oauth_user_id'] = session['user_id']
    else:
        logger.error("No user_id in session when starting OAuth flow")
    
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
