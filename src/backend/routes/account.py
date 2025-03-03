from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
from backend.database.mongo_connection import collection
from marshmallow import ValidationError
from backend.database.mongo_connection import collection
from backend.models.accounts import AccountSchema  # Make sure to import the schema
from backend.services.accountsService import (
    create_account,
)  # Import the create_account function from the service

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
