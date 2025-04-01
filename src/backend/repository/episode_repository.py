from flask import request  # Add this import
from backend.database.mongo_connection import collection, database, get_fs
from datetime import datetime, timezone
import uuid
import logging
from backend.models.episodes import EpisodeSchema
from backend.services.spotify_integration import save_uploaded_files
import bson
import base64

logger = logging.getLogger(__name__)
fs = get_fs()


class EpisodeRepository:
    def __init__(self):
        self.collection = collection.database.Episodes
        self.accounts_collection = collection.database.Accounts

    def register_episode(self, data, user_id):
        """Register a new episode for the given user."""
        try:
            # Fetch the account document from MongoDB for the logged-in user
            user_account = self.accounts_collection.find_one({"userId": user_id})
            if not user_account:
                return {"error": "No account associated with this user"}, 403

            # Fetch the account ID that the user already has
            account_id = user_account.get("id", str(user_account["_id"]))
            logger.info(f"🧩 Found account {account_id} for user {user_id}")

            files = request.files.getlist(
                "episodeFiles"
            )  # Fetch files from the request
            if files:
                saved_files = save_uploaded_files(files)
                if not saved_files:  # Correctly indented inside the try block
                    logger.error("No files were saved to Cloudflare R2.")
                    return {"error": "Failed to save files. Please try again."}, 400

                data["episodeFiles"] = saved_files
                data["audioUrl"] = saved_files[0]["url"]  # Ensure audioUrl is set
                logger.info(f"Audio URL set to: {data['audioUrl']}")

            # Validate data with schema
            schema = EpisodeSchema()
            errors = schema.validate(data)
            if errors:
                logger.error("Schema validation errors: %s", errors)
                return {"error": "Invalid data", "details": errors}, 400
            validated_data = schema.load(data)

            validated = schema.load(data)
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
            }

            self.collection.insert_one(episode_doc)
            return {
                "message": "Episode registered successfully",
                "episode_id": episode_id,
            }, 201

        except Exception as e:
            logger.error("❌ ERROR registering episode: %s", str(e))
            return {"error": f"Failed to register episode: {str(e)}"}, 500

    def get_episode(self, episode_id, user_id):
        """
        Get a single episode by ID
        """
        try:
            user_id_str = str(user_id)

            result = self.collection.find_one(
                {"_id": episode_id, "userid": str(user_id)}
            )
            if not result:
                return {"error": "Episode not found"}, 404

            # Convert binary data to a base64 encoded string
            if "episodeFiles" in episode:
                for file in episode["episodeFiles"]:
                    if "data" in file:
                        file["data"] = base64.b64encode(file["data"]).decode("utf-8")

            return episode, 200

        except Exception as e:
            logger.error(f"Error fetching episode with ID {episode_id}: {e}")
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
                return {"message": "Episode deleted successfully"}, 200
            return {"error": "Failed to delete episode"}, 500
        except Exception as e:
            return {"error": f"Failed to delete episode: {str(e)}"}, 500

    def update_episode(self, episode_id, user_id, data):
        """Update an episode if it belongs to the user."""
        try:
            logger.info(f"Updating episode with ID: {episode_id} for user ID: {user_id}")
            ep = self.collection.find_one({"_id": episode_id})
            if not ep:
                logger.warning(f"Episode with ID {episode_id} not found.")
                return {"error": "Episode not found"}, 404
            if ep["userid"] != str(user_id):
                logger.warning(f"Permission denied for user ID {user_id} to update episode ID {episode_id}.")
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

            # Update the episode in the database
            result = self.collection.update_one({"_id": episode_id}, {"$set": update_fields})

            if result.modified_count == 1:
                logger.info(f"Episode with ID {episode_id} updated successfully.")
                return {"message": "Episode updated successfully"}, 200
            else:
                logger.info(f"No changes made to episode with ID {episode_id}.")
                return {"message": "No changes made to the episode"}, 200

        except Exception as e:
            logger.error(f"Error updating episode with ID {episode_id}: {e}")
            return {"error": f"Failed to update episode: {str(e)}"}, 500

    def get_episodes_by_podcast(self, podcast_id, user_id, return_with_status=False):
        """Get all episodes under a specific podcast owned by the user."""
        try:
            logger.info(f"Fetching episodes for podcast ID: {podcast_id} and user ID: {user_id}")
            episodes = list(
                self.collection.find({"podcast_id": podcast_id, "userid": str(user_id)})
            )

            for ep in episodes:
                ep["_id"] = str(ep["_id"])

            if not episodes:
                logger.warning(f"No episodes found for podcast ID {podcast_id}.")
            else:
                logger.info(f"Found {len(episodes)} episodes for podcast ID {podcast_id}.")

            if return_with_status:
                return {"episodes": episodes}, 200
            return episodes  # Return only the episodes list if status is not needed
        except Exception as e:
            logger.error(f"Error fetching episodes for podcast ID {podcast_id}: {e}")
            if return_with_status:
                return {"error": str(e)}, 500
            raise e  # Re-raise the exception for direct calls

    # Delete episodes associated with user when user account is deleted
    def delete_by_user(self, user_id):
        try:
            result = self.collection.delete_many({"userid": str(user_id)})
            logger.info(
                f"🧹 Deleted {result.deleted_count} episodes for user {user_id}"
            )
            return result.deleted_count
        except Exception as e:

            logger.error(
                f"❌ ERROR fetching episodes for podcast {podcast_id}: {str(e)}"
            )
            return {"error": f"Failed to fetch episodes: {str(e)}"}, 500

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
