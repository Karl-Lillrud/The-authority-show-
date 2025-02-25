from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
from database.mongo_connection import collection
from marshmallow import ValidationError
from Entities.accounts import AccountSchema  # Make sure to import the schema

# Define Blueprint
account_bp = Blueprint("account_bp", __name__)


@account_bp.route("/create_account", methods=["POST"])
def create_account():
    try:
        data = request.get_json()
        print("📩 Received Data for account creation:", data)

        user_id = data[
            "userId"
        ]  # This would be the userId from the registration process
        subscription_id = str(uuid.uuid4())  # Generate a unique subscription ID
        email = data["email"]
        company_name = data.get("companyName", "")
        is_company = data.get("isCompany", False)

        # Generate unique account ID (string UUID)
        account_id = str(uuid.uuid4())

        # Create the account document (set '_id' to string UUID)
        account_document = {
            "_id": account_id,  # Explicitly set '_id' to string UUID
            "ownerId": user_id,  # Associate with the user ID
            "subscriptionId": subscription_id,
            "email": email,
            "isCompany": is_company,
            "companyName": company_name,
            "paymentInfo": "",  # This would be set once payment info is available
            "subscriptionStatus": "active",
            "createdAt": datetime.utcnow().isoformat(),
            "referralBonus": 0,
            "subscriptionStart": datetime.utcnow().isoformat(),
            "subscriptionEnd": "",
            "isActive": True,
        }

        # Insert account into the Accounts collection (with custom _id)
        print("📝 Inserting account into database:", account_document)
        collection.database.Accounts.insert_one(account_document)

        return (
            jsonify(
                {
                    "message": "Account created successfully",
                    "accountId": account_document["_id"],
                }
            ),
            201,
        )

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
