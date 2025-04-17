import logging
from backend.database.mongo_connection import collection
from backend.services.accountService import AccountService

logger = logging.getLogger(__name__)


class AuthRepository:
    def __init__(self):
        self.user_collection = collection.database.Users
        self.account_service = AccountService()

    def find_user_by_email(self, email):
        try:
            user = self.user_collection.find_one({"email": email})
            return user
        except Exception as e:
            logger.error(
                f"Error finding user by email {email}: {str(e)}", exc_info=True
            )
            return None

    def create_user(self, user_data):
        try:
            result = self.user_collection.insert_one(user_data)
            if result.inserted_id:
                logger.info(f"User created: {user_data['email']}")
                # Create account using AccountService
                account, status_code = (
                    self.account_service.create_account_if_not_exists(
                        user_data["_id"], user_data["email"]
                    )
                )
                if status_code not in [200, 201]:
                    logger.error(
                        f"Failed to create account for user {user_data['_id']}: {account.get('error')}"
                    )
                    return None
                return user_data
            return None
        except Exception as e:
            logger.error(
                f"Error creating user {user_data['email']}: {str(e)}", exc_info=True
            )
            return None

    # Övriga metoder i AuthRepository...
