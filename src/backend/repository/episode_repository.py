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

            podcast_id = validated_data.get("podcastId")
            title = validated_data.get("title")

            # Validate required fields
            if not podcast_id or not title:
                return {"error": "Required fields missing: podcastId and title"}, 400

            episode_id = str(uuid.uuid4())

            episode_doc = {
                "_id": episode_id,
                "podcast_id": podcast_id,
                "title": title,
                "description": validated_data.get("description"),
                "publishDate": validated_data.get("publishDate"),
                "duration": validated_data.get("duration"),
                "status": validated_data.get("status"),
                "userid": user_id_str,
                "accountId": account_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "audioUrl": validated_data.get(
                    "audioUrl"
                ),  # Ensure audioUrl is included
                "fileSize": validated_data.get("fileSize"),
                "fileType": validated_data.get("fileType"),
                "guid": validated_data.get("guid"),
                "season": validated_data.get("season"),
                "episode": validated_data.get("episode"),  # Ensure episode is saved
                "episodeType": validated_data.get(
                    "episodeType"
                ),  # Ensure episodeType is saved
                "explicit": validated_data.get("explicit"),
                "imageUrl": validated_data.get("imageUrl"),
                "keywords": validated_data.get("keywords"),
                "chapters": validated_data.get("chapters"),
                "link": validated_data.get("link"),
                "subtitle": validated_data.get("subtitle"),
                "summary": validated_data.get("summary"),
                "author": validated_data.get("author"),
                "isHidden": validated_data.get("isHidden"),
                "category": validated_data.get("category"),  # Ensure category is saved
                "episodeFiles": data.get(
                    "episodeFiles", []
                ),  # Correctly handle optional episodeFiles field
            }

            result = self.collection.insert_one(episode_item)

            # Return success response
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

            # Debugging: Print episode_id and user_id
            print(
                f"Fetching episode with episode_id: {episode_id} for user_id: {user_id_str}"
            )

            # Fetch the episode using the string episode_id
            episode = self.collection.find_one(
                {"_id": episode_id, "userid": user_id_str}
            )

            if not episode:
                print(
                    f"Episode with episode_id: {episode_id} and user_id: {user_id_str} not found."
                )
                return {"error": "Episode not found"}, 404

            # Convert binary data to a base64 encoded string
            if "episodeFiles" in episode:
                for file in episode["episodeFiles"]:
                    if "data" in file:
                        file["data"] = base64.b64encode(file["data"]).decode("utf-8")

            return episode, 200

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

            update_fields = {
                "title": (
                    data.get("title", existing_episode["title"]).strip()
                    if data.get("title")
                    else existing_episode["title"]
                ),
                "description": (
                    data.get("description", existing_episode["description"]).strip()
                    if data.get("description")
                    else existing_episode["description"]
                ),
                "publishDate": data.get("publishDate", existing_episode["publishDate"]),
                "duration": data.get("duration", existing_episode["duration"]),
                "status": (
                    data.get("status", existing_episode["status"]).strip()
                    if data.get("status")
                    else existing_episode["status"]
                ),
                "audioUrl": data.get(
                    "audioUrl", existing_episode["audioUrl"]
                ),  # Ensure audioUrl is updated
                "updated_at": datetime.now(timezone.utc),
            }

            # Update the episode in the database
            result = self.collection.update_one(
                {"_id": episode_id}, {"$set": update_fields}
            )

            # Return the result of the update operation
            if result.modified_count == 1:
                return {"message": "Episode updated successfully"}, 200
            else:
                return {"message": "No changes made to the episode"}, 200

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
            return {"error": str(e)}, 500

    def get_episode_by_id(self, episode_id):
        """
        Get a single episode by ID without user validation
        """
        try:
            episode = self.collection.find_one({"_id": episode_id})
            if not episode:
                return None
            return episode
        except Exception as e:
            logger.error(f"❌ ERROR: {e}")
            return None
