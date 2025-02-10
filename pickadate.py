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
from azure.storage.blob import BlobServiceClient
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

# Azure Blob Storage Configuration
AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME")

if not AZURE_STORAGE_ACCOUNT_NAME or not AZURE_STORAGE_ACCOUNT_KEY or not AZURE_STORAGE_CONTAINER_NAME:
    raise ValueError("Missing Azure Storage credentials. Check your .env file.")

# Initialize Blob Service Client
blob_service_client = BlobServiceClient(
    f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
    credential=AZURE_STORAGE_ACCOUNT_KEY
)
blob_container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER_NAME)

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
        print("Received Form Data:")
        print(request.form)  # Print the raw form data

        guest_name = request.form.get('guestName')
        email = request.form.get('email')
        preferred_time = request.form.get('preferredTime')
        file_url = request.form.get('fileUrl')  # Get uploaded file URL from frontend

        print(f"Guest Name: {guest_name}")
        print(f"Email: {email}")
        print(f"Preferred Time: {preferred_time}")
        print(f"File URL: {file_url}")  # This should NOT be None

        if not guest_name or not email or not preferred_time:
            print("Missing required fields!")
            return jsonify({'message': 'Missing required fields'}), 400

        if not file_url:
            print(" No file URL received! Make sure the upload is successful before submitting.")
            return jsonify({'message': 'File upload required'}), 400

        booking_id = str(uuid.uuid4())
        item = {
            'id': booking_id,
            'guestName': guest_name,
            'email': email,
            'preferredTime': preferred_time,
            'fileUrl': file_url,  # Store uploaded file URL in CosmosDB
            'createdAt': datetime.utcnow().isoformat()
        }

        print(f"Saving to CosmosDB: {item}")

        try:
            container.create_item(body=item)
            print(f"✅ Successfully saved booking {booking_id}")
        except Exception as db_error:
            print(f"CosmosDB Save Error: {db_error}")
            return jsonify({'message': 'Database error', 'error': str(db_error)}), 500

        # Send confirmation emails
        send_booking_email(email, guest_name, preferred_time)
        send_host_notification(HOST_EMAIL, guest_name, email, preferred_time)

        return jsonify({'message': 'Booking Successful', 'bookingId': booking_id}), 201

    except Exception as e:
        print(f"Unexpected Error in `book()`: {e}")
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
    subject = "Podcast Booking Confirmation"
    message = f"""
    Hello {guest_name},

    Your podcast booking for {preferred_time} has been confirmed.

    Thank you!
    """

    send_email(to_email, subject, message)

@pickadate_bp.route('/upload-file', methods=['POST'])
def upload_file():
    """Handles file upload to Azure Blob Storage."""
    if 'file' not in request.files:
        print(" No file found in request!")
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        print(" No file selected!")
        return jsonify({'error': 'No file selected'}), 400

    file_url = upload_to_azure(file)
    if file_url:
        print(f" File successfully uploaded: {file_url}")
        return jsonify({'fileUrl': file_url}), 200
    else:
        print("Upload failed!")
        return jsonify({'error': 'Upload failed'}), 500



def upload_to_azure(file):
    """Uploads file to Azure Blob Storage and returns the file URL"""
    try:
        if file.filename == "":
            print("No file selected for upload!")
            return None

        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        blob_client = blob_container_client.get_blob_client(filename)

        print(f"⬆ Attempting to upload {filename} to Azure Blob Storage...")

        # Read file content to ensure it's being sent
        file_data = file.read()
        if not file_data:
            print("File data is empty! The file may not have been read properly.")
            return None

        # Reset file pointer (important for re-uploading the same file)
        file.seek(0)

        # Upload the file
        blob_client.upload_blob(file, overwrite=True)

        file_url = f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_STORAGE_CONTAINER_NAME}/{filename}"
        print(f"Upload Successful! File URL: {file_url}")
        return file_url
    except Exception as e:
        print(f"Azure Blob Storage Upload Error: {e}")
        return None


def send_host_notification(to_email, guest_name, guest_email, preferred_time):
    subject = "New Podcast Booking Received"
    message = f"""
    Hello,

    A new podcast booking has been made:

    - Guest: {guest_name}
    - Email: {guest_email}
    - Time Slot: {preferred_time}

    Please check the booking system for more details.
    """

    send_email(to_email, subject, message)

def send_email(to_email, subject, message):
    try:
        print(f"Attempting to send email to {to_email}...")
        msg = f"Subject: {subject}\n\n{message}"
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg)
        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Email sending error: {e}")
