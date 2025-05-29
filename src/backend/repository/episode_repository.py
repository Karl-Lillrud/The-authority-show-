from backend.services.subscriptionService import SubscriptionService
from backend.models.episodes import EpisodeSchema
from datetime import datetime, timezone, timedelta
from backend.database.mongo_connection import collection
import uuid
import logging
from backend.services.activity_service import ActivityService
from dateutil.parser import parse as parse_date
from backend.utils.subscription_access import PLAN_BENEFITS
from backend.services.audioToEpisodeService import AudioToEpisodeService # Added import

logger = logging.getLogger(__name__)


class EpisodeRepository:
    def __init__(self):
        self.collection = collection.database.Episodes
        self.accounts_collection = collection.database.Accounts
        self.subscription_service = SubscriptionService()
        self.activity_service = ActivityService()
        self.audio_service = AudioToEpisodeService() # Instantiate AudioToEpisodeService

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

    def update_episode(self, episode_id, user_id, data, audio_file=None): # Added audio_file=None
        """Update an episode if it belongs to the user."""
        try:
            ep = self.collection.find_one({"_id": episode_id})
            if not ep:
                return {"error": "Episode not found"}, 404
            if ep["userid"] != str(user_id):
                return {"error": "Permission denied"}, 403

            # Handle audio file upload first if provided
            if audio_file:
                account_id = ep.get("accountId") # Use accountId from the episode document
                podcast_id = ep.get("podcast_id")

                if not account_id or not podcast_id:
                    logger.error(f"Cannot process audio upload for episode {episode_id}: missing accountId or podcast_id in episode document.")
                    return {"error": "Internal configuration error: cannot determine path for audio upload."}, 500

                logger.info(f"Processing audio file upload for episode {episode_id}")
                audio_meta = self.audio_service.upload_episode_audio(account_id, episode_id, audio_file, podcast_id)

                if audio_meta:
                    data["audioUrl"] = audio_meta.get("blob_url")
                    data["fileSize"] = audio_meta.get("file_size_bytes") # Use file_size_bytes
                    data["fileType"] = audio_meta.get("file_type")       # Use file_type
                    data["duration"] = audio_meta.get("duration_seconds")
                    # Optionally update status if a new audio file is uploaded
                    data["status"] = data.get("status", "Recorded") # Update status, or keep if already set
                    logger.info(f"Audio metadata populated for episode {episode_id}: {data['audioUrl']}")
                else:
                    logger.error(f"Audio upload failed for episode {episode_id}.")
                    return {"error": "Failed to upload and process audio file."}, 500
            
            # Continue with schema validation and field updates
            schema = EpisodeSchema(partial=True)

            validation_data = data.copy()

            file_related_fields = ["audioUrl", "fileSize", "fileType"]
            for field in file_related_fields:
                if field in validation_data:
                    del validation_data[field]

            if (
                "duration" in validation_data
                and validation_data["duration"] is not None
            ):
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

            # Add debug logging for status field specifically
            if "status" in data:
                logger.info(f"Episode {episode_id} status update requested: '{data['status']}'")
            
            # Start building the fields to update in MongoDB
            update_fields = {"updated_at": datetime.now(timezone.utc)}

            # Define all possible fields that can be updated (including file fields)
            allowed_fields = [
                "title",
                "description",
                "publishDate",
                "duration",
                "status",
                "audioUrl",
                "fileSize",
                "fileType",  # File fields included here
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

            # Populate update_fields from the original 'data' dictionary
            for field in allowed_fields:
                if (
                    field in data
                ):  # Check against the original 'data' containing file info
                    value = data[field]
                    if isinstance(value, str):
                        update_fields[field] = value.strip()
                    elif value == "":
                        update_fields[field] = None
                    else:
                        update_fields[field] = value

            # Ensure duration is correctly typed (already handled partially, but double-check)
            if "duration" in update_fields and update_fields["duration"] is not None:
                try:
                    update_fields["duration"] = int(update_fields["duration"])
                except (ValueError, TypeError):
                    logger.error(
                        f"Invalid duration value '{update_fields['duration']}' during final update prep. Removing from update."
                    )
                    if (
                        "duration" in update_fields
                    ):  # Check if still exists before deleting
                        del update_fields["duration"]
            elif "duration" in update_fields and update_fields["duration"] is None:
                # Ensure it's explicitly None if it was an empty string or invalid
                update_fields["duration"] = None

            # Check if there's anything to update besides 'updated_at'
            if len(update_fields) <= 1:
                logger.info(
                    f"No valid fields to update for episode {episode_id} besides timestamp."
                )
                # Decide if this is an error or just means no changes were made
                # If only file fields were sent, this might be expected.
                # Let's proceed if file fields were the only change.
                has_non_timestamp_update = any(k != "updated_at" for k in update_fields)
                if not has_non_timestamp_update:
                    return {"message": "No valid changes detected"}, 200

            # Perform the MongoDB update with additional logging
            logger.info(f"Performing MongoDB update for {episode_id} with fields: {update_fields}")
            
            # Ensure status field is properly included
            if "status" in data:
                update_fields["status"] = data["status"]
                logger.info(f"Status field explicitly set to '{data['status']}' in update for episode {episode_id}")
            
            # Execute the update with priority on status field
            result = self.collection.update_one(
                {"_id": episode_id}, {"$set": update_fields}
            )

            if result.matched_count == 0:
                # Should not happen due to earlier check, but good safeguard
                logger.error(f"Failed to find episode {episode_id} during MongoDB update operation.")
                return {"error": "Failed to update episode, document not found."}, 404
            
            # Additional logging to confirm update
            if result.modified_count > 0:
                logger.info(f"Successfully modified {result.modified_count} document(s) for episode {episode_id}")
                
                # Double-check the update by fetching the document again
                updated_doc = self.collection.find_one({"_id": episode_id})
                if updated_doc:
                    logger.info(f"Episode {episode_id} after update - status: '{updated_doc.get('status')}'")
                    
                    # If status was part of the update, verify it matches
                    if "status" in data and updated_doc.get('status') != data['status']:
                        logger.warning(f"Status mismatch after update: expected '{data['status']}', got '{updated_doc.get('status')}'")
            else:
                logger.warning(f"Episode {episode_id} matched but not modified by update")
            
            # Fetch the updated document to return or confirm changes
            updated_ep = self.collection.find_one({"_id": episode_id})
            if updated_ep and "_id" in updated_ep:
                updated_ep["_id"] = str(updated_ep["_id"])

            # Determine the title to use in the log (new title if updated, otherwise old title)
            log_title = updated_ep.get("title", ep.get("title", "Unknown Title"))

            # Log activity
            try:
                self.activity_service.log_activity(
                    user_id=str(user_id),
                    activity_type="episode_updated",
                    description=f"Updated episode '{log_title}'",  # Use determined title
                    details={
                        "episodeId": episode_id,
                        "title": log_title,  # Include title in details
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

    def get_episodes_by_podcast(self, podcast_id, user_id, exclude_statuses=None):
        """Get all episodes under a specific podcast owned by the user.
           Optionally excludes episodes with statuses specified in exclude_statuses (case-insensitive).
        """
        try:
            query = {
                "podcast_id": podcast_id,
                "userid": str(user_id)
            }

            if exclude_statuses and isinstance(exclude_statuses, list) and len(exclude_statuses) > 0:
                if len(exclude_statuses) == 1:
                    query["status"] = {"$not": {"$regex": f"^{exclude_statuses[0].strip()}$", "$options": "i"}}
                elif len(exclude_statuses) > 1:
                    nor_conditions = []
                    for status_val in exclude_statuses:
                        if isinstance(status_val, str) and status_val.strip():
                            nor_conditions.append({"status": {"$regex": f"^{status_val.strip()}$", "$options": "i"}})
                    if nor_conditions:
                        query["$nor"] = nor_conditions
                        if "status" in query and len(exclude_statuses) > 1: 
                             del query["status"]
            
            episodes_cursor = self.collection.find(query)
            episodes = list(episodes_cursor) # Convert cursor to list to iterate multiple times if needed for logging
            
            # ADDED: Detailed logging of episodes found by the query
            if exclude_statuses: # Log only when filtering is active
                logger.info(f"--- Episodes found by query for podcast {podcast_id} (before _id conversion, with exclude_statuses: {exclude_statuses}) ---")
                if not episodes:
                    logger.info("No episodes matched the query.")
                for ep_doc_idx, ep_doc in enumerate(episodes):
                    logger.info(f"Episode [{ep_doc_idx}]: ID: {ep_doc.get('_id')}, Status: '{ep_doc.get('status')}', Title: '{ep_doc.get('title', 'N/A')}'")
                logger.info(f"--- End of raw episode list from DB ({len(episodes)} episodes) ---")
            
            processed_episodes = []
            for ep in episodes:
                ep["_id"] = str(ep["_id"])
                processed_episodes.append(ep)
            
            excluded_status_str = ", ".join(exclude_statuses) if exclude_statuses else "none"
            logger.info(f"Fetched {len(processed_episodes)} episodes for podcast {podcast_id} by user {user_id}, excluding statuses: [{excluded_status_str}]. Query: {query}")
            return {"episodes": processed_episodes}, 200
        except Exception as e:
            logger.error(f"❌ ERROR fetching episodes for podcast {podcast_id} (exclude_statuses: {exclude_statuses}): {str(e)}", exc_info=True)
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
