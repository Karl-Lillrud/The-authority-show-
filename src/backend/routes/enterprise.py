from flask import Blueprint, render_template, request, jsonify
from backend.utils.email_utils import send_enterprise_inquiry_email
import logging

logger = logging.getLogger(__name__)

enterprise_bp = Blueprint(
    "enterprise", __name__, template_folder="../../frontend/templates"
)

@enterprise_bp.route("")
def enterprise_page():
    """
    Renders the enterprise page.
    """
    return render_template("enterprise/enterprise.html")

@enterprise_bp.route("/submit-inquiry", methods=["POST"])
def submit_inquiry():
    """
    Handles the enterprise inquiry form submission.
    """
    try:
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")

        if not all([name, email, phone]):
            return jsonify({"success": False, "message": "Missing form data."}), 400

        result = send_enterprise_inquiry_email(name, email, phone)

        if result.get("success"):
            return jsonify({"success": True, "message": "Inquiry submitted successfully."}), 200
        else:
            logger.error(f"Failed to send enterprise inquiry email: {result.get('error')}")
            return jsonify({"success": False, "message": "Failed to submit inquiry. Please try again later."}), 500

    except Exception as e:
        logger.error(f"Error processing enterprise inquiry: {e}", exc_info=True)
        return jsonify({"success": False, "message": "An unexpected error occurred."}), 500
