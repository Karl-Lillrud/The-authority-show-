import uuid
from datetime import datetime, timezone
from backend.database.mongo_connection import collection
from backend.models.podcasts import PodcastSchema
import logging
from backend.services.rss_Service import RSSService
from backend.services.activity_service import ActivityService
from backend.repository.episode_repository import EpisodeRepository

logger = logging.getLogger(__name__)


class PodcastRepository:
    def __init__(self):
        self.collection = collection.database.Podcasts
        self.activity_service = ActivityService()
        self.episode_repository = EpisodeRepository()

    def add_podcast(self, user_id, data):
        """Add a podcast for the user."""
        try:
            logger.info(f"Attempting to add podcast for owner_id: {user_id}")
            user_account = collection.database.Accounts.find_one({"ownerId": user_id})

            if not user_account:
                logger.error(f"Account lookup failed for ownerId: {user_id}")
                account_count = collection.database.Accounts.count_documents(
                    {"ownerId": user_id}
                )
                logger.error(
                    f"Total accounts found for ownerId {user_id}: {account_count}"
                )
                raise ValueError("No account associated with this user (owner)")

            account_id = str(user_account["_id"])
            data["accountId"] = account_id

            schema = PodcastSchema()
            errors = schema.validate(data)
            if errors:
                raise ValueError("Invalid data", errors)

            validated_data = schema.load(data)

            account = collection.database.Accounts.find_one(
                {"_id": account_id, "ownerId": user_id}
            )
            if not account:
                logger.error(
                    f"Consistency check failed: Account _id {account_id} not found or doesn't belong to owner {user_id}"
                )
                raise ValueError("Invalid account ID or no permission to add podcast.")

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

            result = self.collection.insert_one(podcast_item)
            if result.inserted_id:
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

                return {
                    "message": "Podcast added successfully",
                    "podcast_id": podcast_id,
                    "redirect_url": "/index.html",
                }, 201
            else:
                raise ValueError("Failed to add podcast.")

        except ValueError as e:
            logger.error(f"ValueError in add_podcast for user {user_id}: {e}")
            if isinstance(e.args[0], str):
                return {"error": e.args[0]}, 400
            else:
                return {"error": e.args[0], "details": e.args[1]}, 400

        except Exception as e:
            logger.error(
                f"General Exception in add_podcast for user {user_id}: {e}",
                exc_info=True,
            )
            return {"error": "Failed to add podcast", "details": str(e)}, 500

    def get_podcasts(self, user_id):
        """Get all podcasts for the user."""
        try:
            user_accounts = list(
                collection.database.Accounts.find({"ownerId": user_id}, {"_id": 1})
            )
            user_account_ids = [str(account["_id"]) for account in user_accounts]

            if not user_account_ids:
                return {"podcast": []}, 200

            podcasts = list(
                self.collection.find({"accountId": {"$in": user_account_ids}})
            )
            for podcast in podcasts:
                podcast["_id"] = str(podcast["_id"])

            return {"podcast": podcasts}, 200

        except Exception as e:
            return {"error": "Failed to fetch podcasts", "details": str(e)}, 500

    def get_podcast_by_id(self, user_id, podcast_id):
        """Get a specific podcast by ID."""
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
        """Delete a podcast and its associated episodes."""
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
                raise ValueError("No accounts found for user")

            podcast = self.collection.find_one(
                {"_id": podcast_id, "accountId": {"$in": user_account_ids}}
            )
            if not podcast:
                raise ValueError("Podcast not found or unauthorized")

            result = self.collection.delete_one({"_id": podcast_id})
            if result.deleted_count == 1:
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

                # Delete associated episodes
                episode_result = self.episode_repository.delete_episodes_by_podcast(
                    podcast_id
                )
                if episode_result.get("error"):
                    return episode_result

                return {
                    "message": "Podcast and associated episodes deleted successfully"
                }, 200
            else:
                return {"error": "Failed to delete podcast"}, 500

        except ValueError as e:
            return {"error": str(e)}, 400

        except Exception as e:
            return {"error": "Failed to delete podcast", "details": str(e)}, 500

    def edit_podcast(self, user_id, podcast_id, data):
        """Edit a podcast if it belongs to the user."""
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
                raise ValueError("No accounts found for user")

            podcast = self.collection.find_one(
                {"_id": podcast_id, "accountId": {"$in": user_account_ids}}
            )
            if not podcast:
                raise ValueError("Podcast not found or unauthorized")

            schema = PodcastSchema(partial=True)
            errors = schema.validate(data)
            if errors:
                raise ValueError("Invalid data", errors)

            update_data = {
                key: value for key, value in data.items() if value is not None
            }
            if not update_data:
                return {"message": "No update data provided"}, 200

            result = self.collection.update_one(
                {"_id": podcast_id}, {"$set": update_data}
            )

            if result.modified_count == 1:
                return {"message": "Podcast updated successfully"}, 200
            else:
                return {"message": "No changes made to the podcast"}, 200

        except ValueError as e:
            if isinstance(e.args[0], str):
                return {"error": e.args[0]}, 400
            else:
                return {"error": e.args[0], "details": e.args[1]}, 400

        except Exception as e:
            return {"error": "Failed to update podcast", "details": str(e)}, 500

    def fetch_rss_feed(self, rss_url):
        """Fetch RSS feed using RSSService."""
        try:
            return RSSService.fetch_rss_feed(rss_url)
        except Exception as e:
            logger.error("❌ ERROR fetching RSS feed: %s", e, exc_info=True)
            return {"error": f"Error fetching RSS feed: {str(e)}"}, 500

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

    def delete_by_user(self, user_id):
        """Delete podcasts associated with user when user account is deleted."""
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
