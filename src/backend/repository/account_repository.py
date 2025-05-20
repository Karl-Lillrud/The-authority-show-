import logging
import uuid
from datetime import datetime
from backend.database.mongo_connection import collection
from backend.services.creditService import initialize_credits
from backend.services.subscriptionService import SubscriptionService
from backend.utils.subscription_access import PLAN_BENEFITS

logger = logging.getLogger(__name__)

class AccountRepository:
    def __init__(self):
        self.collection = collection.database.Accounts
        self.subscription_service = SubscriptionService()

    def create_account(self, data):
        """
        Creates a new account for the user if one does not exist, or returns the existing account.
        Args:
            data (dict): Contains ownerId, email, and optional fields (e.g., isFirstLogin).
        Returns: (dict, status_code)
        """
        try:
            user_id = data.get("ownerId")
            email = data.get("email")
            if not user_id or not isinstance(user_id, str):
                logger.error(f"Invalid user_id: {user_id}")
                return {"error": "Invalid or missing ownerId"}, 400
            if not email or not isinstance(email, str):
                logger.error(f"Invalid email: {email}")
                return {"error": "Invalid or missing email"}, 400

            # Check if an account already exists for the user
            logger.debug(f"Checking for existing account with ownerId: {user_id}")
            existing_account = self.collection.find_one({"ownerId": user_id})
            if existing_account:
                logger.info(
                    f"Account already exists for user {user_id}: {existing_account['_id']}"
                )
                # Optionally update isFirstLogin if provided and changed
                if "isFirstLogin" in data and existing_account.get("isFirstLogin") != data["isFirstLogin"]:
                    self.collection.update_one(
                        {"_id": existing_account["_id"]},
                        {"$set": {"isFirstLogin": data["isFirstLogin"], "updatedAt": datetime.utcnow().isoformat()}}
                    )
                return {
                    "message": "Account already exists",
                    "accountId": existing_account["_id"],
                }, 200

            # Create a new account
            account_id = str(uuid.uuid4())  # Define account_id
            subscription_id = data.get("subscriptionId") or str(uuid.uuid4())
            credit_id = data.get("creditId") or str(uuid.uuid4())

            # Get the subscription plan and its benefits
            plan = data.get("subscriptionPlan", "FREE").upper()
            benefits = PLAN_BENEFITS.get(plan, PLAN_BENEFITS["FREE"])
            
            # Initialize with 0 extra slots - base slots are handled by the plan
            account_data = {
                "_id": account_id,
                "ownerId": user_id,
                "email": email.lower().strip(),
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat(),
                "isActive": data.get("isActive", True),
                "subscriptionId": subscription_id,
                "creditId": credit_id,
                "isCompany": data.get("isCompany", False),
                "companyName": data.get("companyName", ""),
                "subscriptionStatus": data.get("subscriptionStatus", "active"),
                "subscriptionStart": data.get("subscriptionStart", datetime.utcnow().isoformat()),
                "subscriptionEnd": data.get("subscriptionEnd"),
                "referralBonus": data.get("referralBonus", 0),
                "isFirstLogin": data.get("isFirstLogin", True),
                "lastUpdated": datetime.utcnow().isoformat(),
                "subscriptionAmount": data.get("subscriptionAmount", 0),
                "subscriptionPlan": plan,
                "unlockedExtraEpisodeSlots": 0,  # Start with 0 extra slots
                "benefits": benefits  # Store the plan benefits for reference
            }
            logger.debug(f"Attempting to create account with data: {account_data}")
            result = self.collection.insert_one(account_data)
            if result.inserted_id:
                logger.info(
                    f"New account created for user {user_id}: {account_id}"
                )
                # Initialize credits for the new user
                try:
                    initialize_credits(user_id)
                except Exception as credit_error:
                    logger.error(
                        f"Failed to initialize credits for ownerId {user_id}: {str(credit_error)}"
                    )
                return {
                    "message": "Account created successfully!",
                    "accountId": account_id,
                }, 201
            else:
                logger.error(
                    f"Failed to insert account for user {user_id}: No inserted_id returned"
                )
                return {"error": "Failed to create account due to database error"}, 500

        except Exception as e:
            logger.error(
                f"Error creating/retrieving account for user {data.get('ownerId')}: {str(e)}", exc_info=True
            )
            return {"error": f"Internal server error: {str(e)}"}, 500

    def get_account(self, account_id):
        try:
            account = self.collection.find_one({"_id": account_id})
            if not account:
                return {"error": "Account not found"}, 404
            return {"account": account}, 200
        except Exception as e:
            logger.error(f"Error while retrieving account: {e}", exc_info=True)
            return {"error": f"Error while retrieving account: {str(e)}"}, 500

    def get_account_by_user(self, user_id):
        try:
            account = self.collection.find_one({"ownerId": user_id})
            if not account:
                return {"error": "Account not found"}, 404
            return {"account": account}, 200
        except Exception as e:
            logger.error(f"Error while retrieving account: {e}", exc_info=True)
            return {"error": f"Error while retrieving account: {str(e)}"}, 500

    def edit_account(self, user_id, data):
        try:
            updates = {k: v for k, v in data.items() if v is not None}
            if not updates:
                return {"error": "No valid fields provided for update"}, 400

            result = self.collection.update_one({"ownerId": user_id}, {"$set": updates})
            if result.matched_count == 0:
                return {"error": "Account not found"}, 404

            return {"message": "Account successfully updated"}, 200
        except Exception as e:
            logger.error(f"Error while updating account: {e}", exc_info=True)
            return {"error": f"Error while updating account: {str(e)}"}, 500

    def edit_increment_account(self, user_id, data):
        try:
            # Filter out None values and ensure the values are numeric
            increment_updates = {
                k: v for k, v in data.items() if v is not None and isinstance(v, (int, float))}

            if not increment_updates:
                return {"error": "No valid fields specified for update"}, 400

            # Perform the update with the $inc operator
            result = self.collection.update_one({"ownerId": user_id}, {"$inc": increment_updates})
            if result.matched_count == 0:
                return {"error": "No account found"}, 404

            return {"message": "Account succesfully updated"}, 200
        except Exception as e:
            logger.error(f"Error updating account: {e}", exc_info=True)
            return {"error": f"Error updating account: {str(e)}"}, 500

    def delete_by_user(self, user_id):
        try:
            result = self.collection.delete_many({"ownerId": user_id})
            logger.info(f"Deleted {result.deleted_count} accounts for userId {user_id}")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error while deleting accounts: {e}", exc_info=True)
            return 0
