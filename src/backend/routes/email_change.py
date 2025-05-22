from flask import Blueprint, request, jsonify, session, redirect, url_for
from backend.services.email_change_service import EmailChangeService
import logging

logger = logging.getLogger(__name__)
email_change_bp = Blueprint("email_change_bp", __name__)
email_change_service = EmailChangeService()

@email_change_bp.route("/api/email/change", methods=["POST"])
def initiate_email_change():
    """Initiate email change process."""
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        data = request.get_json()
        new_email = data.get("newEmail")
        if not new_email:
            return jsonify({"error": "New email is required"}), 400

        user_id = session["user_id"]
        current_email = session["email"]

        result, status_code = email_change_service.initiate_email_change(
            user_id, current_email, new_email
        )
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Error initiating email change: {e}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@email_change_bp.route("/email/confirm/<token>", methods=["GET"])
def confirm_email_change(token):
    """Confirm email change with token."""
    try:
        logger.info(f"Processing email confirmation with token: {token}")
        result, status_code = email_change_service.confirm_email_change(token)
        logger.info(f"Email confirmation result: {result}, status: {status_code}")
        
        if status_code == 200:
            # Clear any existing session since email is changed
            session.clear()
            if result.get("redirect_url"):
                return redirect(result["redirect_url"])
            return redirect(url_for("auth_bp.signin_page"))
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Error confirming email change: {e}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500 