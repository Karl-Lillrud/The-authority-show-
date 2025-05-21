from backend.services.subscriptionService import SubscriptionService
from backend.models.episodes import EpisodeSchema
from datetime import datetime, timezone, timedelta
from backend.database.mongo_connection import collection
import uuid
import logging
from backend.services.activity_service import ActivityService
from dateutil.parser import parse as parse_date
from backend.utils.subscription_access import PLAN_BENEFITS
import os
from backend.utils.blob_storage import upload_file_to_blob, download_blob_to_tempfile
from backend.services.audioToEpisodeService import AudioToEpisodeService  # Assuming this is where AudioToEpisodeService is defined

logger = logging.getLogger(__name__)


class EpisodeRepository:
    def __init__(self):
        self.collection = collection.database.Episodes
        self.accounts_collection = collection.database.Accounts
        self.subscription_service = SubscriptionService()
        self.activity_service = ActivityService()
        self.audio_service = AudioToEpisodeService()

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


    def update_episode(self, episode_id, user_id, data, audio_file=None):
        """Update an episode if it belongs to the user, including handling audio file uploads."""
        try:
            ep = self.collection.find_one({"_id": episode_id})
            if not ep:
                return {"error": "Episode not found"}, 404
            if ep["userid"] != str(user_id):
                return {"error": "Permission denied"}, 403

            # Initialize the schema for validation
            schema = EpisodeSchema(partial=True)
            validation_data = data.copy()

            # Remove file-related fields from validation (to be handled separately)
            file_related_fields = ["audioUrl", "fileSize", "fileType"]
            for field in file_related_fields:
                if field in validation_data:
                    del validation_data[field]

            # Validate duration if present
            if "duration" in validation_data and validation_data["duration"] is not None:
                try:
                    validation_data["duration"] = int(validation_data["duration"])
                except (ValueError, TypeError):
                    logger.warning(
                        f"Could not convert duration '{validation_data['duration']}' to int for validation."
                    )
                    del validation_data["duration"]

            # Validate the remaining data
            errors = schema.validate(validation_data)
            if errors:
                logger.error(
                    "Schema validation errors during update (excluding file fields): %s",
                    errors,
                )
                return {
                    "error": "Invalid data provided for update",
                    "details": errors,
                }, 400

            # Start building the fields to update in MongoDB
            update_fields = {"updated_at": datetime.now(timezone.utc)}

            # Define all possible fields that can be updated
            allowed_fields = [
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

            for field in allowed_fields:
                if field in data:
                    value = data[field]
                    if isinstance(value, str):
                        update_fields[field] = value.strip()
                    elif value == "":
                        update_fields[field] = None
                    else:
                        update_fields[field] = value

            if audio_file:
                try:
                    account_id = ep.get("accountId")
                    if not account_id:
                        logger.error(f"No accountId found for episode {episode_id}")
                        return {"error": "Account ID not found for episode"}, 500

                    podcast_id = ep.get("podcast_id")
                    if not podcast_id:
                        logger.error(f"No podcast_id found for episode {episode_id}")
                        return {"error": "Podcast ID not found for episode"}, 500

                    # Upload the audio file using AudioToEpisodeService
                    upload_result = self.audio_service.upload_episode_audio(
                        account_id=account_id,
                        podcast_id=podcast_id,
                        episode_id=episode_id,
                        audio_file=audio_file
                    )

                    if not upload_result or not upload_result.get("blob_url"):
                        logger.error(f"Failed to upload audio file for episode {episode_id}")
                        return {"error": "Failed to upload audio file"}, 500

                    # Update audio-related fields
                    update_fields["audioUrl"] = upload_result["blob_url"]
                    update_fields["fileSize"] = upload_result["file_size"]
                    update_fields["fileType"] = audio_file.content_type if hasattr(audio_file, 'content_type') else "audio/mpeg"

                    logger.info(
                        f"Audio file uploaded for episode {episode_id}: "
                        f"URL={upload_result['blob_url']}, Size={upload_result['file_size']} {upload_result.get('size_unit', '')}"
                    )
                except Exception as e:
                    logger.error(f"Error handling audio file upload for episode {episode_id}: {e}", exc_info=True)
                    return {"error": f"Failed to upload audio file: {str(e)}"}, 500

            # Ensure duration is correctly typed
            if "duration" in update_fields and update_fields["duration"] is not None:
                try:
                    update_fields["duration"] = int(update_fields["duration"])
                except (ValueError, TypeError):
                    logger.error(
                        f"Invalid duration value '{update_fields['duration']}' during final update prep. Removing from update."
                    )
                    del update_fields["duration"]
            elif "duration" in update_fields and update_fields["duration"] is None:
                update_fields["duration"] = None

            # Check if there's anything to update besides 'updated_at'
            if len(update_fields) <= 1:
                logger.info(
                    f"No valid fields to update for episode {episode_id} besides timestamp."
                )
                return {"message": "No valid changes detected"}, 200

            # Perform the MongoDB update
            logger.debug(
                f"Performing MongoDB update for {episode_id} with fields: {update_fields}"
            )
            result = self.collection.update_one(
                {"_id": episode_id}, {"$set": update_fields}
            )

            if result.matched_count == 0:
                logger.error(
                    f"Failed to find episode {episode_id} during MongoDB update operation."
                )
                return {"error": "Failed to update episode, document not found."}, 404
            if result.modified_count == 0 and result.matched_count == 1:
                logger.info(
                    f"Episode {episode_id} found but no fields were modified by the update operation."
                )

            # Fetch the updated document
            updated_ep = self.collection.find_one({"_id": episode_id})
            if updated_ep and "_id" in updated_ep:
                updated_ep["_id"] = str(updated_ep["_id"])

            # Determine the title for logging
            log_title = updated_ep.get("title", ep.get("title", "Unknown Title"))

            # Log activity
            try:
                self.activity_service.log_activity(
                    user_id=str(user_id),
                    activity_type="episode_updated",
                    description=f"Updated episode '{log_title}'",
                    details={
                        "episodeId": episode_id,
                        "title": log_title,
                        "updatedFields": [
                            k for k in update_fields.keys() if k != "updated_at"
                        ],
                    },
                )
            except Exception as act_err:
                logger.error(
                    f"Failed to log episode_updated activity: {act_err}", exc_info=True
                )

            return {"message": "Episode updated successfully"}, 200

        except Exception as e:
            logger.error(
                f"Failed to update episode {episode_id}: {str(e)}", exc_info=True
            )
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
