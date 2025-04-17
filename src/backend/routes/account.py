from flask import Blueprint, request, jsonify, g, render_template, session
from backend.models.accounts import AccountSchema
import logging
from backend.repository.account_repository import AccountRepository
import uuid
from datetime import datetime
from backend.database.mongo_connection import collection  # Add this import
from bson import ObjectId  # Import ObjectId for type checking

# Define Blueprint
account_bp = Blueprint("account_bp", __name__)

# Instantiate the Account Repository
account_repo = AccountRepository()

# Configure logger
logger = logging.getLogger(__name__)

# Middleware to populate g.email
@account_bp.before_request
def populate_user_context():
    if not hasattr(g, "email"):
        g.email = session.get("email")  # Retrieve email from session if available

# SHOULD ONLY BE USED FOR SPECIFIC DATA CRUD OPERATIONS
# EXTRA FUNCTIONALITY BESIDES CRUD OPERATIONS SHOULD BE IN SERVICES

@account_bp.route("/create_account", methods=["POST"])
def create_account_route():
    try:
        data = request.get_json()
        email = data["email"]

        # Kontrollera om ett konto redan finns för e-postadressen
        existing_account = collection.database.Accounts.find_one({"email": email})
        if (existing_account):
            logger.warning(f"Account already exists for email {email}.")
            return jsonify({"error": "Account already exists for this email."}), 400

        account_data = {
            "id": str(uuid.uuid4()),
            "userId": data.get("userId"),  # Replace ownerId with userId
            "subscriptionId": str(uuid.uuid4()),
            "creditId": str(uuid.uuid4()),
            "email": data["email"],
            "isCompany": data.get("isCompany", False),
            "companyName": data.get("companyName", ""),
            "paymentInfo": data.get("paymentInfo", ""),
            "subscriptionStatus": "active",
            "createdAt": datetime.utcnow(),
            "referralBonus": 0,
            "subscriptionStart": datetime.utcnow(),
            "subscriptionEnd": None,
            "isActive": True,
            "created_at": datetime.utcnow(),
            "isFirstLogin": True,
        }
        response, status_code = account_repo.create_account(account_data)
        return jsonify(response), status_code
    except Exception as e:
        logger.error(f"Error creating account: {e}", exc_info=True)
        return jsonify({"error": f"Error creating account: {str(e)}"}), 500

@account_bp.route("/get_account", methods=["GET"])
def get_account_route():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Fetch user data from the Users collection
    user = collection.database.Users.find_one({"_id": g.user_id})
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Convert ObjectId fields to strings
    user = {key: str(value) if isinstance(value, ObjectId) else value for key, value in user.items()}

    return jsonify(user), 200

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

@account_bp.route("/billing", methods=["GET"])
def buy_credits():
    user_id = request.args.get("user_id")  # ✅ extract it from query
    return render_template("billing/billing.html", user_id=user_id)
