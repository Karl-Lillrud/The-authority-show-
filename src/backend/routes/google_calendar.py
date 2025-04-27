from flask import Blueprint, redirect, url_for, session, request, jsonify
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
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
    code = request.args.get('code')

    if not code:
        logger.error("No authorization code provided in callback")
        return jsonify({"error": "Authorization code not provided"}), 400

    try:
        # Fetch the tokens from the OAuth flow
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials

        # Extract access token and refresh token
        access_token = credentials.token
        refresh_token = credentials.refresh_token
        
        if not refresh_token:
            logger.error("No refresh token returned from Google OAuth")
            return jsonify({"error": "No refresh token received from Google. Please revoke app permissions and try again."}), 400

        # Get the user ID from the session
        # Try both regular user_id and the one we stored specifically for OAuth
        user_id = session.get("user_id") or session.get("oauth_user_id")
        logger.info(f"User ID from session: {user_id}")

        if not user_id:
            logger.error("User ID not found in session.")
            return jsonify({"error": "User not authenticated"}), 401

        # Save tokens to the database - use direct MongoDB update for debugging
        try:
            # First, try direct MongoDB update to isolate the issue
            update_result = collection.database.Users.update_one(
                {"_id": user_id},
                {"$set": {
                    "googleCalAccessToken": access_token,
                    "googleCalRefreshToken": refresh_token,
                    "googleCalTokenUpdated": datetime.datetime.now()
                }}
            )
            
            logger.info(f"Direct MongoDB update result: matched={update_result.matched_count}, modified={update_result.modified_count}")
            
            # Now also try with the repository method
            user_repo = UserRepository()
            repo_result = user_repo.save_tokens(user_id, access_token, refresh_token)
            logger.info(f"Repository save_tokens result: {repo_result}")
            
            # Verify token saving by querying the user document
            user = collection.database.Users.find_one({"_id": user_id})
            if user:
                logger.info(f"User document after token update: {user.get('googleCalAccessToken', 'Not found')} / {user.get('googleCalRefreshToken', 'Not found')}")
                if not user.get('googleCalAccessToken') or not user.get('googleCalRefreshToken'):
                    logger.error(f"Tokens not found in user document after update")
            else:
                logger.error(f"User document not found after token update for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error saving tokens: {e}", exc_info=True)
            return jsonify({"error": f"Failed to save tokens: {str(e)}"}), 500

        # Optionally store the credentials in the session (for future requests)
        session['credentials'] = credentials_to_dict(credentials)

        # Redirect user to the podprofile page
        return redirect(f"/podprofile?googleToken={access_token}&podRss=&podName=")

    except Exception as e:
        logger.error(f"Error during OAuth callback: {e}", exc_info=True)
        return jsonify({"error": f"Failed to complete Google OAuth process: {str(e)}"}), 500


