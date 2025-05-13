import logging
import uuid
from datetime import datetime
from bson import ObjectId
from backend.database.mongo_connection import collection
from backend.repository.account_repository import AccountRepository

logger = logging.getLogger(__name__)


class AuthRepository:
    def __init__(self):
        self.user_collection = collection.database.Users
        self.account_collection = collection.database.Accounts
        self.account_repository = AccountRepository()

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
        """Creates a new user document and ensures an account exists."""
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
                # Ensure account exists using AccountRepository
                account_data_for_creation = {
                    "ownerId": user_data["_id"],
                    "email": user_data["email"],
                    "isFirstLogin": True,
                }
                account_result, status_code = self.account_repository.create_account(account_data_for_creation)
                if status_code not in [200, 201]:
                    logger.error(
                        f"Failed to create or retrieve account for user {user_data['_id']}: {account_result.get('error')}"
                    )
                    self.user_collection.delete_one({"_id": result.inserted_id})
                    return None
                logger.info(f"Account ensured for user {user_data['_id']}. Account ID: {account_result.get('accountId')}")
                return self.user_collection.find_one({"_id": result.inserted_id})
            else:
                logger.error("User creation failed (insert operation).")
                return None
        except Exception as e:
            logger.error(
                f"Error creating user {user_data.get('email')}: {e}", exc_info=True
            )
            return None
