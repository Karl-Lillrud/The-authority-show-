from flask import Blueprint, request, jsonify, redirect, session, current_app, url_for
import logging
from backend.services.authService import AuthService

# ... other imports ...

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")  # Or use existing blueprint
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
    result, status_code = auth_service.activate_user_via_token(token)

    # This endpoint now returns JSON, the frontend handles the redirect
    return jsonify(result), status_code


@auth_bp.route("/activate", methods=["GET"])
def activate_user():
    """Activate user via token."""
    token = request.args.get("token")
    if not token:
        return jsonify({"error": "Missing activation token"}), 400

    result, status_code = auth_service.activate_user_via_token(token)
    return jsonify(result), status_code


# ... rest of the routes ...
