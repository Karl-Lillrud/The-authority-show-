from flask import Blueprint, request, jsonify, render_template, session
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
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
def get_available_dates():
    """
    Fetch the inviting user's available calendar dates and working hours from Google Calendar.
    """
    try:
        guest_id = request.args.get("guestId")
        google_cal_token = request.args.get("googleCal")

        if not guest_id or not google_cal_token:
            logger.error("Guest ID or Google Calendar token is missing in the request.")
            return {"error": "Guest ID and Google Calendar token are required"}, 400

        # Use the googleCal token to fetch events and working hours from Google Calendar
        credentials = Credentials(token=google_cal_token)
        service = build("calendar", "v3", credentials=credentials)

        # Fetch events for the next 30 days
        now = datetime.utcnow()
        time_min = now.isoformat() + "Z"
        time_max = (now + timedelta(days=30)).isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        busy_dates = set()
        busy_times = {}

        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))
            date = start.split("T")[0]
            busy_dates.add(date)

            if "T" in start and "T" in end:
                start_time = start.split("T")[1]
                end_time = end.split("T")[1]
                if date not in busy_times:
                    busy_times[date] = []
                busy_times[date].append({"start": start_time, "end": end_time})

        # Fetch the user's working hours
        try:
            settings = service.settings().get(setting="workingHours").execute()
            working_hours = settings.get("value", {"start": "09:00:00", "end": "17:00:00"})
        except HttpError:
            working_hours = {"start": "09:00:00", "end": "17:00:00"}  # Default working hours

        return jsonify({
            "busy_dates": list(busy_dates),
            "busy_times": busy_times,
            "working_hours": working_hours
        }), 200

    except Exception as e:
        logger.error(f"Failed to fetch available dates: {e}", exc_info=True)
        return {"error": "Failed to fetch available dates"}, 500
