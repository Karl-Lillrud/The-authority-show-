import logging
from datetime import datetime
from backend.database.mongo_connection import collection
from backend.repository.auth_repository import AuthRepository

logger = logging.getLogger(__name__)


class AccountRepository:
    def __init__(self):
        self.collection = collection.database.Accounts
        self.auth_repository = AuthRepository()

    def create_account(self, data):
        try:
            if not data or "ownerId" not in data:
                return {"error": "ownerId are required"}, 400

            # Use AuthRepository to create or retrieve account
            account_result, status_code = self.auth_repository.create_account(data)
            if status_code in [200, 201]:
                logger.info(
                    f"Account {'created' if status_code == 201 else 'found'} for ownerId {data['ownerId']}: {account_result['accountId']}"
                )
                return account_result, status_code
            else:
                logger.error(
                    f"Failed to create/retrieve account for ownerId {data['ownerId']}: {account_result.get('error')}"
                )
                return account_result, status_code

        except Exception as e:
            logger.error(f"Error while creating account: {e}", exc_info=True)
            return {"error": f"Error while creating account: {str(e)}"}, 500

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
