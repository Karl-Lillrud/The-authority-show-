import os
import smtplib
import uuid
from flask import Blueprint, request, jsonify, render_template
from azure.cosmos import CosmosClient, PartitionKey
from werkzeug.utils import secure_filename
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask Blueprint
pickadate_bp = Blueprint('pickadate_bp', __name__)

# Cosmos DB Configuration
COSMOS_ENDPOINT = os.getenv('COSMOS_ENDPOINT')
COSMOS_KEY = os.getenv('COSMOS_KEY')
DATABASE_NAME = 'podmanagedb'
CONTAINER_NAME = 'bookings'

if not COSMOS_ENDPOINT or not COSMOS_KEY:
    raise ValueError("Missing CosmosDB credentials. Check your .env file.")

# Initialize CosmosDB Client
try:
    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.get_database_client(DATABASE_NAME)
    container = database.get_container_client(CONTAINER_NAME)
except Exception as e:
    raise RuntimeError(f"Failed to connect to CosmosDB: {e}")

# Google Calendar Configuration
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "service-account.json")

if not os.path.exists(SERVICE_ACCOUNT_FILE):
    raise FileNotFoundError("Missing service-account.json. Ensure it exists in the correct path.")

try:
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    calendar_service = build('calendar', 'v3', credentials=creds)
except Exception as e:
    raise RuntimeError(f"Failed to initialize Google Calendar API: {e}")

CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
if not CALENDAR_ID:
    raise ValueError("GOOGLE_CALENDAR_ID is missing. Set it in .env file.")

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
HOST_EMAIL = os.getenv("HOST_EMAIL")  # Email of the host (admin)

if not SMTP_SERVER or not EMAIL_USER or not EMAIL_PASS or not HOST_EMAIL:
    raise ValueError("Missing SMTP or Host Email credentials. Check your .env file.")

@pickadate_bp.route('/pickadate')
def pickadate():
    return render_template('pickadate/pickadate.html')

@pickadate_bp.route('/book', methods=['POST'])
def book():
    try:
        guest_name = request.form.get('guestName')
        email = request.form.get('email')
        phone = request.form.get('phone')
        social_media = request.form.get('socialMedia')
        podcast_name = request.form.get('podcastName')
        preferred_time = request.form.get('preferredTime')
        meeting_preferences = request.form.get('meetingPreferences')
        file_url = None

        if 'upload' in request.files:
            file = request.files['upload']
            if file.filename:
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                filepath = os.path.join('uploads/', filename)
                file.save(filepath)
                file_url = filepath

        booking_id = str(uuid.uuid4())
        item = {
            'id': booking_id,
            'guestName': guest_name,
            'email': email,
            'phone': phone,
            'socialMedia': social_media,
            'podcastName': podcast_name,
            'preferredTime': preferred_time,
            'meetingPreferences': meeting_preferences,
            'fileUrl': file_url,
            'createdAt': datetime.utcnow().isoformat()
        }

        container.create_item(body=item)

        # Debugging - Print logs
        print(f"📩 Sending email to Guest: {email}")
        print(f"📩 Sending email to Host: {HOST_EMAIL}")

        # Send email confirmation to Guest & Host
        send_booking_email(email, guest_name, preferred_time)
        send_host_notification(HOST_EMAIL, guest_name, email, preferred_time)

        return jsonify({'message': 'Booking Successful', 'bookingId': booking_id}), 201
    except Exception as e:
        print(f"🚨 Error in book(): {e}")
        return jsonify({'message': 'Internal Server Error', 'error': str(e)}), 500

@pickadate_bp.route('/bookings', methods=['GET'])
def get_bookings():
    try:
        bookings = list(container.read_all_items())
        return jsonify(bookings), 200
    except Exception as e:
        return jsonify({'message': 'Internal Server Error', 'error': str(e)}), 500

@pickadate_bp.route('/available-slots', methods=['GET'])
def get_available_slots():
    try:
        now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = calendar_service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        available_slots = []
        for event in events:
            start_time = event['start'].get('dateTime', event['start'].get('date'))
            end_time = event['end'].get('dateTime', event['end'].get('date'))
            available_slots.append({"start": start_time, "end": end_time})

        return jsonify(available_slots), 200
    except Exception as e:
        return jsonify({'message': 'Error fetching available slots', 'error': str(e)}), 500

def send_booking_email(to_email, guest_name, preferred_time):
    subject = "📅 Podcast Booking Confirmation"
    message = f"""
    Hello {guest_name},

    Your podcast booking for {preferred_time} has been confirmed.

    Thank you!
    """

    print(f"📨 Sending email to guest: {to_email}")  # Debugging
    send_email(to_email, subject, message)

def send_host_notification(to_email, guest_name, guest_email, preferred_time):
    subject = "🔔 New Podcast Booking Received"
    message = f"""
    Hello,

    A new podcast booking has been made:

    - Guest: {guest_name}
    - Email: {guest_email}
    - Time Slot: {preferred_time}

    Please check the booking system for more details.
    """

    print(f"📨 Sending email to host: {to_email}")  # Debugging
    send_email(to_email, subject, message)

def send_email(to_email, subject, message):
    try:
        msg = f"Subject: {subject}\n\n{message}"
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg)
        print(f"✅ Email sent successfully to {to_email}")
    except Exception as e:
        print(f"🚨 Email sending error: {e}")
