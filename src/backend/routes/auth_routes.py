from flask import Blueprint, request, jsonify, redirect, session, current_app, url_for
import logging
from backend.services.authService import AuthService
from backend.database.mongo_connection import collection
from backend.services.rss_Service import RSSService
import uuid
from datetime import datetime

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")  # Defines the blueprint
auth_service = AuthService()
logger = logging.getLogger(__name__)

# ... existing routes like /signin, /verify-otp ...


@auth_bp.route("/verify-token/<token>", methods=["GET"])
def verify_token_route(token):
    """Endpoint called by the link in the standard login email."""
    logger.info(
        f"Received token verification request for token: {token[:10]}..."
    )  # Log safely
    result, status_code = auth_service.verify_login_token(token)
    if status_code == 200:
        # Redirect based on the result from the service
        redirect_url = result.get(
            "redirect_url", url_for("views.podprofile")
        )  # Default redirect
        logger.info(f"Token verified, redirecting to {redirect_url}")
        # Maybe add accountId to session or return it if needed by frontend after redirect?
        # session['accountId'] = result.get('accountId')
        return redirect(redirect_url)
    else:
        # Handle error - maybe redirect to a login page with an error message
        error_message = result.get("error", "An unknown error occurred.")
        logger.error(f"Token verification failed: {error_message}")
        # You might want a dedicated error page or flash message
        return jsonify({"error": error_message}), status_code


# --- New Activation Route ---
@auth_bp.route("/activate-user", methods=["POST"])  # Changed to POST for API call
def activate_user_route():
    """API Endpoint called by the frontend after user clicks activation link."""
    data = request.get_json()
    token = data.get("token")
    if not token:
        logger.warning("Activation API called without token.")
        return jsonify({"error": "Missing activation token"}), 400

    logger.info(f"Received activation request via API for token: {token[:10]}...")
    result, status_code = auth_service.process_activation_token(token)

    # This endpoint now returns JSON, the frontend handles the redirect
    return jsonify(result), status_code


@auth_bp.route("/activate", methods=["GET"])
def activate_account_route():  # This is the route hit by the activation email link
    token = request.args.get("token")
    logger.info(f"Received activation request for token: {token}")
    if not token:
        logger.warn("Activation attempt with no token.")
        # Redirect to a user-friendly error page or the sign-in page with an error message
        return redirect(url_for("auth_bp.signin_page", error="Activation token is missing or invalid."))

    try:
        # Delegate the entire token processing to AuthService.process_activation_token
        # This service method handles user creation, account creation, session setup,
        # RSS parsing, podcast creation (with correct accountId and isImported=True),
        # and determines the appropriate redirect URL.
        response_data, status_code = auth_service.process_activation_token(token)

        if status_code == 200:
            # AuthService.process_activation_token should have set up the session.
            # It returns a redirect_url (e.g., /podcastmanagement or /podprofile if RSS fetch failed).
            redirect_url = response_data.get("redirect_url", url_for("podprofile_bp.podprofile"))  # Default if not specified
            logger.info(f"Account activation processed. User ID: {session.get('user_id')}. Redirecting to {redirect_url}")
            return redirect(redirect_url)
        else:
            # Activation failed (e.g., token expired, RSS fetch failed, podcast creation failed within the service)
            error_message = response_data.get("error", "Activation failed. Please try again or contact support.")
            logger.error(f"Activation failed. Status: {status_code}, Response: {response_data}")
            # Redirect to a page that can display the error or to signin with an error query param
            return redirect(url_for("auth_bp.signin_page", error=error_message))

    except Exception as e:
        logger.error(f"Critical exception during account activation process for token {token}: {str(e)}", exc_info=True)
        # Redirect to a generic error page or signin
        return redirect(url_for("auth_bp.signin_page", error="An unexpected error occurred during activation. Please try again."))


# ... rest of the routes ...
