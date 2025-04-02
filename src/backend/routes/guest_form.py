from flask import Blueprint, request, jsonify, render_template, session
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from backend.database.mongo_connection import collection
import logging
from datetime import datetime, timedelta

guest_form_bp = Blueprint("guest_form", __name__)  # Ensure the blueprint name matches
logger = logging.getLogger(__name__)

@guest_form_bp.route("/", methods=["GET", "POST"])
def guest_form():
    if request.method == 'POST':
        data = request.get_json()
        # Process the form data here
        # For example, save it to the database or send an email
        return jsonify({"message": "Guest form submitted successfully"}), 200
    elif request.method == 'GET':
        return render_template('guest-form/guest-form.html')  # Render the HTML template

@guest_form_bp.route("/available_dates", methods=["GET"])
def available_dates():
    """
    Fetch available dates and times for a guest based on the user's Google Calendar.
    """
    try:
        guest_id = request.args.get("guestId")
        google_cal_token = request.args.get("googleCal")

        if not guest_id or not google_cal_token:
            logger.error("Missing guestId or googleCal token in request.")
            return jsonify({"error": "Missing guestId or googleCal token"}), 400

        # If the googleCal token is just the access token, we should attempt to retrieve full credentials from session
        credentials = Credentials(token=google_cal_token)

        # If the credentials are expired and we have a refresh token, try to refresh them
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())  # Refresh the credentials using the refresh_token

        # If credentials are missing refresh_token, return an error
        if not credentials.refresh_token:
            logger.error("No refresh token available to refresh credentials.")
            return jsonify({"error": "Failed to refresh access token"}), 500

        service = build("calendar", "v3", credentials=credentials)

        # Fetch busy times from the primary calendar
        calendar_id = "primary"
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin="2025-03-01T00:00:00Z",  # Example: Fetch events starting from March 1, 2025
            timeMax="2025-03-31T23:59:59Z",  # Example: Fetch events until March 31, 2025
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
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

        # Example working hours
        working_hours = {"start": "09:00:00", "end": "17:00:00"}

        return jsonify({
            "busy_dates": busy_dates,
            "busy_times": busy_times,
            "working_hours": working_hours
        }), 200

    except Exception as e:
        logger.error(f"Error fetching available dates: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch available dates"}), 500