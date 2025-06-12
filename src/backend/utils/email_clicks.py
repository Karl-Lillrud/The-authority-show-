from flask import Blueprint, request, jsonify, send_file # Added send_file
import datetime
import json
import os
import io 
import logging
import base64 # Added base64

try:
    from .blob_storage import upload_file_to_blob, get_blob_content
except ImportError:
    from blob_storage import upload_file_to_blob, get_blob_content


email_clicks_bp = Blueprint('email_clicks', __name__) 
logger = logging.getLogger(__name__) 

BLOB_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "podmanagerfiles") 
BLOB_FILE_PATH = "tracking/email_click_tracker.json" # As per user request

SENDER_EMAIL = "contact@podmanager.ai"

def load_tracked_data():
    """Loads tracked data from Azure Blob Storage."""
    logger.info(f"Attempting to load data from blob: {BLOB_CONTAINER_NAME}/{BLOB_FILE_PATH}")
    file_content_bytes = get_blob_content(BLOB_CONTAINER_NAME, BLOB_FILE_PATH)
    
    if file_content_bytes is None:
        logger.info(f"Blob '{BLOB_FILE_PATH}' not found or empty in container '{BLOB_CONTAINER_NAME}'. Returning empty list.")
        return []
    
    try:
        file_content_str = file_content_bytes.decode('utf-8')
        data = json.loads(file_content_str)
        if not isinstance(data, list):
            logger.warning("Data in blob is not a list. Returning empty list.")
            return []
        logger.info(f"Successfully loaded {len(data)} records from blob.")
        return data
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from blob: {BLOB_CONTAINER_NAME}/{BLOB_FILE_PATH}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading data from blob: {e}", exc_info=True)
        return []

def save_tracked_data(data):
    """Saves tracked data to Azure Blob Storage."""
    logger.info(f"Attempting to save {len(data)} records to blob: {BLOB_CONTAINER_NAME}/{BLOB_FILE_PATH}")
    try:
        json_data_str = json.dumps(data, indent=4)
        # Convert string to bytes and wrap in a BytesIO stream
        file_stream = io.BytesIO(json_data_str.encode('utf-8'))
        
        # Upload to blob storage
        blob_url = upload_file_to_blob(BLOB_CONTAINER_NAME, BLOB_FILE_PATH, file_stream, content_type='application/json')
        
        if blob_url:
            logger.info(f"Data successfully saved to blob: {blob_url}")
            return True
        else:
            logger.error("Failed to save data to blob. upload_file_to_blob returned None.")
            return False
    except Exception as e:
        logger.error(f"Error saving data to blob: {e}", exc_info=True)
        return False

@email_clicks_bp.route('/track_email_open', methods=['GET']) # Use the blueprint for routing
def track_email_open():
    """
    Tracks an email open event.
    Query Parameters:
        email_id (str): A unique identifier for the email that was opened.
        user_id (str): An identifier for the user who opened the email.
    """
    email_id = request.args.get('email_id')
    user_id = request.args.get('user_id')

    if not email_id or not user_id:
        logger.warning("track_email_open called with missing email_id or user_id.")
        return jsonify({"status": "error", "message": "Missing email_id or user_id"}), 400

    timestamp = datetime.datetime.now().isoformat()

    click_data = {
        "timestamp": timestamp,
        "email_id": email_id,
        "user_id": user_id,
        "sender_email": SENDER_EMAIL 
    }
    logger.info(f"Tracking email open: {click_data}")

    tracked_emails = load_tracked_data()
    tracked_emails.append(click_data)
    
    if save_tracked_data(tracked_emails):
        # For a tracking pixel, return a 1x1 transparent GIF image.
        pixel_gif_b64 = "R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=="
        pixel_gif_bytes = base64.b64decode(pixel_gif_b64)
        return send_file(io.BytesIO(pixel_gif_bytes), mimetype='image/gif')
        # return jsonify({"status": "success", "message": "Email open tracked"}), 200 # Old JSON response
    else:
        return jsonify({"status": "error", "message": "Failed to save tracking data"}), 500
