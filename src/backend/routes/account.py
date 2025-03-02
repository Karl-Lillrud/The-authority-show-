import logging
import uuid
from datetime import datetime
from bson import ObjectId
from flask import Blueprint, request, jsonify, url_for
from marshmallow import ValidationError
from backend.database.mongo_connection import collection
from backend.models.accounts import AccountSchema
from backend.models.users import UserSchema
from werkzeug.security import check_password_hash

# Initialize logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Define Blueprint
account_bp = Blueprint("account_bp", __name__)

@account_bp.route("/create_accounts", methods=["POST"])
def create_account():
    try:
        data = request.get_json()

        if not data:
            raise ValueError("No data received or invalid JSON.")

        # Check for required fields
        if "userId" not in data or "email" not in data:
            raise ValueError("Missing required fields: userId and email")

        user_id = data["userId"]
        email = data["email"]
        company_name = data.get("companyName", "")
        is_company = data.get("isCompany", False)

        subscription_id = str(uuid.uuid4())  # Generate unique subscription ID
        account_id = str(uuid.uuid4())  # Generate unique account ID

        # Create account document
        account_document = {
            "_id": account_id,  # Explicitly set '_id' to string UUID
            "userId": user_id,
            "subscriptionId": subscription_id,
            "email": email,
            "isCompany": is_company,
            "companyName": company_name,
            "paymentInfo": "",  # Placeholder for payment info
            "subscriptionStatus": "active",
            "createdAt": datetime.utcnow().isoformat(),
            "referralBonus": 0,
            "subscriptionStart": datetime.utcnow().isoformat(),
            "subscriptionEnd": "",
            "isActive": True,
        }

        # Insert account into the Accounts collection (with custom _id)
        print("🔍 Inserting account into the database:", account_document)
        collection.database.Accounts.insert_one(account_document)

        # Return success response
        response = {
            "message": "Account created successfully",
            "accountId": account_document["_id"],
        }
        print("✅ Account created successfully:", response)
        return jsonify(response), 201

    except ValueError as ve:
        print(f"❌ ValueError: {ve}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": f"Error creating account: {str(e)}"}), 500


@account_bp.route("/get_accounts/<account_id>", methods=["GET"])
def get_account(account_id):
    try:
        # Fetch account from the database using account_id
        account = collection.database.Accounts.find_one({"id": account_id})

        if not account:
            return jsonify({"error": "Account not found"}), 404

        # Serialize the account using AccountSchema
        schema = AccountSchema()
        result = schema.dump(account)  # This will serialize the account data

        return jsonify({"account": result}), 200

    except ValidationError as ve:
        # If there are validation errors
        return jsonify({"error": "Validation error", "details": ve.messages}), 400

    except Exception as e:
        # Generic error handling
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch account: {str(e)}"}), 500


@account_bp.route("/delete_user", methods=["DELETE"])
def delete_user():
    """
    DELETE endpoint to remove a user and associated data from:
      - UsersToTeams (join collection)
      - Teams (where UserID equals the user's id)
      - Users collection
    Expects a JSON payload with:
      - deleteEmail: The user's email.
      - deletePassword: The user's password (plain-text; it will be verified against the stored hash).
      - deleteConfirm: Must equal "DELETE" (case-insensitive).
    """
    try:
        data = request.get_json() or {}
        input_email = data.get("deleteEmail")
        input_password = data.get("deletePassword")
        delete_confirm = data.get("deleteConfirm", "").strip().upper()

        logger.debug("Received deletion request for email: %s", input_email)

        if delete_confirm != "DELETE":
            logger.debug("Delete confirmation not correct: %s", delete_confirm)
            return jsonify({"error": "Please type 'DELETE' exactly to confirm account deletion."}), 400

        if not input_email or not input_password:
            logger.debug("Missing email or password in request.")
            return jsonify({"error": "Email and password are required."}), 400

        # Retrieve the user document by email (case-insensitive search)
        user = collection.database.Users.find_one({
            "email": {"$regex": f"^{input_email}$", "$options": "i"}
        })
        if not user:
            logger.debug("No user found for email: %s", input_email)
            return jsonify({"error": "User does not exist in the database."}), 404

        # Verify the provided password using Werkzeug's check_password_hash
        stored_hash = user.get("passwordHash")
        if not stored_hash:
            logger.error("User record for %s does not have a password hash.", input_email)
            return jsonify({"error": "User record is missing password hash."}), 500

        if not check_password_hash(stored_hash, input_password):
            logger.debug("Incorrect password provided for user %s", input_email)
            return jsonify({"error": "Incorrect password."}), 400

        # Ensure the user's identifier exists
        user_id_field = user.get("_id")
        if user_id_field is None:
            logger.error("User document missing '_id' field for email %s", input_email)
            return jsonify({"error": "User identifier missing from record."}), 500

        # Attempt conversion to ObjectId if needed
        try:
            if not isinstance(user_id_field, ObjectId):
                user_object_id = ObjectId(user_id_field)
            else:
                user_object_id = user_id_field
        except Exception as conversion_error:
            logger.error("Error converting user _id to ObjectId for user %s: %s", input_email, conversion_error)
            user_object_id = user_id_field  # Fallback

        logger.debug("User identifier used for deletion: %s", user_object_id)

        # Delete associated data from UsersToTeams and Teams collections
        join_result = collection.database.UsersToTeams.delete_many({
            "$or": [{"userId": user_object_id}, {"userId": user.get("id")}]
        })
        logger.info("Deleted %s records from UsersToTeams for user %s", join_result.deleted_count, input_email)

        teams_result = collection.database.Teams.delete_many({
            "$or": [{"UserID": user_object_id}, {"UserID": user.get("id")}]
        })
        logger.info("Deleted %s records from Teams for user %s", teams_result.deleted_count, input_email)

        # Delete the user document from the Users collection
        user_result = collection.database.Users.delete_one({
            "$or": [{"_id": user_object_id}, {"id": user.get("id")}]
        })
        if user_result.deleted_count == 0:
            logger.error("User deletion failed for email %s", input_email)
            return jsonify({"error": "User deletion failed."}), 500

        logger.info("User %s and associated data deleted successfully.", input_email)
        return jsonify({
            "message": "User account and associated data deleted successfully.",
            "redirect": url_for("signin_bp.signin")
        }), 200

    except Exception as e:
        logger.error("Error during deletion: %s", e, exc_info=True)
        return jsonify({"error": f"Error during deletion: {str(e)}"}), 500