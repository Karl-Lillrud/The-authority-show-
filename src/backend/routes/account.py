from flask import Blueprint, request, jsonify
from backend.models.accounts import AccountSchema
from backend.repository.account_repository import AccountRepository

# Define Blueprint
account_bp = Blueprint("account_bp", __name__)

# Instantiate the Account Repository
account_repo = AccountRepository()

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

@account_bp.route("/get_account/<account_id>", methods=["GET"])
def get_account_route(account_id):
    try:
        response, status_code = account_repo.get_account(account_id)  # ✅ Use account_repo instance
        return jsonify(response), status_code
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch account: {str(e)}"}), 500
