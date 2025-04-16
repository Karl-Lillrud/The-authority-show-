import uuid
from datetime import datetime, timezone
from backend.database.mongo_connection import collection
from backend.models.podcasts import PodcastSchema
import logging
import urllib.request
import feedparser
from backend.services.rss_Service import RSSService  # Import RSSService


logger = logging.getLogger(__name__)


class PodcastRepository:
    def __init__(self):
        self.collection = collection.database.Podcasts

    def add_podcast(self, user_id, data):
        try:
            # Add Logging Here
            logger.info(f"Attempting to add podcast for user_id: {user_id}")
            # Fetch the account document for the logged-in user
            user_account = collection.database.Accounts.find_one({"userId": user_id})

            # Add Logging Here
            if not user_account:
                logger.error(f"Account lookup failed for userId: {user_id}")
                # You might want to log the count of accounts for this user to see if any exist at all
                account_count = collection.database.Accounts.count_documents(
                    {"userId": user_id}
                )
                logger.error(
                    f"Total accounts found for userId {user_id}: {account_count}"
                )
                raise ValueError("No account associated with this user")
            else:
                logger.info(
                    f"Found account for userId {user_id}: Account _id: {user_account.get('_id')}"
                )

            # Get the account ID (use _id as primary)
            account_id = str(user_account["_id"])  # Prefer _id

            # Inject the accountId into the data
            data["accountId"] = account_id

            # Validate data using PodcastSchema
            schema = PodcastSchema()
            errors = schema.validate(data)
            if errors:
                raise ValueError("Invalid data", errors)

            validated_data = schema.load(data)

            # Ensure account exists and belongs to the user (redundant check, but safe)
            account = collection.database.Accounts.find_one(
                {"_id": account_id, "userId": user_id}
            )
            if not account:
                # This should ideally not happen if the first lookup succeeded
                logger.error(
                    f"Consistency check failed: Account _id {account_id} not found or doesn't belong to user {user_id}"
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

    def get_podcasts(self, user_id):
        try:
            user_accounts = list(
                collection.database.Accounts.find(
                    {"userId": user_id}, {"id": 1, "_id": 1}
                )
            )
            user_account_ids = [
                account.get("id", str(account["_id"])) for account in user_accounts
            ]

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
                    {"userId": user_id}, {"id": 1, "_id": 1}
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
                    {"userId": user_id}, {"id": 1, "_id": 1}
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
                    {"userId": user_id}, {"id": 1, "_id": 1}
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
            accounts = list(collection.database.Accounts.find({"userId": user_id}))
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
