from backend.services.subscriptionService import SubscriptionService
from backend.models.episodes import EpisodeSchema
from datetime import datetime, timezone, timedelta
from backend.database.mongo_connection import collection
import uuid
import logging
from backend.services.activity_service import ActivityService
from dateutil.parser import parse as parse_date
from backend.utils.subscription_access import PLAN_BENEFITS

logger = logging.getLogger(__name__)


class EpisodeRepository:
    def __init__(self):
        self.collection = collection.database.Episodes
        self.accounts_collection = collection.database.Accounts
        self.subscription_service = SubscriptionService()
        self.activity_service = ActivityService()

    @staticmethod
    def get_episodes_by_user_id(user_id):
        """Fetch episodes for a specific user."""
        return list(collection.Episodes.find({"ownerId": user_id}))

    def register_episode(self, data, user_id):
        try:
            user_account = self.accounts_collection.find_one({"ownerId": user_id})
            if not user_account:
                return {"error": "No account associated with this user"}, 403

            is_imported = data.get("isImported", False)
            if not is_imported:
                can_create, reason = self.subscription_service.can_create_episode(user_id)
                if not can_create:
                    return {"error": "Episode limit reached", "reason": reason}, 403

            account_id = user_account.get("id", str(user_account["_id"]))
            if 'accountId' not in data:
                data['accountId'] = account_id

            validated = data  

            episode_id = str(uuid.uuid4())
            episode_doc = {
                "_id": episode_id,
                "podcast_id": validated.get("podcastId"),
                "title": validated.get("title"),
                "description": validated.get("description"),
                "publishDate": validated.get("publishDate"),
                "duration": validated.get("duration"),
                "status": validated.get("status"),
                "userid": str(user_id),
                "accountId": account_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "audioUrl": validated.get("audioUrl"),
                "fileSize": validated.get("fileSize"),
                "fileType": validated.get("fileType"),
                "guid": validated.get("guid"),
                "season": validated.get("season"),
                "episode": validated.get("episode"),
                "episodeType": validated.get("episodeType"),
                "explicit": validated.get("explicit"),
                "imageUrl": validated.get("imageUrl"),
                "keywords": validated.get("keywords"),
                "chapters": validated.get("chapters"),
                "link": validated.get("link"),
                "subtitle": validated.get("subtitle"),
                "summary": validated.get("summary"),
                "author": validated.get("author"),
                "isHidden": validated.get("isHidden"),
                "recordingAt": validated.get("recordingAt"),
                "audioEdits": [],
                "isImported": is_imported,
            }

            # Insert the episode
            self.collection.insert_one(episode_doc)

            try:
                self.activity_service.log_activity(
                    user_id=str(user_id),
                    activity_type="episode_created",
                    description=f"Created episode '{episode_doc.get('title', '')}'",
                    details={
                        "episodeId": episode_id,
                        "podcastId": episode_doc.get("podcast_id", ""),
                        "title": episode_doc.get("title", ""),
                    },
                )
            except Exception as act_err:
                logger.error(f"Failed to log activity: {act_err}", exc_info=True)

            return {"message": "Episode registered successfully", "episode_id": episode_id}, 201

        except Exception as e:
            logger.error("❌ ERROR registering episode: %s", str(e))
            return {"error": f"Failed to register episode: {str(e)}"}, 500

    def get_episode(self, episode_id, user_id):
        """Get a single episode by its ID and user."""
        try:
            result = self.collection.find_one(
                {"_id": episode_id, "userid": str(user_id)}
            )
            if not result:
                return {"error": "Episode not found"}, 404
            return result, 200
        except Exception as e:
            return {"error": f"Failed to fetch episode: {str(e)}"}, 500

    def get_episodes(self, user_id):
        """Get all episodes created by the user."""
        try:
            results = list(self.collection.find({"userid": str(user_id)}))
            for ep in results:
                ep["_id"] = str(ep["_id"])
            return {"episodes": results}, 200
        except Exception as e:
            return {"error": f"Failed to fetch episodes: {str(e)}"}, 500

    def delete_episode(self, episode_id, user_id):
        """Delete an episode if it belongs to the user."""
        try:
            ep = self.collection.find_one({"_id": episode_id})
            if not ep:
                return {"error": "Episode not found"}, 404
            if ep["userid"] != str(user_id):
                return {"error": "Permission denied"}, 403

            episode_title = ep.get(
                "title", "Unknown Title"
            )  # Get title before deleting

            result = self.collection.delete_one({"_id": episode_id})
            if result.deleted_count == 1:
                try:
                    self.activity_service.log_activity(
                        user_id=str(user_id),
                        activity_type="episode_deleted",
                        description=f"Deleted episode '{episode_title}'",  # Use fetched title
                        details={
                            "episodeId": episode_id,
                            "title": episode_title,
                        },  # Include title in details
                    )
                except Exception as act_err:
                    logger.error(
                        f"Failed to log episode_deleted activity: {act_err}",
                        exc_info=True,
                    )
                return {"message": "Episode deleted successfully"}, 200
            return {"error": "Failed to delete episode"}, 500
        except Exception as e:
            return {"error": f"Failed to delete episode: {str(e)}"}, 500

    def update_episode(self, episode_id, user_id, data):
        """Update an episode if it belongs to the user."""
        try:
            ep = self.collection.find_one({"_id": episode_id})
            if not ep:
                return {"error": "Episode not found"}, 404
            if ep["userid"] != str(user_id):
                return {"error": "Permission denied"}, 403

            # Log the data being updated
            logger.debug(f"Updating episode {episode_id} for user {user_id} with data: {data}")

            # Perform the MongoDB update
            update_fields = {"updated_at": datetime.now(timezone.utc)}
            update_fields.update(data)  # Merge the provided data into the update fields

            result = self.collection.update_one(
                {"_id": episode_id}, {"$set": update_fields}
            )

            if result.matched_count == 0:
                logger.error(f"Failed to find episode {episode_id} during MongoDB update operation.")
                return {"error": "Failed to update episode, document not found."}, 404
            if result.modified_count == 0:
                logger.info(f"Episode {episode_id} found but no fields were modified by the update operation.")

            # Fetch the updated document to confirm changes
            updated_ep = self.collection.find_one({"_id": episode_id})
            if updated_ep and "_id" in updated_ep:
                updated_ep["_id"] = str(updated_ep["_id"])
                logger.debug(f"Updated episode {episode_id} status: {updated_ep.get('status')}")  # Log updated status

            return {"message": "Episode updated successfully", "episode": updated_ep}, 200

        except Exception as e:
            logger.error(f"Failed to update episode {episode_id}: {str(e)}", exc_info=True)
            return {"error": f"Failed to update episode: {str(e)}"}, 500

    def get_episodes_by_podcast(self, podcast_id, user_id):
        """Get all episodes under a specific podcast owned by the user."""
        try:
            episodes = list(
                self.collection.find({"podcast_id": podcast_id, "userid": str(user_id)})
            )
            for ep in episodes:
                ep["_id"] = str(ep["_id"])
            return {"episodes": episodes}, 200
        except Exception as e:
            logger.error("❌ ERROR: %s", e)
            return {"error": f"Failed to fetch episodes by podcast: {str(e)}"}, 500

    def delete_by_user(self, user_id):
        """Delete episodes associated with user when user account is deleted."""
        try:
            result = self.collection.delete_many({"userid": str(user_id)})
            logger.info(
                f"🧹 Deleted {result.deleted_count} episodes for user {user_id}"
            )
            return result.deleted_count
        except Exception as e:
            logger.error(f"❌ ERROR deleting episodes: {str(e)}")
            return {"error": f"Failed to delete episodes: {str(e)}"}, 500

    def get_episode_detail_with_podcast(self, episode_id):
        """Fetch an episode along with its associated podcast."""
        try:
            episode = self.collection.find_one({"_id": episode_id})
            if not episode:
                return None, None
            podcast = (
                collection.database.Podcasts.find_one(
                    {"_id": episode.get("podcast_id")}
                )
                or {}
            )
            return episode, podcast
        except Exception as e:
            logger.error(f"Failed to fetch episode with podcast: {str(e)}")
            return None, None

    def get_podcast_id_by_episode(self, episode_id: str) -> str:
        """
        Fetch the podcast ID for a given episode.
        Raises ValueError if not found.
        """
        doc = collection.database.Episodes.find_one(
            {"_id": episode_id}, {"podcast_id": 1}
        )
        if doc and "podcast_id" in doc:
            return doc["podcast_id"]
        raise ValueError(f"Podcast ID not found for episode {episode_id}")

    def delete_episodes_by_podcast(self, podcast_id):
        """Delete all episodes associated with a specific podcast."""
        try:
            result = self.collection.delete_many({"podcast_id": podcast_id})
            logger.info(
                f"Deleted {result.deleted_count} episodes for podcast {podcast_id}"
            )
            return {"message": f"Deleted {result.deleted_count} episodes"}, 200
        except Exception as e:
            logger.error(
                f"Failed to delete episodes for podcast {podcast_id}: {str(e)}"
            )
            return {"error": f"Failed to delete episodes: {str(e)}"}, 500

    def get_episodes_by_guest(self, guest_id):
        """Fetch all episodes associated with a specific guest."""
        try:
            episodes = list(self.collection.find({"guestId": guest_id}))
            for ep in episodes:
                ep["_id"] = str(ep["_id"])
            return {"episodes": episodes}, 200
        except Exception as e:
            logger.error(f"Failed to fetch episodes by guest {guest_id}: {str(e)}")
            return {"error": f"Failed to fetch episodes: {str(e)}"}, 500

    def count_episodes_by_guest(self, guest_id):
        """Count the number of episodes associated with a specific guest."""
        try:
            count = self.collection.count_documents({"guestId": guest_id})
            return {"count": count}, 200
        except Exception as e:
            logger.error(f"Failed to count episodes by guest {guest_id}: {str(e)}")
            return {"error": f"Failed to count episodes: {str(e)}"}, 500

    def add_tasks_to_episode(self, episode_id, guest_id, tasks):
        """Add tasks to an episode for a specific guest."""
        try:
            update_result = self.collection.update_one(
                {"_id": episode_id, "guestId": guest_id},
                {"$push": {"tasks": {"$each": tasks}}},
            )
            if update_result.modified_count == 1:
                return {"message": "Tasks added successfully"}, 200
            return {"error": "Failed to add tasks to episode"}, 500
        except Exception as e:
            logger.error(f"Failed to add tasks to episode {episode_id}: {str(e)}")
            return {"error": f"Failed to add tasks: {str(e)}"}, 500

    def view_tasks_by_episode(self, episode_id):
        """View tasks associated with a specific episode."""
        try:
            episode = self.collection.find_one({"_id": episode_id}, {"tasks": 1})
            if not episode:
                return {"error": "Episode not found"}, 404
            return {"tasks": episode.get("tasks", [])}, 200
        except Exception as e:
            logger.error(f"Failed to fetch tasks for episode {episode_id}: {str(e)}")
            return {"error": f"Failed to fetch tasks: {str(e)}"}, 500
