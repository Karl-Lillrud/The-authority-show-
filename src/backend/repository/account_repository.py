import uuid
from datetime import datetime
from backend.database.mongo_connection import collection
from backend.models.accounts import AccountSchema
import logging

logger = logging.getLogger(__name__)

#THIS GETS IMPORTED INTO ROUTES
#USE FOR CRUD OPERATIONS ONLY
#SERVICES SHOULD BE USED FOR EXTRA FUNCTIONALITY INTO REPOSITORY

class AccountRepository:
    def __init__(self):
        self.collection = collection.database.Accounts  # Use the Accounts collection

    def create_account(self, data):
        try:
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
                "_id": account_id,
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

            # Insert account into the database
            self.collection.insert_one(account_document)
            logger.info("Inserted account into database: %s", account_document)

            return {
                "message": "Account created successfully",
                "accountId": account_document["_id"],
            }, 201

        except ValueError as ve:
            logger.error("ValueError: %s", ve)
            return {"error": str(ve)}, 400
        except Exception as e:
            logger.error("Error creating account: %s", e, exc_info=True)
            return {"error": f"Error creating account: {str(e)}"}, 500

    def get_account(self, account_id):
        try:
            account = self.collection.find_one({"id": account_id})
            if not account:
                return {"error": "Account not found"}, 404

            schema = AccountSchema()
            result = schema.dump(account)  # Serialize the account data

            return {"account": result}, 200

        except Exception as e:
            logger.error(f"Failed to fetch account: {e}")
            return {"error": f"Failed to fetch account: {str(e)}"}, 500

    def delete_by_user(self, user_id):
        try:
            result = self.collection.delete_many({"userId": user_id})
            logger.info(f"Deleted {result.deleted_count} accounts for user {user_id}")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to delete accounts: {e}", exc_info=True)
            return 0

    def get_credit_ids_by_user(self, user_id):
        try:
            user_id_str = str(user_id)

            account = self.collection.find_one({"userId": user_id_str}, {"_id": 1})
            if not account:
                logger.warning(f"No account found for user {user_id_str}")
                return []

            account_id_str = str(account["_id"])

            credits = self.credits_collection.find(
                {"accountId": account_id_str}, {"_id": 1}
            )
            credit_ids = [str(credit["_id"]) for credit in credits]

            logger.info(
                f"Found {len(credit_ids)} credit IDs for user {user_id_str}: {credit_ids}"
            )
            return credit_ids

        except Exception as e:
            logger.error(f"Failed to retrieve credit IDs: {e}", exc_info=True)
            return []