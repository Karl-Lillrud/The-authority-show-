from flask import Blueprint, request, jsonify, render_template, session
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from backend.database.mongo_connection import collection
import logging
from datetime import datetime, timedelta
import os
from backend.repository.user_repository import UserRepository
from google.auth.transport.requests import Request

guest_form_bp = Blueprint("guest_form", __name__)
logger = logging.getLogger(__name__)

@guest_form_bp.route("/", methods=["GET", "POST"])
def guest_form():
    if request.method == 'POST':
        data = request.get_json()
        
        # Process the form data (Save to the database, etc.)
        guest_id = save_guest_to_db(data)  # Assume this function saves the guest to your database
        
        # Create Google Calendar event
        google_cal_token = data.get("googleCalToken")  # Ensure the token is passed in the data
        
        if google_cal_token:
            try:
                # Check if there's an existing calendar event to delete
                existing_event_id = data.get("calendarEventId")
                if existing_event_id:
                    # Delete the existing event before creating a new one
                    delete_google_calendar_event(existing_event_id, google_cal_token)
                    logger.info(f"Deleted existing calendar event: {existing_event_id}")
                
                # Now create a new event
                event_result = create_google_calendar_event(data, google_cal_token)
                
                # Update the guest record with the new event ID
                if event_result and 'id' in event_result:
                    update_guest_calendar_event_id(guest_id, event_result['id'])
                    
                return jsonify({"message": "Guest form submitted and event created successfully", "eventId": event_result.get('id')}), 200
            except Exception as e:
                logger.error(f"Error creating Google Calendar event: {str(e)}")
                return jsonify({"error": "Failed to create Google Calendar event"}), 500
        else:
            return jsonify({"message": "Guest form submitted successfully, but Google Calendar event creation failed. Token missing."}), 200
            
    elif request.method == 'GET':
        # Handle GET request logic here
        user_id = session.get("user_id")
        google_cal_token = None
        
        if user_id:
            # Try to get the token from the database
            user_repo = UserRepository()
            user = user_repo.get_user_by_id(user_id)
            if user and user.get("googleCalAccessToken"):
                google_cal_token = user.get("googleCalAccessToken")
                logger.info(f"Found Google Calendar token for user {user_id}")
        
        # Make sure to return a response for the GET request (either render a template or return JSON)
        return render_template('guest-form/guest-form.html', google_cal_token=google_cal_token)


def create_google_calendar_event(data, google_cal_token):
    """
    Create a Google Calendar event using the Google Calendar API.
    """
    try:
        # Retrieve Google Calendar token and user information
        user_id = session.get("user_id")
        user_repo = UserRepository()
        user = user_repo.get_user_by_id(user_id)

        # Refresh the credentials using the access token and refresh token
        credentials = Credentials(
            token=google_cal_token,
            refresh_token=user.get("googleCalRefreshToken"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
        )

        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())  # Refresh expired token

        # Create the Google Calendar service instance
        service = build("calendar", "v3", credentials=credentials)
        event = {
            'summary': f"Podcast Recording: {data['firstName']}",
            'location': data.get('company', 'N/A'),
            'description': f"Recording with {data['firstName']} from {data['company']}",
            'start': {
                'dateTime': f"{data['recordingDate']}T{data['recordingTime']}:00",
                'timeZone': 'Europe/Stockholm',
            },
            'end': {
                'dateTime': f"{data['recordingDate']}T{data['recordingTime']}:30",
                'timeZone': 'Europe/Stockholm',  # Adjust duration as necessary
            },
            'attendees': [
                {'email': data['email']},
            ],
        }

        # Create the event on the user's primary calendar
        event_result = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()

        logger.info(f"Created event: {event_result['summary']} at {event_result['start']['dateTime']}")

        return event_result

    except HttpError as error:
        logger.error(f"An error occurred while creating the event: {error}")
        raise error


def delete_google_calendar_event(event_id, google_cal_token):
    """
    Delete a Google Calendar event using the Google Calendar API.
    """
    try:
        # Retrieve Google Calendar token and user information
        user_id = session.get("user_id")
        user_repo = UserRepository()
        user = user_repo.get_user_by_id(user_id)

        # Refresh the credentials using the access token and refresh token
        credentials = Credentials(
            token=google_cal_token,
            refresh_token=user.get("googleCalRefreshToken"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
        )

        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())  # Refresh expired token

        # Create the Google Calendar service instance
        service = build("calendar", "v3", credentials=credentials)
        
        # Delete the event from the user's primary calendar
        service.events().delete(
            calendarId='primary',
            eventId=event_id
        ).execute()

        logger.info(f"Deleted event: {event_id}")
        return True

    except HttpError as error:
        logger.error(f"An error occurred while deleting the event: {error}")
        raise error


def update_guest_calendar_event_id(guest_id, event_id):
    """
    Update the guest record with the calendar event ID.
    """
    try:
        collection.database.Guests.update_one(
            {"_id": guest_id},
            {"$set": {"calendarEventId": event_id}}
        )
        logger.info(f"Updated guest {guest_id} with calendar event ID {event_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating guest with calendar event ID: {e}")
        return False


def save_guest_to_db(data):
    """
    Function to save guest data to the database.
    """
    guest_data = {
        "guestId": data.get("guestId"),  # Include the guest ID
        "name": data.get("firstName"),
        "email": data["email"],
        "company": data["company"],
        "phone": data["phone"],
        "recordingDate": data["recordingDate"],
        "recordingTime": data["recordingTime"],
        "bio": data["bio"],
        "interest": data["interest"],
        "socialMedia": data.get("socialMedia", []),
        "recommendedGuests": data.get("recommendedGuests", []),
        "list": data.get("list", ""),
        "notes": data.get("notes", ""),
        "updatesOption": data.get("updatesOption", "no"),
        "profilePhoto": data.get("profilePhoto"),
        "createdAt": datetime.now(),
        "status": "pending",  # Initial status for the guest
        "calendarEventId": data.get("calendarEventId")  # Store the calendar event ID
    }
    # Save the guest data to the guests collection
    guest_id = collection.database.Guests.insert_one(guest_data).inserted_id
    return guest_id

