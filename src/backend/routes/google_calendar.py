from flask import Blueprint, redirect, url_for, session, request
from google_auth_oauthlib.flow import Flow
import os
from dotenv import load_dotenv
import json
from backend.database.mongo_connection import collection
import logging

google_calendar_bp = Blueprint('google_calendar_bp', __name__)
logger = logging.getLogger(__name__)

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_AUTH_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# Create the client_secret.json file dynamically
client_secret_data = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uris": [GOOGLE_REDIRECT_URI],
        "auth_uri": GOOGLE_AUTH_URL,
        "token_uri": GOOGLE_TOKEN_URL
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
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    return redirect(url_for('dashboard_bp.dashboard'))

@google_calendar_bp.route("/connect_calendar")
def connect_calendar():
    user_id = session.get("user_id")
    if not user_id:
        return {"error": "User not authenticated"}, 401

    # Preserve query parameters for RSS and Podcast Name
    pod_rss = request.args.get("podRss", "")
    pod_name = request.args.get("podName", "")
    session["podRss"] = pod_rss
    session["podName"] = pod_name

    # Redirect to Google OAuth
    auth_url = (
        f"{GOOGLE_AUTH_URL}?response_type=code"
        f"&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&scope=https://www.googleapis.com/auth/calendar"
        f"&access_type=offline"
    )
    return redirect(auth_url)

@google_calendar_bp.route("/calendar_callback")
def calendar_callback():
    user_id = session.get("user_id")
    if not user_id:
        return {"error": "User not authenticated"}, 401

    code = request.args.get("code")
    if not code:
        return {"error": "Authorization code not provided"}, 400

    try:
        # Save the code in the user's collection under the "googleCal" field
        collection.database.Users.update_one(
            {"_id": user_id}, {"$set": {"googleCal": code}}
        )
        logger.info(f"Google Calendar code saved for user {user_id}")

        # Redirect back to the podprofile page with preserved query parameters
        pod_rss = session.get("podRss", "")
        pod_name = session.get("podName", "")
        return redirect(url_for("podprofile_bp.podprofile", podRss=pod_rss, podName=pod_name))
    except Exception as e:
        logger.error(f"Failed to save Google Calendar code: {e}", exc_info=True)
        return {"error": "Failed to save Google Calendar code"}, 500

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
