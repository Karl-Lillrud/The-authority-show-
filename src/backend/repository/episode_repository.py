from backend.services.subscriptionService import SubscriptionService
from datetime import datetime, timezone
from backend.database.mongo_connection import collection
import uuid
import logging
from backend.models.episodes import EpisodeSchema
from backend.services.activity_service import ActivityService

logger = logging.getLogger(__name__)


class EpisodeRepository:
    def __init__(self):
        self.collection = collection.database.Episodes
        self.accounts_collection = collection.database.Accounts
        self.activity_service = ActivityService()
        self.subscription_service = SubscriptionService()

    def register_episode(self, data, user_id):
        """Register a new episode for the given user."""
        try:
            user_account = self.accounts_collection.find_one({"ownerId": user_id})
            if not user_account:
                return {"error": "No account associated with this user"}, 403

            logger.debug(f"📥 Raw incoming data to register_episode: {data}")

            # ✅ Always set is_imported = True if the source is RSS
            is_imported = False
            if data.get("source") == "rss":
                is_imported = True
                data["isImported"] = True  # ✅ Force into payload
            elif "isImported" in data:
                is_imported = data["isImported"]

            if isinstance(is_imported, str):
                is_imported = is_imported.lower() == "true"

            logger.info(f"🧪 is_imported interpreted as: {is_imported} for user {user_id}")
            logger.info(f"🔍 Checking if user {user_id} can create episode with is_imported={is_imported}")

            can_create, reason = self.subscription_service.can_create_episode(user_id, is_imported=is_imported)
            if not can_create:
                return {"error": "Episode limit reached", "reason": reason}, 403

            account_id = user_account.get("id", str(user_account["_id"]))
            schema = EpisodeSchema()
            errors = schema.validate(data)
            if errors:
                logger.error("Schema validation errors: %s", errors)
                return {"error": "Invalid data", "details": errors}, 400

            validated = schema.load(data)
            validated["isImported"] = is_imported  # 🔐 Final overwrite

            episode_id = str(uuid.uuid4())

            episode_doc = {
                **validated,
                "_id": episode_id,
                "userid": str(user_id),
                "accountId": account_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }

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
                logger.error(f"Failed to log episode_created activity: {act_err}", exc_info=True)

            return {
                "message": "Episode registered successfully",
                "episode_id": episode_id,
            }, 201

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

            result = self.collection.delete_one({"_id": episode_id})
            if result.deleted_count == 1:
                # --- Log activity for episode deleted ---
                try:
                    self.activity_service.log_activity(
                        user_id=str(user_id),
                        activity_type="episode_deleted",
                        description=f"Deleted episode '{ep.get('title', '')}'",
                        details={"episodeId": episode_id, "title": ep.get("title", "")},
                    )
                except Exception as act_err:
                    logger.error(
                        f"Failed to log episode_deleted activity: {act_err}",
                        exc_info=True,
                    )
                # --- End activity log ---
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

            # Validate data with schema
            schema = EpisodeSchema(partial=True)  # partial=True allows partial updates
            errors = schema.validate(data)
            if errors:
                logger.error("Schema validation errors: %s", errors)
                return {"error": "Invalid data", "details": errors}, 400

            # Create update fields dictionary
            update_fields = {
                "title": data.get("title", ep["title"]),
                "description": data.get("description", ep["description"]),
                "publishDate": data.get("publishDate", ep.get("publishDate")),
                "duration": data.get("duration", ep.get("duration")),
                "status": data.get("status", ep.get("status")),
                "updated_at": datetime.now(timezone.utc),
            }

            # Add all fields from data that are not None
            fields_to_update = [
                "title",
                "description",
                "publishDate",
                "duration",
                "status",
                "audioUrl",
                "fileSize",
                "fileType",
                "guid",
                "season",
                "episode",
                "episodeType",
                "explicit",
                "imageUrl",
                "keywords",
                "chapters",
                "link",
                "subtitle",
                "summary",
                "author",
                "isHidden",
                "recordingAt",
            ]

            for field in fields_to_update:
                if field in data and data[field] is not None:
                    # Strip string values
                    if isinstance(data[field], str):
                        update_fields[field] = data[field].strip()
                    else:
                        update_fields[field] = data[field]

            self.collection.update_one({"_id": episode_id}, {"$set": update_fields})

            # --- Log activity for episode updated ---
            try:
                self.activity_service.log_activity(
                    user_id=str(user_id),
                    activity_type="episode_updated",
                    description=f"Updated episode '{ep.get('title', '')}'",
                    details={"episodeId": episode_id, "title": ep.get("title", "")},
                )
            except Exception as act_err:
                logger.error(
                    f"Failed to log episode_updated activity: {act_err}",
                    exc_info=True,
                )
            # --- End activity log ---

            return {"message": "Episode updated"}, 200

        except Exception as e:

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

    # Delete episodes associated with user when user account is deleted
    def delete_by_user(self, user_id):
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