@google_calendar_bp.route("/connect_calendar", methods=["POST"])
def connect_calendar():
    try:
        # Retrieve the OAuth token from the request
        token_data = request.json
        if not token_data:
            logger.error("Missing token data in /connect_calendar request.")
            return jsonify({"error": "Missing token data"}), 400

        # Get the access token and refresh token
        access_token = token_data.get("token")
        refresh_token = token_data.get("refresh_token")
        
        if not access_token:
            logger.error("Missing access token in request")
            return jsonify({"error": "Missing access token"}), 400

        # Use the token to authenticate with Google Calendar API
        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET
        )
        
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

        # Save the shareable link and tokens to the database
        user_id = session.get("user_id")
        if not user_id:
            logger.error("User not authenticated in /connect_calendar request.")
            return jsonify({"error": "User not authenticated"}), 401

        # Save both the shareable link and the tokens
        update_result = collection.database.Users.update_one(
            {"_id": user_id}, 
            {"$set": {
                "googleCal": shareable_link,
                "googleCalAccessToken": access_token,
                "googleCalRefreshToken": refresh_token
            }}
        )
        
        logger.info(f"Update result: matched={update_result.matched_count}, modified={update_result.modified_count}")

        # Verify the update
        user = collection.database.Users.find_one({"_id": user_id})
        if user:
            logger.info(f"User document after update: googleCal={user.get('googleCal', 'Not found')}, tokens={bool(user.get('googleCalAccessToken'))}/{bool(user.get('googleCalRefreshToken'))}")

        logger.info(f"Google Calendar connected successfully for user {user_id}.")
        return jsonify({"message": "Calendar connected successfully", "googleCal": shareable_link}), 200

    except Exception as e:
        logger.error(f"Error in /connect_calendar: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@google_calendar_bp.route("/calendar_callback")
def calendar_callback():
    user_id = session.get("user_id")
    if not user_id:
        logger.error("User ID not found in session during calendar_callback")
        return {"error": "User not authenticated"}, 401

    code = request.args.get("code")
    if not code:
        logger.error("No authorization code provided in calendar_callback")
        return {"error": "Authorization code not provided"}, 400

    try:
        # Exchange the code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        
        logger.info(f"Exchanging code for tokens with data: {data}")
        response = requests.post(token_url, data=data)
        
        if not response.ok:
            logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
            return {"error": f"Token exchange failed: {response.text}"}, response.status_code
            
        tokens = response.json()
        logger.info(f"Received tokens: access_token={bool(tokens.get('access_token'))}, refresh_token={bool(tokens.get('refresh_token'))}")
        
        # Save both the code and the tokens
        update_result = collection.database.Users.update_one(
            {"_id": user_id}, 
            {"$set": {
                "googleCal": code,  # Keep the original behavior
                "googleCalAccessToken": tokens.get("access_token"),
                "googleCalRefreshToken": tokens.get("refresh_token")
            }}
        )
        
        logger.info(f"Update result: matched={update_result.matched_count}, modified={update_result.modified_count}")
        
        # Verify the update
        user = collection.database.Users.find_one({"_id": user_id})
        if user:
            logger.info(f"User document after update: googleCal={user.get('googleCal', 'Not found')}, tokens={bool(user.get('googleCalAccessToken'))}/{bool(user.get('googleCalRefreshToken'))}")
        
        logger.info(f"Google Calendar code and tokens saved for user {user_id}")

        # Redirect back to the podprofile page with preserved query parameters
        pod_rss = session.get("podRss", "")
        pod_name = session.get("podName", "")
        return redirect(url_for("podprofile_bp.podprofile", podRss=pod_rss, podName=pod_name))
    except Exception as e:
        logger.error(f"Failed to save Google Calendar code and tokens: {e}", exc_info=True)
        return {"error": f"Failed to save Google Calendar code and tokens: {str(e)}"}, 500

@google_calendar_bp.route("/get_google_cal_token", methods=["GET"])
def get_google_cal_token():
    """
    Get the Google Calendar access token for the current user.
    This endpoint is used by the frontend to retrieve the token when needed.
    """
    try:
        # Get the user ID from the session
        user_id = session.get("user_id")
        if not user_id:
            logger.error("User not authenticated in get_google_cal_token request.")
            return jsonify({"error": "User not authenticated"}), 401

        # Get the user from the database
        user_repo = UserRepository()
        user = user_repo.get_user_by_id(user_id)
        if not user:
            logger.error(f"User with ID {user_id} not found.")
            return jsonify({"error": "User not found"}), 404

        # Get the access token
        access_token = user.get("googleCalAccessToken")
        if not access_token:
            logger.error(f"No Google Calendar access token found for user {user_id}.")
            return jsonify({"error": "No Google Calendar access token found"}), 404

        # Return the token
        return jsonify({"token": access_token}), 200

    except Exception as e:
        logger.error(f"Error getting Google Calendar token: {e}", exc_info=True)
        return jsonify({"error": f"Failed to get Google Calendar token: {str(e)}"}), 500

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
