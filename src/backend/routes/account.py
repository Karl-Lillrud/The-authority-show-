from flask import Blueprint, request, jsonify
from backend.services.account_service import create_account as create_account_service
from marshmallow import ValidationError
from backend.models.accounts import AccountSchema  # Make sure to import the schema
import logging

# Define Blueprint
account_bp = Blueprint("account_bp", __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@account_bp.route("/create_accounts", methods=["POST"])
def create_account():
    try:
        data = request.get_json()

        if not data:
            raise ValueError("No data received or invalid JSON.")

        # Check for required fields
        if "userId" not in data or "email" not in data:
            raise ValueError("Missing required fields: userId and email")

        # Call the service function to create the account
        result = create_account_service(data)

        if result["success"]:
            response = {
                "message": "Account created successfully",
                "accountId": result["accountId"],
            }
            logger.info("Account created successfully: %s", response)
            return jsonify(response), 201
        else:
            raise Exception(result["details"])

    except ValueError as ve:
        logger.error("ValueError: %s", ve)
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error("Error: %s", e, exc_info=True)
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
