import uuid
from datetime import datetime, timezone
from backend.database.mongo_connection import collection
from backend.models.podcasts import PodcastSchema
import logging
import urllib.request
import feedparser
from backend.services.rss_Service import RSSService  # Import RSSService
from backend.services.activity_service import ActivityService  # Add this import
from bson import ObjectId
from backend.repository.episode_repository import (
    EpisodeRepository,
)  # Assuming EpisodeRepository exists


logger = logging.getLogger(__name__)


class PodcastRepository:
    def __init__(self):
        self.collection = collection.database.Podcasts
        self.activity_service = ActivityService()  # Add this line
        self.episode_repo = EpisodeRepository()  # Initialize EpisodeRepository

    def add_podcast(self, user_id, data):  # user_id here is the owner's ID
        try:
            logger.info(f"Attempting to add podcast for owner_id: {user_id}")
            # Fetch the account document for the logged-in user using ownerId
            user_account = collection.database.Accounts.find_one(
                {"ownerId": user_id}
            )  # Query by ownerId

            if not user_account:
                logger.error(f"Account lookup failed for ownerId: {user_id}")
                account_count = collection.database.Accounts.count_documents(
                    {"ownerId": user_id}
                )
                logger.error(
                    f"Total accounts found for ownerId {user_id}: {account_count}"
                )
                raise ValueError("No account associated with this user (owner)")
            else:
                logger.info(
                    f"Found account for ownerId {user_id}: Account _id: {user_account.get('_id')}"
                )

            account_id = str(user_account["_id"])
            data["accountId"] = account_id

            # Validate data using PodcastSchema
            schema = PodcastSchema()
            errors = schema.validate(data)
            if errors:
                raise ValueError("Invalid data", errors)

            validated_data = schema.load(data)

            # Ensure account exists and belongs to the user (redundant check, but safe)
            account = collection.database.Accounts.find_one(
                {"_id": account_id, "ownerId": user_id}
            )  # Check ownerId here too
            if not account:
                logger.error(
                    f"Consistency check failed: Account _id {account_id} not found or doesn't belong to owner {user_id}"
                )
                raise ValueError("Invalid account ID or no permission to add podcast.")

            # Generate a unique podcast ID
            podcast_id = str(uuid.uuid4())
            podcast_item = {
                "_id": podcast_id,
                "teamId": validated_data.get("teamId"),
                "accountId": account_id,
                "podName": validated_data.get("podName"),
                "ownerName": validated_data.get("ownerName"),
                "hostName": validated_data.get("hostName"),
                "rssFeed": validated_data.get("rssFeed"),
                "googleCal": validated_data.get("googleCal"),
                "podUrl": validated_data.get("podUrl"),
                "guestUrl": validated_data.get("guestUrl"),
                "socialMedia": validated_data.get("socialMedia", []),
                "email": validated_data.get("email"),
                "description": validated_data.get("description"),
                "logoUrl": validated_data.get("logoUrl"),
                "category": validated_data.get("category", ""),
                "created_at": datetime.now(timezone.utc),
                "title": validated_data.get("title", ""),
                "language": validated_data.get("language", ""),
                "author": validated_data.get("author", ""),
                "copyright_info": validated_data.get("copyright_info", ""),
                "bannerUrl": validated_data.get("bannerUrl", ""),
                "tagline": validated_data.get("tagline", ""),
                "hostBio": validated_data.get("hostBio", ""),
                "hostImage": validated_data.get("hostImage", ""),
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
                        f"Failed to log podcast_created activity: {act_err}",
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
            )  # Log the specific error
            if isinstance(e.args[0], str):
                return {"error": e.args[0]}, 400
            else:
                return {"error": e.args[0], "details": e.args[1]}, 400

        except Exception as e:
            logger.error(
                f"General Exception in add_podcast for user {user_id}: {e}",
                exc_info=True,
            )  # Log general errors
            return {"error": "Failed to add podcast", "details": str(e)}, 500

    def get_podcasts(self, user_id):  # user_id is the owner's ID
        try:
            # Find accounts owned by the user
            user_accounts = list(
                collection.database.Accounts.find({"ownerId": user_id}, {"_id": 1})
            )  # Query by ownerId
            user_account_ids = [str(account["_id"]) for account in user_accounts]

            if not user_account_ids:
                return {"podcast": []}, 200  # No podcasts if no accounts

            podcasts = list(
                self.collection.find({"accountId": {"$in": user_account_ids}})
            )
            for podcast in podcasts:
                podcast["_id"] = str(podcast["_id"])

            return {"podcast": podcasts}, 200

        except Exception as e:
            return {"error": "Failed to fetch podcasts", "details": str(e)}, 500

    def get_podcast_by_id(self, user_id, podcast_id):
        try:
            user_accounts = list(
                collection.database.Accounts.find(
                    {"ownerId": user_id}, {"id": 1, "_id": 1}
                )
            )
            user_account_ids = [
                account.get("id", str(account["_id"])) for account in user_accounts
            ]

            if not user_account_ids:
                return {"error": "No accounts found for user"}, 403

            podcast = self.collection.find_one(
                {"_id": podcast_id, "accountId": {"$in": user_account_ids}}
            )
            if not podcast:
                return {"error": "Podcast not found or unauthorized"}, 404

            podcast["_id"] = str(podcast["_id"])
            return {"podcast": podcast}, 200
        except Exception as e:
            return {"error": f"Failed to fetch podcast: {str(e)}"}, 500

    def delete_podcast(self, user_id, podcast_id):
        try:
            # Fetch user account IDs
            user_accounts = list(
                collection.database.Accounts.find(
                    {"ownerId": user_id}, {"id": 1, "_id": 1}
                )
            )
            user_account_ids = [
                account.get("id", str(account["_id"])) for account in user_accounts
            ]

            if not user_account_ids:
                raise ValueError("No accounts found for user")

            # Find podcast by podcast_id and accountId
            podcast = self.collection.find_one(
                {"_id": podcast_id, "accountId": {"$in": user_account_ids}}
            )
            if not podcast:
                raise ValueError("Podcast not found or unauthorized")

            # Perform delete operation
            result = self.collection.delete_one({"_id": podcast_id})
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
                    {"ownerId": user_id}, {"id": 1, "_id": 1}
                )
            )
            user_account_ids = [
                account.get("id", str(account["_id"])) for account in user_accounts
            ]

            if not user_account_ids:
                raise ValueError("No accounts found for user")

            # Find podcast by podcast_id and accountId
            podcast = self.collection.find_one(
                {"_id": podcast_id, "accountId": {"$in": user_account_ids}}
            )
            if not podcast:
                raise ValueError("Podcast not found or unauthorized")

            # Validate input data using schema
            schema = PodcastSchema(partial=True)
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
                {"_id": podcast_id}, {"$set": update_data}
            )

            if result.modified_count == 1:
                return {"message": "Podcast updated successfully"}, 200
            else:
                return {"message": "No changes made to the podcast"}, 200

        except ValueError as e:
            # Specific business logic error
            if isinstance(e.args[0], str):
                return {
                    "error": e.args[0]
                }, 400  # Return specific error with 400 for bad input
            else:
                return {
                    "error": e.args[0],
                    "details": e.args[1],
                }, 400  # For validation errors

        except Exception as e:
            return {"error": "Failed to update podcast", "details": str(e)}, 500

    def fetch_rss_feed(self, rss_url):
        try:
            # Delegate RSS fetching to RSSService
            return RSSService.fetch_rss_feed(rss_url)
        except Exception as e:
            logger.error(
                "❌ ERROR fetching RSS feed: %s", e, exc_info=True
            )  # Added error log
            return {"error": f"Error fetching RSS feed: {str(e)}"}, 500

    # Delete podcast associated with user when user account is deleted
    def delete_by_user(self, user_id):
        try:
            accounts = list(collection.database.Accounts.find({"ownerId": user_id}))
            account_ids = [str(a.get("id", a["_id"])) for a in accounts]
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
            # Fetch RSS data
            rss_data, status_code = RSSService.fetch_rss_feed(rss_url)
            if status_code != 200:
                return {"error": "Failed to fetch RSS feed", "details": rss_data}, 400

            # Call existing add_podcast method
            return self.add_podcast(user_id)

        except Exception as e:
            logger.error("Error in addPodcastWithRss: %s", e, exc_info=True)
            return {"error": "Failed to add podcast with RSS", "details": str(e)}, 500

    def create_podcast(self, data):
        """
        Creates a new podcast document in the database.
        Handles data potentially coming from RSS feed parsing during activation.
        """
        try:
            user_id = data.get("userId")
            if not user_id:
                return {"error": "Missing userId"}, 400

            # Check for existing podcast with the same RSS URL for this user? Optional.
            # existing = self.podcast_collection.find_one({"userId": user_id, "rssUrl": data.get("rssUrl")})
            # if existing:
            #     return {"message": "Podcast already exists for this user", "podcast": existing}, 200

            podcast_doc = {
                "_id": str(ObjectId()),
                "userId": user_id,
                "title": data.get("title", "Untitled Podcast"),
                "description": data.get("description", ""),
                "rssUrl": data.get("rssUrl"),
                "websiteUrl": data.get("websiteUrl"),
                "artworkUrl": data.get("artworkUrl"),
                "language": data.get("language"),
                "author": data.get("author"),
                "ownerName": data.get("ownerName"),
                "ownerEmail": data.get("ownerEmail"),
                "categories": data.get("categories", []),
                "isImported": data.get(
                    "isImported", False
                ),  # Mark if imported via activation/RSS
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat(),
                "isActive": True,
                # Add other relevant fields from your schema
            }

            result = self.podcast_collection.insert_one(podcast_doc)
            if not result.inserted_id:
                logger.error(
                    f"Failed to insert podcast for user {user_id}, RSS: {data.get('rssUrl')}"
                )
                return {"error": "Database error creating podcast"}, 500

            logger.info(f"Podcast created: {podcast_doc['_id']} for user {user_id}")

            # --- Import Episodes if provided ---
            episodes_to_import = data.get("episodes", [])
            if episodes_to_import and isinstance(episodes_to_import, list):
                logger.info(
                    f"Importing {len(episodes_to_import)} episodes for podcast {podcast_doc['_id']}"
                )
                # Adapt episode data structure if needed for episode_repo.create_episode
                imported_count = 0
                failed_count = 0
                for episode_data in episodes_to_import:
                    # Add podcastId and userId to episode data
                    episode_data["podcastId"] = podcast_doc["_id"]
                    episode_data["userId"] = user_id
                    episode_data["isImported"] = True  # Mark episode as imported

                    # Call episode repository to create/import the episode
                    # Assuming create_episode handles potential duplicates based on GUID?
                    ep_result, ep_status = self.episode_repo.create_episode(
                        episode_data
                    )
                    if ep_status in [200, 201]:
                        imported_count += 1
                    else:
                        failed_count += 1
                        logger.warning(
                            f"Failed to import episode '{episode_data.get('title')}' for podcast {podcast_doc['_id']} : {ep_result.get('error')}"
                        )

                logger.info(
                    f"Episode import for podcast {podcast_doc['_id']}: {imported_count} succeeded, {failed_count} failed."
                )
            # --- End Episode Import ---

            # Return the created podcast document (or just relevant info)
            # Fetch the inserted doc to ensure all defaults/DB operations are reflected
            created_podcast = self.podcast_collection.find_one(
                {"_id": podcast_doc["_id"]}
            )
            return {
                "message": "Podcast created successfully",
                "podcast": created_podcast,
            }, 201

        except Exception as e:
            logger.error(f"Error creating podcast: {e}", exc_info=True)
            return {"error": f"Internal server error: {str(e)}"}, 500
