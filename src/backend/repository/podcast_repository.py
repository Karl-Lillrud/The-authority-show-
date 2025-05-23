import uuid
from datetime import datetime, timezone
from backend.database.mongo_connection import collection
from backend.models.podcasts import Podcast
from pydantic import ValidationError
from backend.services.rss_Service import RSSService  # Import RSSService
from backend.services.activity_service import ActivityService  # Add this import
from backend.repository.episode_repository import (
    EpisodeRepository,
)  # Assuming EpisodeRepository exists
import logging
import urllib.request
import feedparser
from pydantic.networks import HttpUrl


logger = logging.getLogger(__name__)


class PodcastRepository:
    def __init__(self):
        self.collection = collection.database.Podcasts
        self.activity_service = ActivityService()  # Add this line
        self.episode_repo = EpisodeRepository()  # Initialize EpisodeRepository
        self.rss_service = RSSService()  # Initialize RSSService instance

    @staticmethod
    def get_podcasts_by_user_id(user_id):
        """Fetch podcasts for a specific user."""
        return list(collection.Podcasts.find({"ownerId": user_id}))

    def add_podcast(self, user_id, data):  # user_id here is the owner's ID
        try:
            logger.info(f"Attempting to add podcast for owner_id: {user_id}")
            # Fetch the account document for the logged-in user using ownerId
            user_account = collection.database.Accounts.find_one(
                {"ownerId": user_id}
            )  # Query by ownerId

            if not user_account:
                logger.error(f"Account lookup failed for ownerId: {user_id}")
                raise ValueError("No account associated with this user (owner)")

            account_id = str(user_account["id"])
            data["accountId"] = account_id  # Add accountId to the data
            logger.info(f"Account ID {account_id} added to podcast data.")

            # Validate data using Pydantic's Podcast model
            try:
                validated_podcast = Podcast(**data)
                validated_data = validated_podcast.dict(exclude_none=True)
            except ValidationError as e:
                logger.error(f"Pydantic validation error: {e.errors()}")
                raise ValueError("Invalid podcast data", e.errors())

            # Convert HttpUrl fields to strings
            for key, value in validated_data.items():
                if isinstance(value, HttpUrl):
                    validated_data[key] = str(value)

            podcast_id = str(uuid.uuid4())
            podcast_item = {
                "id": podcast_id,
                "created_at": datetime.now(timezone.utc),
                **validated_data,
            }

            # Insert into database
            result = self.collection.insert_one(podcast_item)
            if result.inserted_id:
                # --- Add activity log for podcast creation using ActivityService ---
                try:
                    self.activity_service.log_activity(
                        user_id=user_id,
                        activity_type="podcast_created",
                        description=f"Created podcast '{podcast_item.get('podName', '')}'",
                        details={
                            "podcastId": podcast_id,
                            "podcastName": podcast_item.get("podName", ""),
                        },
                    )
                except Exception as act_err:
                    logger.error(
                        f"Failed to log activity: {act_err}",
                        exc_info=True,
                    )
                # --- End activity log ---

                return {
                    "message": "Podcast added successfully",
                    "podcast_id": podcast_id,
                    "redirect_url": "/index.html",
                }, 201
            else:
                raise ValueError("Failed to add podcast.")

        except ValueError as e:
            logger.error(
                f"ValueError in add_podcast for user {user_id}: {e}"
            )
            error_message = str(e.args[0]) if e.args else "Invalid data"
            details = e.args[1] if len(e.args) > 1 else None
            return {"error": error_message, "details": details}, 400

        except Exception as e:
            logger.error(
                f"General Exception in add_podcast for user {user_id}: {e}",
                exc_info=True,
            )
            return {"error": "Failed to add podcast", "details": str(e)}, 500

    def get_podcasts(self, user_id):  # user_id is the owner's ID
        try:
            # Find accounts owned by the user
            user_accounts = list(
                collection.database.Accounts.find({"ownerId": user_id}, {"id": 1})
            )  # Query by ownerId
            user_account_ids = [str(account["id"]) for account in user_accounts]

            if not user_account_ids:
                return {"podcast": []}, 200  # No podcasts if no accounts

            podcasts = list(
                self.collection.find({"accountId": {"$in": user_account_ids}})
            )
            for podcast in podcasts:
                podcast["id"] = str(podcast["id"])
                # Set image URL from RSS feed if available
                if podcast.get("rssFeed"):
                    try:
                        rss_data, status_code = self.rss_service.fetch_rss_feed(podcast["rssFeed"])
                        if status_code == 200 and rss_data and rss_data.get("imageUrl"):
                            # Update the podcast in the database with the RSS image URL
                            self.collection.update_one(
                                {"id": podcast["id"]},
                                {"$set": {"rssImage": rss_data["imageUrl"]}}
                            )
                            podcast["rssImage"] = rss_data["imageUrl"]
                            logger.info(f"Updated podcast {podcast['_id']} with RSS image URL: {rss_data['imageUrl']}")
                    except Exception as e:
                        logger.error(f"Failed to fetch RSS data for podcast {podcast['_id']}: {e}")
                # Ensure logoUrl is set (for frontend image display)
                if not podcast.get("logoUrl") and podcast.get("imageUrl"):
                    podcast["logoUrl"] = podcast["imageUrl"]

            return {"podcast": podcasts}, 200

        except Exception as e:
            return {"error": "Failed to fetch podcasts", "details": str(e)}, 500

    def get_podcast_by_id(self, user_id, podcast_id):
        try:
            user_accounts = list(
                collection.database.Accounts.find(
                    {"ownerId": user_id}, {"id": 1, "id": 1}
                )
            )
            user_account_ids = [
                account.get("id", str(account["id"])) for account in user_accounts
            ]

            if not user_account_ids:
                return {"error": "No accounts found for user"}, 403

            podcast = self.collection.find_one(
                {"id": podcast_id, "accountId": {"$in": user_account_ids}}
            )
            if not podcast:
                return {"error": "Podcast not found or unauthorized"}, 404

            podcast["id"] = str(podcast["id"])
            
            # Set image URL from RSS feed if available
            if podcast.get("rssFeed"):
                try:
                    rss_data, status_code = self.rss_service.fetch_rss_feed(podcast["rssFeed"])
                    if status_code == 200 and rss_data and rss_data.get("imageUrl"):
                        # Use the RSS image URL directly
                        podcast["imageUrl"] = rss_data["imageUrl"]
                        logger.info(f"Using RSS image URL for podcast {podcast_id}: {rss_data['imageUrl']}")
                except Exception as e:
                    logger.error(f"Failed to fetch RSS data for podcast {podcast_id}: {e}")
            
            # Ensure logoUrl is set (for frontend image display)
            if not podcast.get("logoUrl") and podcast.get("imageUrl"):
                podcast["logoUrl"] = podcast["imageUrl"]

            return {"podcast": podcast}, 200
        except Exception as e:
            return {"error": f"Failed to fetch podcast: {str(e)}"}, 500

    def delete_podcast(self, user_id, podcast_id):
        try:
            # Fetch user account IDs
            user_accounts = list(
                collection.database.Accounts.find(
                    {"ownerId": user_id}, {"id": 1, "id": 1}
                )
            )
            user_account_ids = [
                account.get("id", str(account["id"])) for account in user_accounts
            ]

            if not user_account_ids:
                raise ValueError("No accounts found for user")

            # Find podcast by podcast_id and accountId
            podcast = self.collection.find_one(
                {"id": podcast_id, "accountId": {"$in": user_account_ids}}
            )
            if not podcast:
                raise ValueError("Podcast not found or unauthorized")

            # Perform delete operation
            result = self.collection.delete_one({"id": podcast_id})
            if result.deleted_count == 1:
                # --- Add activity log for podcast deletion ---
                try:
                    self.activity_service.log_activity(
                        user_id=user_id,
                        activity_type="podcast_deleted",
                        description=f"Deleted podcast '{podcast.get('podName', '')}'",
                        details={
                            "podcastId": podcast_id,
                            "podcastName": podcast.get("podName", ""),
                        },
                    )
                except Exception as act_err:
                    logger.error(
                        f"Failed to log podcast_deleted activity: {act_err}",
                        exc_info=True,
                    )
                # --- End activity log ---
                return {"message": "Podcast deleted successfully"}, 200
            else:
                return {"error": "Failed to delete podcast"}, 500

        except ValueError as e:
            # Handle specific errors like no accounts found or podcast not found
            return {
                "error": str(e)
            }, 400  # Return a 400 Bad Request for known business errors

        except Exception as e:
            return {"error": "Failed to delete podcast", "details": str(e)}, 500

    def edit_podcast(self, user_id, podcast_id, data):
        try:
            # Fetch user account IDs
            user_accounts = list(
                collection.database.Accounts.find(
                    {"ownerId": user_id}, {"id": 1, "id": 1}
                )
            )
            user_account_ids = [
                account.get("id", str(account["id"])) for account in user_accounts
            ]

            if not user_account_ids:
                raise ValueError("No accounts found for user")

            # Find podcast by podcast_id and accountId
            podcast = self.collection.find_one(
                {"id": podcast_id, "accountId": {"$in": user_account_ids}}
            )
            if not podcast:
                raise ValueError("Podcast not found or unauthorized")

            # Validate input data using schema
            schema = Podcast(partial=True)
            errors = schema.validate(data)
            if errors:
                raise ValueError("Invalid data", errors)

            # Prepare update data by filtering out None values
            update_data = {
                key: value for key, value in data.items() if value is not None
            }
            if not update_data:
                return {
                    "message": "No update data provided"
                }, 200  # No actual update needed

            # Perform update operation
            result = self.collection.update_one(
                {"id": podcast_id}, {"$set": update_data}
            )

            if result.modified_count == 1:
                # --- Add activity log for podcast update ---
                try:
                    self.activity_service.log_activity(
                        user_id=user_id,
                        activity_type="podcast_updated",
                        description=f"Updated podcast '{podcast.get('podName', podcast_id)}'",
                        details={
                            "podcastId": podcast_id,
                            "updatedFields": list(update_data.keys()),
                        },
                    )
                except Exception as act_err:
                    logger.error(
                        f"Failed to log podcast_updated activity: {act_err}",
                        exc_info=True,
                    )
                # --- End activity log ---
                return {"message": "Podcast updated successfully"}, 200
            else:
                return {"message": "No changes made to the podcast"}, 200

        except ValueError as e:
            logger.error(
                f"ValueError in edit_podcast for user {user_id}, podcast {podcast_id}: {e}"
            )
            error_message = "Invalid data"
            details = None
            if e.args:  # Check if args exist
                error_message = str(e.args[0])
                if len(e.args) > 1:
                    if isinstance(e.args[1], dict): # Marshmallow errors
                        details = e.args[1]
                    else:
                        details = str(e.args[1])
            else: # No args, use string representation of e
                error_message = str(e)
            
            if details:
                return {"error": error_message, "details": details}, 400
            else:
                return {"error": error_message}, 400

        except Exception as e:
            logger.error(
                f"General Exception in edit_podcast for user {user_id}, podcast {podcast_id}: {e}",
                exc_info=True,
            )
            return {"error": "Failed to update podcast", "details": str(e)}, 500

    def fetch_rss_feed(self, rss_url):
        try:
            # Delegate RSS fetching to RSSService instance
            return self.rss_service.fetch_rss_feed(rss_url)
        except Exception as e:
            logger.error(
                "❌ ERROR fetching RSS feed via PodcastRepository: %s", e, exc_info=True
            )  # Added error log
            return {"error": f"Error fetching RSS feed: {str(e)}"}, 500

    # Delete podcast associated with user when user account is deleted
    def delete_by_user(self, user_id):
        try:
            accounts = list(collection.database.Accounts.find({"ownerId": user_id}))
            account_ids = [str(a.get("id", a["id"])) for a in accounts]
            result = self.collection.delete_many({"accountId": {"$in": account_ids}})
            logger.info(
                f"🧹 Deleted {result.deleted_count} podcasts for user {user_id}"
            )
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to delete podcasts: {e}", exc_info=True)
            return 0

    def addPodcastWithRss(self, user_id, rss_url):
        """
        Fetch RSS data using RSSService and add a podcast to the repository.
        """
        try:
            # Fetch RSS data using the instance
            rss_data, status_code = self.rss_service.fetch_rss_feed(rss_url)
            if status_code != 200:
                return {"error": "Failed to fetch RSS feed", "details": rss_data}, 400

            # Prepare data for add_podcast based on rss_data
            # This part needs to be adapted based on what add_podcast expects
            # and what rss_data provides. For example:
            podcast_data_for_add = {
                "podName": rss_data.get("title", "Untitled Podcast from RSS"),
                "rssFeed": rss_url,
                "description": rss_data.get("description"),
                "logoUrl": rss_data.get("imageUrl"),
                # Add other necessary fields extracted from rss_data
                # or default values as required by PodcastSchema
            }
            
            # Call existing add_podcast method
            return self.add_podcast(user_id, podcast_data_for_add)

        except Exception as e:
            logger.error("Error in addPodcastWithRss: %s", e, exc_info=True)
            return {"error": "Failed to add podcast with RSS", "details": str(e)}, 500

