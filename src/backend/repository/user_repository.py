import logging
from flask import url_for
from werkzeug.security import check_password_hash, generate_password_hash
from backend.database.mongo_connection import collection
from backend.repository.account_repository import AccountRepository
from backend.repository.episode_repository import EpisodeRepository
from backend.repository.guest_repository import GuestRepository
from backend.repository.podcast_repository import PodcastRepository
from backend.repository.podtask_repository import PodtaskRepository
from backend.repository.usertoteam_repository import UserToTeamRepository
from backend.repository.team_repository import TeamRepository
from backend.repository.teaminvitrepository import TeamInviteRepository

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

    # Delete user and all associated data from related collections
    def cleanup_user_data(self, user_id, user_email):
        try:
            user_id_str = str(user_id)
            logger.info(f"Starting cleanup for user {user_id_str} ({user_email})")

            # Delete content in each related collection
            episodes = EpisodeRepository().delete_by_user(user_id_str)
            guests = GuestRepository().delete_by_user(user_id_str)
            podcasts = PodcastRepository().delete_by_user(user_id_str)
            podtasks = PodtaskRepository().delete_by_user(user_id_str)            
            
            # Clean up teams: remove from members or delete if creator
            team_repo = TeamRepository()
            affected_teams = team_repo.user_to_teams_collection.find(
                {"userId": user_id_str}, {"teamId": 1}
            )

            team_cleanup_results = []
            deleted_count = 0
            removed_count = 0

            for entry in affected_teams:
                team_id = entry.get("teamId")
                if team_id:
                    result = team_repo.remove_member_or_delete_team(team_id, user_id_str, return_message_only=True)
                    team_cleanup_results.append(result)

                    # Count deletions vs removals
                    if "deleted" in result.get("message", "").lower():
                        deleted_count += 1
                    elif "removed" in result.get("message", "").lower():
                        removed_count += 1

            logger.info(f"🧹 Team cleanup summary for user {user_id_str}: {deleted_count} team(s) deleted, {removed_count} team(s) cleaned (user removed from team members)")

            # Continue cleanup
            accounts = AccountRepository().delete_by_user(user_id_str)
            user_teams = UserToTeamRepository().delete_by_user(user_id_str)         

            return {
                "episodes_deleted": episodes,
                "guests_deleted": guests,
                "podcasts_deleted": podcasts,
                "podtasks_deleted": podtasks,
                "accounts_deleted": accounts,
                "user_team_links_deleted": user_teams,
                "teams_processed": team_cleanup_results 
            }

        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)
            return {"error": f"Cleanup failed: {str(e)}"}

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

            cleanup_result = self.cleanup_user_data(user_id, user["email"])
            
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