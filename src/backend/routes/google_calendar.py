from flask import Blueprint, redirect, url_for, session, request
from google_auth_oauthlib.flow import Flow
from flask import Blueprint, jsonify, session
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta
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
    authorization_url, state = flow.authorization_url(access_type='offline', prompt='consent', include_granted_scopes='true')
    session['state'] = state
    return redirect(authorization_url)

@google_calendar_bp.route('/oauth2callback')
def oauth2callback():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    return redirect(url_for('dashboard_bp.dashboard'))

@google_calendar_bp.route("/api/creator-availability", methods=["GET"])
def fetch_calendar_events():
    try:
        creds_data = session.get("credentials")
        if not creds_data:
            return jsonify({"error": "User not authenticated with Google Calendar"}), 403

        credentials = Credentials(
            token=creds_data["token"],
            refresh_token=creds_data.get("refresh_token"),
            token_uri=creds_data["token_uri"],
            client_id=creds_data["client_id"],
            client_secret=creds_data["client_secret"],
            scopes=creds_data["scopes"]
        )

        service = build("calendar", "v3", credentials=credentials)

        now = datetime.utcnow().isoformat() + "Z"
        end = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            timeMax=end,
            maxResults=100,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])

        unavailable_dates = set()
        for event in events:
            start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date"))
            if start:
                date = start[:10]
                unavailable_dates.add(date)

        return jsonify({"unavailableDates": list(unavailable_dates)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
