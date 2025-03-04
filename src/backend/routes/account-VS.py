from flask import Blueprint, request, jsonify, url_for
from datetime import datetime
import uuid
from backend.database.mongo_connection import collection
from marshmallow import ValidationError
from backend.models.accounts import AccountSchema  # Make sure to import the schema
from backend.services.accountsService import (
    create_account,
)  # Import the create_account function from the service
from backend.models.accounts import AccountSchema
from werkzeug.security import check_password_hash
from bson import ObjectId

# Define Blueprint
account_bp = Blueprint("account_bp", __name__)


@account_bp.route("/create_account", methods=["POST"])
def create_account_route():
    try:
        data = request.get_json()
        response, status_code = create_account(data)
        return jsonify(response), status_code

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Error creating account: {str(e)}"}), 500


@account_bp.route("/get_account/<account_id>", methods=["GET"])
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
    """

    try:
        data = request.get_json() or {}
        input_email = data.get("deleteEmail")
        input_password = data.get("deletePassword")
        delete_confirm = data.get("deleteConfirm", "").strip().upper()

        if delete_confirm != "DELETE":
            return jsonify({"error": "Please type 'DELETE' exactly to confirm account deletion."}), 400

        if not input_email or not input_password:
            return jsonify({"error": "Email and password are required."}), 400

        # Retrieve the user document by email (case-insensitive search)
        user = collection.database.Users.find_one({
            "email": {"$regex": f"^{input_email}$", "$options": "i"}
        })
        if not user:
            return jsonify({"error": "User does not exist in the database."}), 404

        # Verify the provided password using Werkzeug's check_password_hash
        stored_hash = user.get("passwordHash")
        if not stored_hash:
            return jsonify({"error": "User record is missing password hash."}), 500

        if not check_password_hash(stored_hash, input_password):
            return jsonify({"error": "Incorrect password."}), 400

        # Ensure the user's identifier exists
        user_id_field = user.get("_id")
        if user_id_field is None:
            return jsonify({"error": "User identifier missing from record."}), 500

        # Attempt conversion to ObjectId if needed
        try:
            if not isinstance(user_id_field, ObjectId):
                user_object_id = ObjectId(user_id_field)
            else:
                user_object_id = user_id_field
        except Exception:
            user_object_id = user_id_field  # Fallback

        # Delete associated data from UsersToTeams and Teams collections
        collection.database.UsersToTeams.delete_many({
            "$or": [{"userId": user_object_id}, {"userId": user.get("id")}]
        })

        collection.database.Teams.delete_many({
            "$or": [{"UserID": user_object_id}, {"UserID": user.get("id")}]
        })

        # Delete the user document from the Users collection
        user_result = collection.database.Users.delete_one({
            "$or": [{"_id": user_object_id}, {"id": user.get("id")}]
        })
        if user_result.deleted_count == 0:
            return jsonify({"error": "User deletion failed."}), 500

        return jsonify({
            "message": "User account and associated data deleted successfully.",
            "redirect": url_for("signin_bp.signin")
        }), 200

    except Exception as e:
        return jsonify({"error": f"Error during deletion: {str(e)}"}), 500