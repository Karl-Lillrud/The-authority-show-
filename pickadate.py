import os
import smtplib
import uuid
from flask import Blueprint, request, jsonify, render_template
from azure.cosmos import CosmosClient, PartitionKey
from werkzeug.utils import secure_filename
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Flask Blueprint
pickadate_bp = Blueprint('pickadate_bp', __name__)

# Cosmos DB Configuration
COSMOS_ENDPOINT = os.getenv('COSMOS_ENDPOINT')
COSMOS_KEY = os.getenv('COSMOS_KEY')
DATABASE_NAME = 'podmanagedb'
CONTAINER_NAME = 'bookings'

client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = client.create_database_if_not_exists(DATABASE_NAME)
container = database.create_container_if_not_exists(id=CONTAINER_NAME, partition_key=PartitionKey(path='/email'))

# Google Calendar Configuration
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_FILE = "service-account.json"  # Ensure this file is configured correctly

creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
calendar_service = build('calendar', 'v3', credentials=creds)

CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")

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
            if file.filename != '':
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
            'createdAt': str(uuid.uuid1())
        }

        container.create_item(body=item)
        return jsonify({'message': 'Booking Successful', 'bookingId': booking_id}), 201
    except Exception as e:
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
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
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

def send_booking_email(to_email, guest_name, preferred_time):
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")

    subject = "Podcast Booking Confirmation"
    message = f"Hello {guest_name},\n\nYour podcast booking for {preferred_time} has been confirmed.\n\nThank you!"

    try:
        msg = f"Subject: {subject}\n\n{message}"
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg)
    except Exception as e:
        print(f"Error sending email: {e}")
