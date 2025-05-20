import logging
from flask import url_for
from backend.database.mongo_connection import collection
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


logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self):
        self.user_collection = collection.database.Users
        self.teams_collection = collection.database.Teams
        self.user_to_teams_collection = collection.database.UsersToTeams

    def get_user_by_email(self, email):
        return self.user_collection.find_one({"email": email.lower().strip()})

    def get_user_by_id(self, user_id):
        """
        Get user by ID, always using string representation.
        """
        try:
            # Always use string ID
            string_user_id = str(user_id)
            return self.user_collection.find_one({"_id": string_user_id})
        except Exception as e:
            logger.error(f"Error in get_user_by_id: {e}", exc_info=True)
            return None
    
    def get_profile(self, user_id):
        """
        Get user profile by ID, always using string representation.
        """
        try:
            # Always use string ID
            string_user_id = str(user_id)
            user = self.user_collection.find_one(
                {"_id": string_user_id}, {"email": 1, "full_name": 1, "phone": 1, "profile_pic_url": 1}
            )

            if not user:
                return {"error": "User not found"}, 404

            return {
                "full_name": user.get("full_name", ""),
                "email": user.get("email", ""),
                "phone": user.get("phone", ""),
                "profile_pic_url": user.get("profile_pic_url", ""),
            }, 200

        except Exception as e:
            logger.error(f"Failed to fetch profile: {e}", exc_info=True)
            return {"error": f"Failed to fetch profile: {str(e)}"}, 500

    def update_profile(self, user_id, data):
        """
        Update user profile, always using string representation of user ID.
        """
        try:
            # Always use string ID
            string_user_id = str(user_id)
            updates = {k: v for k, v in data.items() if v is not None}

            if not updates:
                return {"error": "No valid fields provided for update"}, 400

            self.user_collection.update_one({"_id": string_user_id}, {"$set": updates})

            return {"message": "Profile updated successfully!"}, 200

        except Exception as e:
            logger.error(f"Error updating profile: {e}", exc_info=True)
            return {"error": f"Error updating profile: {str(e)}"}, 500

    def update_profile_picture(self, user_id, profile_pic_url):
        """
        Update user's profile picture URL.
        Args:
            user_id (str): The ID of the user
            profile_pic_url (str): The URL of the profile picture in Azure Blob Storage
        Returns:
            tuple: (dict, int) containing response message and status code
        """
        try:
            # Always use string ID
            string_user_id = str(user_id)
            result = self.user_collection.update_one(
                {"_id": string_user_id},
                {"$set": {"profile_pic_url": profile_pic_url}}
            )

            if result.matched_count == 0:
                logger.error(f"No user found with ID: {string_user_id}")
                return {"error": "User not found"}, 404

            logger.info(f"Successfully updated profile picture for user {string_user_id}")
            return {"message": "Profile picture updated successfully"}, 200

        except Exception as e:
            logger.error(f"Error updating profile picture for user {user_id}: {e}", exc_info=True)
            return {"error": f"Failed to update profile picture: {str(e)}"}, 500

    # Delete user and all associated data from related collections
    def cleanup_user_data(self, user_id, user_email):
        """
        Clean up all user data across collections, using string representation of user ID.
        """
        try:
            # Always use string ID
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
            user_teams = UserToTeamRepository().delete_by_user(user_id_str)
            user_credit = delete_credits_by_user(user_id_str)
            user_activity = ActivitiesRepository().delete_by_user(user_id_str)

            return {
                "episodes_deleted": episodes,
                "guests_deleted": guests,
                "podcasts_deleted": podcasts,
                "podtasks_deleted": podtasks,
                "user_team_links_deleted": user_teams,
                "teams_processed": team_cleanup_results,
                "user_credits_deleted": user_credit,
                "user_activity_deleted": user_activity,
            }

        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)
            return {"error": f"Cleanup failed: {str(e)}"}

    def delete_user(self, data):
        """
        Delete user and all associated data, using string representation of user ID.
        """
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
                return {"error": "User does not exist in the database."}, 404

            user_id = user.get("_id")
            # Always use string ID
            user_id_str = str(user_id)

            cleanup_result = self.cleanup_user_data(user_id_str, user["email"])

            user_result = self.user_collection.delete_one({"_id": user_id_str})

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
        Save access token and refresh token to the user document using string ID.
        """
        try:
            # Log token saving attempt
            logger.info(f"save_tokens called for user {user_id}")
            
            # Always convert user_id to string to ensure consistency
            string_user_id = str(user_id)
            
            # Create update data
            user_data = {
                "googleCalAccessToken": access_token,
                "googleCalRefreshToken": refresh_token,
                "googleCalLastUpdated": datetime.now(timezone.utc)
            }
            
            # Update using string ID
            result = self.user_collection.update_one(
                {"_id": string_user_id},
                {"$set": user_data}
            )
            
            logger.info(f"Update with user_id {string_user_id}: matched={result.matched_count}, modified={result.modified_count}")
            
            if result.matched_count > 0:
                # We found and updated the user
                logger.info(f"Successfully updated user {string_user_id} with tokens")
                
                # Verify the update
                user = self.user_collection.find_one({"_id": string_user_id})
                if user and user.get("googleCalRefreshToken") == refresh_token:
                    logger.info(f"Verified tokens saved for user {string_user_id}")
                    return {"message": "Tokens saved successfully"}, 200
                else:
                    logger.warning(f"Tokens saved but verification failed for user {string_user_id}")
                    return {"message": "Tokens saved but verification failed"}, 200
            
            # If we get here, we didn't find the user
            logger.error(f"No user found with ID: {string_user_id}")
            return {"error": "User not found"}, 404

        except Exception as e:
            logger.error(f"Failed to save tokens for user {user_id}: {str(e)}", exc_info=True)
            return {"error": f"Failed to save tokens: {str(e)}"}, 500