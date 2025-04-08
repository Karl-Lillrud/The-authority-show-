from flask import Blueprint, request, jsonify, render_template, session
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from backend.database.mongo_connection import collection
import logging
from datetime import datetime, timedelta
import os
from backend.repository.user_repository import UserRepository

guest_form_bp = Blueprint("guest_form", __name__)
logger = logging.getLogger(__name__)

@guest_form_bp.route("/", methods=["GET", "POST"])
def guest_form():
    if request.method == 'POST':
        data = request.get_json()
        # Process the form data here
        # For example, save it to the database or send an email
        return jsonify({"message": "Guest form submitted successfully"}), 200
    elif request.method == 'GET':
        # Pass the Google Calendar token to the template if available
        user_id = session.get("user_id")
        google_cal_token = None
        
        if user_id:
            # Try to get the token from the database
            user_repo = UserRepository()
            user = user_repo.get_user_by_id(user_id)
            if user and user.get("googleCalAccessToken"):
                google_cal_token = user.get("googleCalAccessToken")
                logger.info(f"Found Google Calendar token for user {user_id}")
        
        return render_template('guest-form/guest-form.html', google_cal_token=google_cal_token)

@guest_form_bp.route("/available_dates", methods=["GET"])
def available_dates():
    """
    Fetch available dates and times for a guest based on the user's Google Calendar.
    """
    try:
        # Get the authenticated user's ID from the session instead of using guestId
        user_id = session.get("user_id")
        if not user_id:
            logger.error("User not authenticated in available_dates request.")
            return jsonify({"error": "User not authenticated"}), 401

        # Get the Google Calendar access token from the request
        google_cal_token = request.args.get("googleCal")
        if not google_cal_token:
            logger.error("Missing googleCal token in request.")
            return jsonify({"error": "Missing Google Calendar token"}), 400

        # Log the request parameters for debugging
        logger.info(f"Fetching available dates for user {user_id} with token {google_cal_token[:10]}...")

        # Retrieve the user's refresh token from the database
        user_repo = UserRepository()
        user = user_repo.get_user_by_id(user_id)
        if not user:
            logger.error(f"User with ID {user_id} not found.")
            return jsonify({"error": "User not found"}), 404

        # Log the user document for debugging
        logger.info(f"User document: {user.keys() if user else 'None'}")

        refresh_token = user.get("googleCalRefreshToken")
        if not refresh_token:
            logger.error(f"No refresh token available for user {user_id}.")
            return jsonify({"error": "No refresh token available. Please connect your Google Calendar first."}), 400

        # Create credentials using the access token and refresh token
        credentials = Credentials(
            token=google_cal_token,  # Access token
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
        )

        # Refresh the credentials if expired
        if credentials.expired and credentials.refresh_token:
            logger.info("Refreshing expired credentials")
            credentials.refresh(Request())  # Refresh the credentials using the refresh token

        # Use the credentials to interact with the Google Calendar API
        service = build("calendar", "v3", credentials=credentials)
        calendar_id = "primary"
        
        # Get the current date and calculate a month from now
        now = datetime.now()
        one_month_later = now + timedelta(days=30)
        
        # Format dates for the API request
        time_min = now.strftime("%Y-%m-%dT00:00:00Z")
        time_max = one_month_later.strftime("%Y-%m-%dT23:59:59Z")
        
        logger.info(f"Fetching events from {time_min} to {time_max}")
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        logger.info(f"Found {len(events)} events in calendar")
        
        busy_dates = []
        busy_times = {}

        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))

            if "dateTime" in event["start"]:
                date = start.split("T")[0]
                if date not in busy_times:
                    busy_times[date] = []
                busy_times[date].append({"start": start, "end": end})
            else:
                busy_dates.append(start)

        # Get working hours from user preferences or use default
        working_hours = {"start": "09:00:00", "end": "17:00:00"}
        
        # If user has custom working hours, use those instead
        if user.get("workingHoursStart") and user.get("workingHoursEnd"):
            working_hours = {
                "start": user.get("workingHoursStart"),
                "end": user.get("workingHoursEnd")
            }

        logger.info(f"Returning busy dates: {len(busy_dates)}, busy times: {len(busy_times)}")
        return jsonify({
            "busy_dates": busy_dates,
            "busy_times": busy_times,
            "working_hours": working_hours
        }), 200

    except Exception as e:
        logger.error(f"Error fetching available dates: {e}", exc_info=True)
        return jsonify({"error": f"Failed to fetch available dates: {str(e)}"}), 500
