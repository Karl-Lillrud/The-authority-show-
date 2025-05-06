from flask import Blueprint, request, jsonify, render_template, session, current_app
from backend.utils.email_utils import send_lia_inquiry_email
import logging

# Ensure the blueprint name matches what's expected in app.py
lia_bp = Blueprint("lia_bp", __name__, template_folder='../../frontend/templates/lia')
logger = logging.getLogger(__name__)

@lia_bp.route("/")
def lia_page():
    """
    Serves the LIA page.
    """
    user_id = session.get("user_id")
    if not user_id:
        current_app.logger.info("LIA page accessed by unauthenticated user.")
    # else:
    # current_app.logger.info(f"LIA page accessed by user {user_id}.")
    return render_template("lia.html")


@lia_bp.route("/submit-inquiry", methods=["POST"])
def submit_lia_inquiry():
    """
    Handles the LIA form submission, sends an email, and returns a response.
    """
    try:
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        school_and_study = data.get("schoolAndStudy") # Matches JS key

        if not all([name, email, phone, school_and_study]):
            logger.warning("LIA inquiry submission missing required fields.")
            return jsonify({"success": False, "error": "Missing required fields."}), 400

        logger.info(f"Received LIA inquiry: Name: {name}, Email: {email}, Phone: {phone}, School/Study: {school_and_study}")

        email_result = send_lia_inquiry_email(name, email, phone, school_and_study)

        if email_result.get("success"):
            logger.info("LIA inquiry email sent successfully.")
            return jsonify({"success": True, "message": "Inquiry submitted and email sent."}), 200
        else:
            logger.error(f"Failed to send LIA inquiry email: {email_result.get('error')}")
            return jsonify({"success": False, "error": "Failed to send inquiry email."}), 500

    except Exception as e:
        logger.error(f"Error processing LIA inquiry: {e}", exc_info=True)
        return jsonify({"success": False, "error": "An internal error occurred."}), 500
