import uuid
from datetime import datetime
from backend.database.mongo_connection import collection
from backend.models.accounts import AccountSchema
from backend.services.creditService import initialize_credits
import logging

logger = logging.getLogger(__name__)


class AccountRepository:
    def __init__(self):
        self.collection = collection.database.Accounts

    def create_account(self, data):
        try:
            if not data:
                raise ValueError("No data received or invalid JSON.")

            # Check for required fields (ownerId instead of userId)
            if "ownerId" not in data or "email" not in data:
                raise ValueError("Missing required fields: ownerId and email")

            # Check for existing account by email or ownerId
            existing_account = self.collection.find_one(
                {"$or": [{"email": data["email"]}, {"ownerId": data["ownerId"]}]}
            )
            if existing_account:
                raise ValueError("Account already exists for this email or owner.")

            # Use string _id instead of ObjectId
            account_id = str(uuid.uuid4())
            account_document = {
                "_id": account_id,
                "ownerId": data["ownerId"],  # Ensure ownerId is set
                "userId": data.get("userId"),  # Keep if needed for other relations
                "email": data["email"],
                "subscriptionId": data.get("subscriptionId"),
                "creditId": data.get("creditId"),
                "isCompany": data.get("isCompany", False),
                "companyName": data.get("companyName", ""),
                "paymentInfo": data.get("paymentInfo", ""),
                "subscriptionStatus": data.get("subscriptionStatus", "active"),
                "createdAt": data.get("createdAt", datetime.utcnow()),
                "referralBonus": data.get("referralBonus", 0),
                "subscriptionStart": data.get("subscriptionStart", datetime.utcnow()),
                "subscriptionEnd": data.get("subscriptionEnd"),
                "isActive": data.get("isActive", True),
                "created_at": data.get("created_at", datetime.utcnow()),
                "isFirstLogin": data.get("isFirstLogin", True),
            }

            # Insert account into the database
            self.collection.insert_one(account_document)
            logger.info(f"Account created successfully: {account_document}")

            initialize_credits(data["ownerId"])

            return {
                "message": "Account created successfully",
                "accountId": account_id,
            }, 201

        except ValueError as ve:
            logger.error("ValueError: %s", ve)
            return {"error": str(ve)}, 400
        except Exception as e:
            logger.error("Error creating account: %s", e, exc_info=True)
            return {"error": f"Error creating account: {str(e)}"}, 500

    def get_account(self, account_id):
        try:
            account = self.collection.find_one({"_id": account_id})
            if not account:
                return {"error": "Account not found"}, 404

            schema = AccountSchema()
            result = schema.dump(account)

            return {"account": result}, 200

        except Exception as e:
            logger.error(f"Failed to fetch account: {e}")
            return {"error": f"Failed to fetch account: {str(e)}"}, 500

    def get_account_by_user(self, user_id):  # user_id is the owner's ID
        try:
            # Find account by ownerId
            account = self.collection.find_one({"ownerId": user_id})  # Query by ownerId
            if not account:
                return {"error": "Account not found"}, 404

            return {"account": account}, 200

        except Exception as e:
            logger.error(f"Failed to fetch account: {e}")
            return {"error": f"Failed to fetch account: {str(e)}"}, 500

    def edit_account(self, user_id, data):  # user_id is the owner's ID
        try:
            updates = {k: v for k, v in data.items() if v is not None}

            if not updates:
                return {"error": "No valid fields provided for update"}, 400

            # Update account based on ownerId
            self.collection.update_one(
                {"ownerId": user_id}, {"$set": updates}
            )  # Query by ownerId

            return {"message": "Profile updated successfully!"}, 200

        except Exception as e:
            logger.error(f"Error updating profile: {e}", exc_info=True)
            return {"error": f"Error updating profile: {str(e)}"}, 500

    def delete_by_user(self, user_id):  # user_id is the owner's ID
        try:
            # Delete accounts based on ownerId
            result = self.collection.delete_many(
                {"ownerId": user_id}
            )  # Query by ownerId
            logger.info(f"Deleted {result.deleted_count} accounts for user {user_id}")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to delete accounts: {e}", exc_info=True)
            return 0
