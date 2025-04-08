from flask import Blueprint, request, jsonify, g
from backend.models.accounts import AccountSchema
import logging
from backend.repository.account_repository import AccountRepository

# Define Blueprint
account_bp = Blueprint("account_bp", __name__)

# Instantiate the Account Repository
account_repo = AccountRepository()

# Configure logger
logger = logging.getLogger(__name__)

# SHOULD ONLY BE USED FOR SPECIFIC DATA CRUD OPERATIONS
# EXTRA FUNCTIONALITY BESIDES CRUD OPERATIONS SHOULD BE IN SERVICES

@account_bp.route("/create_account", methods=["POST"])
def create_account_route():
    try:
        data = request.get_json()
        response, status_code = account_repo.create_account(data)  # ✅ Use account_repo instance
        return jsonify(response), status_code
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Error creating account: {str(e)}"}), 500

@account_bp.route("/get_account", methods=["GET"])
def get_account_route():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    response, status_code = account_repo.get_account_by_user(str(g.user_id))
    return jsonify(response), status_code

# Route to update user profile data
@account_bp.route("/edit_account", methods=["PUT"])
def edit_account():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        response, status_code = account_repo.edit_account(str(g.user_id), data)
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to edit account: {str(e)}"}), 500
