from flask import Blueprint, redirect, url_for, session, request, jsonify
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
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
    try:
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        session['credentials'] = credentials_to_dict(credentials)

        # Extract the refresh token
        refresh_token = credentials.refresh_token
        if not refresh_token:
            logger.error("❌ ERROR: No refresh token received during OAuth callback.")
            return jsonify({"error": "No refresh token received"}), 400

        # Save the refresh token in the Users collection as googleRefresh
        user_id = session.get("user_id")
        if not user_id:
            logger.error("❌ ERROR: User not authenticated during OAuth callback.")
            return jsonify({"error": "User not authenticated"}), 401

        collection.database.Users.update_one(
            {"_id": user_id},
            {"$set": {"googleRefresh": refresh_token}},  # Save as googleRefresh
            upsert=True
        )

        logger.info(f"✅ Refresh token saved successfully for user {user_id}.")
        return redirect(f"/podprofile?googleToken={refresh_token}")  # Pass refresh token to frontend
    except Exception as e:
        logger.error(f"Error during OAuth callback: {e}", exc_info=True)
        return jsonify({"error": "Failed to complete Google OAuth process"}), 500

@google_calendar_bp.route("/connect_calendar", methods=["POST"])
def connect_calendar():
    try:
        # Retrieve the OAuth token from the request
        token = request.json.get("token")
        if not token:
            logger.error("Missing token in /connect_calendar request.")
            return jsonify({"error": "Missing token"}), 400

        # Use the token to authenticate with Google Calendar API
        credentials = Credentials.from_authorized_user_info(token)
        service = build("calendar", "v3", credentials=credentials)

        # Generate a publicly shareable calendar link
        calendar_list = service.calendarList().list().execute()
        primary_calendar = next(
            (cal for cal in calendar_list.get("items", []) if cal.get("primary")), None
        )
        if not primary_calendar:
            logger.error("Primary calendar not found for user.")
            return jsonify({"error": "Primary calendar not found"}), 404

        calendar_id = primary_calendar["id"]
        shareable_link = f"https://calendar.google.com/calendar/embed?src={calendar_id}"

        # Save the shareable link to the database
        user_id = session.get("user_id")
        if not user_id:
            logger.error("User not authenticated in /connect_calendar request.")
            return jsonify({"error": "User not authenticated"}), 401

        collection.database.Users.update_one(
            {"_id": user_id}, {"$set": {"googleCal": shareable_link}}
        )

        logger.info(f"Google Calendar connected successfully for user {user_id}.")
        return jsonify({"message": "Calendar connected successfully", "googleCal": shareable_link}), 200

    except Exception as e:
        logger.error(f"Error in /connect_calendar: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

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
