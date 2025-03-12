from flask import Blueprint, request, jsonify, g
from backend.utils.email_utils import send_email
from backend.database.mongo_connection import collection
from datetime import datetime, timezone

email_bp = Blueprint('email_bp', __name__)

@email_bp.route('/send_pitch_email', methods=['POST'])
def send_pitch_email():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    guest_id = data.get('guest_id')
    guest_email = data.get('guest_email')
    guest_name = data.get('guest_name')

    if not guest_id or not guest_email or not guest_name:
        return jsonify({"error": "Missing required fields"}), 400

    # Send the pitch email
    subject = "Invitation to Join Our Podcast"
    body = f"Hi {guest_name},\n\nWe would love to have you as a guest on our podcast. Please let us know if you're interested.\n\nBest regards,\nThe Podcast Team"
    send_email(guest_email, subject, body)

    # Store email status in the database
    email_status = {
        "guest_id": guest_id,
        "email": guest_email,
        "status": "sent",
        "sent_at": datetime.now(timezone.utc),
        "response_rate": 0  # Initial response rate
    }
    collection.database.EmailStatus.insert_one(email_status)

    return jsonify({"message": "Pitch email sent successfully"}), 200