# RENAMED this route function to avoid the naming conflict
@guest_form_bp.route("/create-google-calendar-event", methods=["POST"])
def create_calendar_event_route():
    """
    Create or update a Google Calendar event using the Google Calendar API.
    If an existing event ID is provided, it will delete that event before creating a new one.
    """
    try:
        data = request.get_json()
        logger.info(f"Received calendar event data: {data}")

        # Ensure necessary data is provided
        if not data.get('summary') or not data.get('start') or not data.get('end'):
            return jsonify({'error': 'Missing required fields'}), 400

        google_cal_token = data.get('googleCalToken')  # The token sent from frontend
        existing_event_id = data.get('calendarEventId')  # Get existing event ID if available

        if not google_cal_token:
            return jsonify({"error": "Google Calendar token is missing."}), 400

        # Retrieve user info and credentials for Google Calendar API
        user_id = session.get("user_id")
        user_repo = UserRepository()
        user = user_repo.get_user_by_id(user_id)

        if not user:
            return jsonify({"error": "User not found."}), 404

        credentials = Credentials(
            token=google_cal_token,
            refresh_token=user.get("googleCalRefreshToken"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
        )

        # Refresh the credentials if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())  # Refresh the credentials

        # Create Google Calendar service instance
        service = build("calendar", "v3", credentials=credentials)
        
        # If there's an existing event ID, delete it first
        if existing_event_id:
            try:
                logger.info(f"Attempting to delete existing calendar event: {existing_event_id}")
                service.events().delete(
                    calendarId='primary',
                    eventId=existing_event_id
                ).execute()
                logger.info(f"Successfully deleted existing calendar event: {existing_event_id}")
            except HttpError as error:
                # If the event doesn't exist, just log it and continue
                if error.resp.status == 404:
                    logger.warning(f"Event {existing_event_id} not found, continuing with creation")
                else:
                    logger.error(f"Error deleting event {existing_event_id}: {error}")
                    return jsonify({'error': f"Error deleting existing event: {str(error)}"}), 500

        event = {
            'summary': data['summary'],
            'description': data.get('description', ''),
            'start': {
                'dateTime': data['start']['dateTime'],
                'timeZone': data['start']['timeZone'],
            },
            'end': {
                'dateTime': data['end']['dateTime'],
                'timeZone': data['end']['timeZone'],
            },
            'attendees': data.get('attendees', []),  # Optional attendees list
        }

        # Create event on the user's primary calendar
        event_result = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()

        logger.info(f"Created new event: {event_result['summary']} at {event_result['start']['dateTime']} with ID: {event_result['id']}")
        
        # If this is updating a guest record, update the calendar event ID
        guest_id = data.get('guestId')
        if guest_id:
            try:
                collection.database.Guests.update_one(
                    {"_id": guest_id},
                    {"$set": {"calendarEventId": event_result['id']}}
                )
                logger.info(f"Updated guest {guest_id} with new calendar event ID {event_result['id']}")
            except Exception as e:
                logger.error(f"Error updating guest with calendar event ID: {e}")

        return jsonify({
            'message': 'Google Calendar event created successfully',
            'eventId': event_result['id']
        }), 200

    except HttpError as error:
        logger.error(f"An error occurred while creating the event: {error}")
        return jsonify({'error': str(error)}), 500

    except Exception as e:
        logger.error(f"Error creating Google Calendar event: {e}", exc_info=True)
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500

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

# Add a new route to explicitly handle calendar event deletion

@guest_form_bp.route("/delete-calendar-event", methods=["POST"])
def delete_calendar_event_route():
    """
    Delete a Google Calendar event using the Google Calendar API.
    """
    try:
        data = request.get_json()
        
        # Ensure necessary data is provided
        event_id = data.get('eventId')
        google_cal_token = data.get('googleCalToken')
        
        if not event_id:
            return jsonify({'error': 'Missing event ID'}), 400
            
        if not google_cal_token:
            return jsonify({"error": "Google Calendar token is missing."}), 400

        # Retrieve user info and credentials for Google Calendar API
        user_id = session.get("user_id")
        user_repo = UserRepository()
        user = user_repo.get_user_by_id(user_id)

        if not user:
            return jsonify({"error": "User not found."}), 404

        credentials = Credentials(
            token=google_cal_token,
            refresh_token=user.get("googleCalRefreshToken"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
        )

        # Refresh the credentials if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())  # Refresh the credentials

        # Create Google Calendar service instance
        service = build("calendar", "v3", credentials=credentials)
        
        # Delete the event
        try:
            service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            logger.info(f"Successfully deleted calendar event: {event_id}")
            
            return jsonify({
                'message': 'Google Calendar event deleted successfully',
                'eventId': event_id
            }), 200
            
        except HttpError as error:
            # If the event doesn't exist, return success anyway
            if error.resp.status == 404:
                logger.warning(f"Event {event_id} not found, but considering deletion successful")
                return jsonify({
                    'message': 'Event not found, but considering deletion successful',
                    'eventId': event_id
                }), 200
            else:
                logger.error(f"Error deleting event {event_id}: {error}")
                return jsonify({'error': f"Error deleting event: {str(error)}"}), 500

    except Exception as e:
        logger.error(f"Error deleting Google Calendar event: {e}", exc_info=True)
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500
