import logging
from flask import url_for
from werkzeug.security import check_password_hash, generate_password_hash
from backend.database.mongo_connection import collection

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self):
        self.user_collection = collection.database.Users
        self.teams_collection = collection.database.Teams
        self.user_to_teams_collection = collection.database.UsersToTeams

    def get_user_by_email(self, email):

        return self.user_collection.find_one({"email": email.lower().strip()})
    
    def get_user_by_id(self, user_id):

        return self.user_collection.find_one({"_id": user_id})

    def get_profile(self, user_id):
        try:
            user = self.user_collection.find_one(
                {"_id": user_id}, {"email": 1, "full_name": 1, "phone": 1}
            )

            if not user:
                return {"error": "User not found"}, 404

            return {
                "full_name": user.get("full_name", ""),
                "email": user.get("email", ""),
                "phone": user.get("phone", ""),
            }, 200

        except Exception as e:
            logger.error(f"Failed to fetch profile: {e}", exc_info=True)
            return {"error": f"Failed to fetch profile: {str(e)}"}, 500

    def update_profile(self, user_id, data):
        try:
            updates = {k: v for k, v in data.items() if v is not None}

            if not updates:
                return {"error": "No valid fields provided for update"}, 400

            self.user_collection.update_one({"_id": user_id}, {"$set": updates})

            return {"message": "Profile updated successfully!"}, 200

        except Exception as e:
            logger.error(f"Error updating profile: {e}", exc_info=True)
            return {"error": f"Error updating profile: {str(e)}"}, 500

    def update_password(self, user_id, data):
        try:
            current_password = data.get("current_password")
            new_password = data.get("new_password")

            if not current_password or not new_password:
                return {"error": "Both current and new passwords are required"}, 400

            user = self.user_collection.find_one({"_id": user_id})

            if not user:
                return {"error": "User not found"}, 404

            if not check_password_hash(user.get("passwordHash", ""), current_password):
                return {"error": "Current password is incorrect"}, 400

            hashed_new_password = generate_password_hash(new_password)

            self.user_collection.update_one({"_id": user_id}, {"$set": {"passwordHash": hashed_new_password}})

            return {"message": "Password updated successfully!"}, 200

        except Exception as e:
            logger.error(f"Error updating password: {e}", exc_info=True)
            return {"error": f"Error updating password: {str(e)}"}, 500

    def delete_user(self, data):
        try:
            input_email = data.get("deleteEmail")
            input_password = data.get("deletePassword")
            delete_confirm = data.get("deleteConfirm", "").strip().upper()

            if delete_confirm != "DELETE":
                return {"error": "Please type 'DELETE' exactly to confirm account deletion."}, 400

            if not input_email or not input_password:
                return {"error": "Email and password are required."}, 400

            user = self.user_collection.find_one({"email": {"$regex": f"^{input_email}$", "$options": "i"}})
            if not user:
                return {"error": "User does not exist in the database."}, 404

            stored_hash = user.get("passwordHash")
            if not stored_hash or not check_password_hash(stored_hash, input_password):
                return {"error": "Incorrect password."}, 400

            user_id = user.get("_id")

            self.user_to_teams_collection.delete_many({"userId": user_id})
            self.teams_collection.delete_many({"UserID": user_id})
            user_result = self.user_collection.delete_one({"_id": user_id})

            if user_result.deleted_count == 0:
                return {"error": "User deletion failed."}, 500

            return {
                "message": "User account and associated data deleted successfully.",
                "redirect": url_for("auth_bp.signin"),
            }, 200

        except Exception as e:
            logger.error(f"Error during deletion: {e}", exc_info=True)
            return {"error": f"Error during deletion: {str(e)}"}, 500