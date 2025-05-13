import logging
import uuid
from datetime import datetime
from bson import ObjectId
from backend.database.mongo_connection import collection
from backend.services.creditService import initialize_credits

logger = logging.getLogger(__name__)


class AuthRepository:
    def __init__(self):
        self.user_collection = collection.database.Users
        self.account_collection = collection.database.Accounts

    def find_user_by_email(self, email):
        """Finds a user by email."""
        try:
            logger.debug(f"Searching for user with email: {email}")
            user = self.user_collection.find_one({"email": email.lower().strip()})
            if user:
                logger.debug(f"User found: {user['_id']}")
            else:
                logger.debug("User not found.")
            return user
        except Exception as e:
            logger.error(f"Error finding user by email {email}: {e}", exc_info=True)
            return None

    def create_user(self, user_data):
        """Creates a new user document."""
        try:
            # Ensure required fields are present, add defaults if needed
            if "_id" not in user_data:
                user_data["_id"] = str(uuid.uuid4())
            if "email" not in user_data:
                logger.error("Cannot create user without email.")
                return None
            user_data["email"] = user_data["email"].lower().strip()
            user_data.setdefault("createdAt", datetime.utcnow().isoformat())
            user_data.setdefault("updatedAt", datetime.utcnow().isoformat())
            # Add other default fields as per your User schema

            logger.info(
                f"Creating new user with ID: {user_data['_id']} for email: {user_data['email']}"
            )
            result = self.user_collection.insert_one(user_data)
            if result.inserted_id:
                # Create account using internal create_account method
                account_data = {
                    "ownerId": user_data["_id"],
                    "isFirstLogin": True,
                }
                account_result, status_code = self.create_account(account_data)
                if status_code not in [200, 201]:
                    logger.error(
                        f"Failed to create account for user {user_data['_id']}: {account_result.get('error')}"
                    )
                    return None
                return self.user_collection.find_one({"_id": result.inserted_id})
            else:
                logger.error("User creation failed (insert operation).")
                return None
        except Exception as e:
            logger.error(
                f"Error creating user {user_data.get('email')}: {e}", exc_info=True
            )
            return None

    def create_account(self, data):
        """
        Creates a new account for the user if one does not exist, or returns the existing account.
        Args:
            data (dict): Contains ownerId and optional fields (e.g., subscriptionId, isFirstLogin).
        Returns: (dict, status_code)
        """
        try:
            # Validate inputs
            user_id = data.get("ownerId")
            if not user_id or not isinstance(user_id, str):
                logger.error(f"Invalid user_id: {user_id}")
                return {"error": "Invalid or missing user_id"}, 400

            # Check if an account already exists for the user
            logger.debug(f"Checking for existing account with ownerId: {user_id}")
            existing_account = self.account_collection.find_one({"ownerId": user_id})
            if existing_account:
                logger.info(
                    f"Account already exists for user {user_id}: {existing_account['_id']}"
                )
                return {
                    "message": "Account already exists",
                    "accountId": existing_account["_id"],
                }, 200

            # Create a new account
            account_data = {
                "_id": str(ObjectId()),
                "ownerId": user_id,
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat(),
                "isActive": data.get("isActive", True),
                "subscriptionId": data.get("subscriptionId", str(ObjectId())),
                "creditId": data.get("creditId", str(ObjectId())),
                "isCompany": data.get("isCompany", False),
                "companyName": data.get("companyName", ""),
                "subscriptionStatus": data.get("subscriptionStatus", "active"),
                "subscriptionStart": data.get(
                    "subscriptionStart", datetime.utcnow().isoformat()
                ),
                "subscriptionEnd": data.get("subscriptionEnd"),
                "referralBonus": data.get("referralBonus", 0),
                "isFirstLogin": data.get("isFirstLogin", True),
                "lastUpdated": datetime.utcnow().isoformat(),
                "subscriptionAmount": 0,
                "subscriptionPlan": "Free",
            }
            logger.debug(f"Attempting to create account with data: {account_data}")
            result = self.account_collection.insert_one(account_data)
            if result.inserted_id:
                logger.info(
                    f"New account created for user {user_id}: {account_data['_id']}"
                )
                # Initialize credits
                logger.debug(f"Initializing credits for ownerId: {user_id}")
                try:
                    initialize_credits(user_id)
                except Exception as credit_error:
                    logger.error(
                        f"Failed to initialize credits for ownerId {user_id}: {str(credit_error)}"
                    )
                return {
                    "message": "Account created successfully!",
                    "accountId": account_data["_id"],
                }, 201
            else:
                logger.error(
                    f"Failed to insert account for user {user_id}: No inserted_id returned"
                )
                return {"error": "Failed to create account due to database error"}, 500

        except Exception as e:
            logger.error(
                f"Error creating account for user {user_id}: {str(e)}", exc_info=True
            )
            return {"error": f"Internal server error: {str(e)}"}, 500
