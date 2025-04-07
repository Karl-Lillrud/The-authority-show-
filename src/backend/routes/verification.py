from flask import Blueprint, request, jsonify
from backend.utils.email_utils import send_email
import random

# Define Blueprint
verification_bp = Blueprint("verification_bp", __name__)

# In-memory store for verification codes (use a database in production)
verification_codes = {}

@verification_bp.route("/send-verification-code", methods=["POST"])
def send_verification_code():
    """
    Endpoint to send a verification code to the user's email
    """
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"success": False, "message": "Email is required"}), 400

    try:
        # Generate a 6-digit verification code
        verification_code = str(random.randint(100000, 999999))

        # Save the code in the in-memory store (replace with database logic)
        verification_codes[email] = verification_code

        # Send the verification code via email
        send_email(
            recipient=email,
            subject="Your Verification Code",
            body=f"Your verification code is: {verification_code}",
        )

        return jsonify({"success": True, "message": "Verification code sent successfully."})
    except Exception as e:
        print(f"Error sending verification code: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@verification_bp.route("/verify-code", methods=["POST"])
def verify_code():
    """
    Endpoint to verify the code entered by the user
    """
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    data = request.get_json()
    email = data.get("email")
    code = data.get("code")

    if not email or not code:
        return jsonify({"error": "Email and code are required"}), 400

    # Check if the code matches
    stored_code = verification_codes.get(email)
    if stored_code and stored_code == code:
        # Code is valid
        return jsonify({"success": True, "message": "Code verified successfully."})
    else:
        # Code is invalid
        return jsonify({"success": False, "message": "Invalid verification code."}), 400