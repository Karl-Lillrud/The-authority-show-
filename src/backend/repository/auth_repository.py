import logging
import uuid
from datetime import datetime
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
                logger.debug(f"User found: {user['id']}")
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
            if "id" not in user_data or not user_data["id"]:  # Ensure id is generated if missing or empty
                user_data["id"] = str(uuid.uuid4())
            if "email" not in user_data:
                logger.error("Cannot create user without email.")
                return None
            user_data["email"] = user_data["email"].lower().strip()
            user_data.setdefault("createdAt", datetime.utcnow().isoformat())
            user_data.setdefault("updatedAt", datetime.utcnow().isoformat())
            # Add other default fields as per your User schema

            logger.info(
                f"Creating new user with ID: {user_data['id']} for email: {user_data['email']}"
            )
            result = self.user_collection.insert_one(user_data)
            # result.inserted_id will be the _id (ObjectId) assigned by MongoDB
            # user_data["id"] is the string UUID we assigned to the 'id' field

            if result.inserted_id:  # Confirms the insert operation itself was acknowledged by MongoDB
                # Ensure account exists using AccountRepository
                account_data_for_creation = {
                    "ownerId": user_data["id"],  # Link account to the user's string id
                    "isFirstLogin": True,
                    # The AccountRepository.create_account method will be responsible for generating its own string 'id'
                }
                # Assuming account_result is a dictionary representing the created/found account,
                # and it contains an 'id' field (string UUID) for the account.
                account_result, status_code = self.account_repository.create_account(account_data_for_creation)
                if status_code not in [200, 201]:
                    logger.error(
                        f"Failed to create or retrieve account for user {user_data['id']}: {account_result.get('error')}"
                    )
                    # Rollback user creation if account creation fails
                    self.user_collection.delete_one({"id": user_data["id"]})
                    return None
                # Use 'id' from account_result, assuming it's the standard identifier
                logger.info(f"Account ensured for user {user_data['id']}. Account ID: {account_result.get('id')}")
                # Fetch the user document using the string 'id' we generated and inserted
                return self.user_collection.find_one({"id": user_data["id"]})
            else:
                logger.error("User creation failed (insert operation did not return an inserted_id).")
                return None
        except Exception as e:
            logger.error(
                f"Error creating user {user_data.get('email')}: {e}", exc_info=True
            )
            return None
