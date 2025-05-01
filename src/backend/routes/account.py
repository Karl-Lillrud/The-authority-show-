from flask import Blueprint, request, jsonify, g, render_template, session
# Import AuthService instead of AccountService
from backend.services.authService import AuthService
import logging

# Define Blueprint
account_bp = Blueprint("account_bp", __name__, url_prefix="/api/account")

# Instantiate the Auth Service
auth_service = AuthService()

# Configure logger
logger = logging.getLogger(__name__)

# Middleware to populate g.email
@account_bp.before_request
def populate_user_context():
    if not hasattr(g, "email"):
        g.email = session.get("email")


@account_bp.route("", methods=["GET"])
def get_account():
 
    user_id = getattr(g, "user_id", None)
    if not user_id:
        logger.warning("Unauthorized attempt to get account info.")
        return jsonify({"error": "Unauthorized"}), 401

    try:
        response, status_code = auth_service.get_account_by_user(user_id)
        logger.info(f"--- Responding to GET /api/account for user {user_id} with status {status_code} ---")
        return jsonify(response), status_code
    except Exception as e:
        logger.error(f"Error fetching account for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@account_bp.route("", methods=["PUT"])
def edit_account():

    user_id = getattr(g, "user_id", None)
    if not user_id:
        logger.warning("Unauthorized attempt to edit account.")
        return jsonify({"error": "Unauthorized"}), 401

    if not request.is_json:
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        response, status_code = auth_service.edit_account(user_id, data)
        return jsonify(response), status_code
    except Exception as e:
        logger.error(f"Error updating account for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@account_bp.route("", methods=["DELETE"])
def delete_account():

    user_id = getattr(g, "user_id", None)
    if not user_id:
        logger.warning("Unauthorized attempt to delete account.")
        return jsonify({"error": "Unauthorized"}), 401

    try:
        response, status_code = auth_service.delete_account(user_id)
        if status_code == 200:
            session.clear()  # Clear session on successful deletion
            response_obj = jsonify(response)
            response_obj.delete_cookie("remember_me")  # Clear remember me cookie
            return response_obj, status_code
        return jsonify(response), status_code
    except Exception as e:
        logger.error(f"Error deleting account for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@account_bp.route("/profile-picture", methods=["POST"])
def upload_profile_picture():
    user_id = getattr(g, "user_id", None)
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if 'profilePic' not in request.files:
        return jsonify({"error": "No profile picture file provided"}), 400

    file = request.files['profilePic']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        response, status_code = auth_service.upload_profile_picture(user_id, file)
        return jsonify(response), status_code
    except Exception as e:
        logger.error(f"Error uploading profile picture for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": f"Internal server error during upload: {str(e)}"}), 500


@account_bp.route("/billing", methods=["GET"])
def buy_credits():
    user_id = request.args.get("user_id")
    return render_template("billing/billing.html", user_id=user_id)
