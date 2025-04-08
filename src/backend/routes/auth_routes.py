from flask import Blueprint, request, jsonify
from utils.email_utils import send_verification_code_email
import random

auth_routes = Blueprint("auth_routes", __name__)

@auth_routes.route("/api/send-verification-code", methods=["POST"])
def send_verification_code():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"success": False, "error": "Email is required."}), 400

    # Generate a random 6-digit verification code
    verification_code = str(random.randint(100000, 999999))

    # Call the send_verification_code_email function
    result = send_verification_code_email(email, verification_code)

    if result.get("success"):
        return jsonify({"success": True}), 200
    else:
        return jsonify({"success": False, "error": result.get("error")}), 500
