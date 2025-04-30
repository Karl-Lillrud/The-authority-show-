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
from backend.repository.teaminviterepository import TeamInviteRepository
from backend.repository.credits_repository import delete_by_user as delete_credits_by_user
from backend.repository.activities_repository import ActivitiesRepository
from datetime import datetime, timezone
import bson

logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self):
        self.user_collection = collection.database.Users
        self.teams_collection = collection.database.Teams
        self.user_to_teams_collection = collection.database.UsersToTeams

    def get_user_by_email(self, email):
        return self.user_collection.find_one({"email": email.lower().strip()})

    def get_user_by_id(self, user_id):
        # Handle both string and ObjectId formats
        try:
            if isinstance(user_id, str) and bson.ObjectId.is_valid(user_id):
                # Try to convert to ObjectId if it's a valid format
                return self.user_collection.find_one({"_id": bson.ObjectId(user_id)})
            else:
                # Otherwise use as is
                return self.user_collection.find_one({"_id": user_id})
        except Exception as e:
            logger.error(f"Error in get_user_by_id: {e}", exc_info=True)
            # Try both formats as fallback
            return self.user_collection.find_one({"$or": [
                {"_id": user_id},
                {"_id": str(user_id)}
            ]})

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

            self.user_collection.update_one(
                {"_id": user_id}, {"$set": {"passwordHash": hashed_new_password}}
            )

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
                    result = team_repo.remove_member_or_delete_team(
                        team_id, user_id_str, return_message_only=True
                    )
                    team_cleanup_results.append(result)

                    # Count deletions vs removals
                    if "deleted" in result.get("message", "").lower():
                        deleted_count += 1
                    elif "removed" in result.get("message", "").lower():
                        removed_count += 1

            logger.info(
                f"🧹 Team cleanup summary for user {user_id_str}: {deleted_count} team(s) deleted, {removed_count} team(s) cleaned (user removed from team members)"
            )

            # Continue cleanup
            accounts = AccountRepository().delete_by_user(user_id_str)
            user_teams = UserToTeamRepository().delete_by_user(user_id_str)
            user_credit = delete_credits_by_user(user_id_str)
            user_activity = ActivitiesRepository().delete_by_user(user_id_str)

            return {
                "episodes_deleted": episodes,
                "guests_deleted": guests,
                "podcasts_deleted": podcasts,
                "podtasks_deleted": podtasks,
                "accounts_deleted": accounts,
                "user_team_links_deleted": user_teams,
                "teams_processed": team_cleanup_results,
                "user_credits_deleted": user_credit,
                "user_activity_deleted": user_activity,
            }

        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)
            return {"error": f"Cleanup failed: {str(e)}"}

    def delete_user(self, data):
        try:
            input_email = data.get("deleteEmail")
            delete_confirm = data.get("deleteConfirm", "").strip().upper()

            if delete_confirm != "DELETE":
                return {
                    "error": "Please type 'DELETE' exactly to confirm account deletion."
                }, 400

            if not input_email:
                return {"error": "Email is required."}, 400

            user = self.user_collection.find_one(
                {"email": input_email.lower().strip()}
            )
            if not user:
                return {"error": "User doeexist in the database."}, 404

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

    def save_tokens(self, user_id, access_token, refresh_token):
        """
        Save access token and refresh token to the user document.
        """
        try:
            # Log token saving attempt with partial token info for security
            logger.info(f"save_tokens called for user {user_id}")
            
            # Try different user_id formats to ensure we find the user
            try_user_ids = [user_id]
            
            # If it's a string that could be an ObjectId, add that format
            if isinstance(user_id, str) and bson.ObjectId.is_valid(user_id):
                try_user_ids.append(bson.ObjectId(user_id))
            
            # If it's an ObjectId, add the string version
            if not isinstance(user_id, str):
                try_user_ids.append(str(user_id))
                
            logger.info(f"Will try user IDs: {try_user_ids}")
            
            # Create update data
            user_data = {
                "googleCalAccessToken": access_token,
                "googleCalRefreshToken": refresh_token,
                "googleCalLastUpdated": datetime.now(timezone.utc)
            }
            
            # Try to update with each possible user_id format
            for uid in try_user_ids:
                try:
                    result = self.user_collection.update_one(
                        {"_id": uid},
                        {"$set": user_data}
                    )
                    
                    logger.info(f"Update with user_id {uid}: matched={result.matched_count}, modified={result.modified_count}")
                    
                    if result.matched_count > 0:
                        # We found and updated the user, so we can stop trying
                        logger.info(f"Successfully updated user {uid} with tokens")
                        
                        # Verify the update
                        user = self.user_collection.find_one({"_id": uid})
                        if user and user.get("googleCalRefreshToken") == refresh_token:
                            logger.info(f"Verified tokens saved for user {uid}")
                            return {"message": "Tokens saved successfully"}, 200
                        else:
                            logger.warning(f"Tokens saved but verification failed for user {uid}")
                            
                        # Even if verification failed, we did find and update the user
                        return {"message": "Tokens saved"}, 200
                except Exception as e:
                    logger.error(f"Error updating user {uid}: {e}", exc_info=True)
            
            # If we get here, we didn't find the user with any ID format
            logger.error(f"No user found with any ID format: {try_user_ids}")
            return {"error": "User not found"}, 404

        except Exception as e:
            logger.error(f"Failed to save tokens for user {user_id}: {str(e)}", exc_info=True)
            return {"error": f"Failed to save tokens: {str(e)}"}, 500
