from backend.database.mongo_connection import collection
from datetime import datetime, timezone
import uuid
import logging
from backend.models.episodes import EpisodeSchema

logger = logging.getLogger(__name__)


class EpisodeRepository:
    def __init__(self):
        self.collection = collection.database.Episodes
        self.accounts_collection = collection.database.Accounts

    def add_episode(self, data, user_id):
        """
        Register a new episode in the database
        """
        try:
            # Fetch the account document from MongoDB for the logged-in user
            user_account = self.accounts_collection.find_one({"userId": user_id})
            if not user_account:
                return {"error": "No account associated with this user"}, 403

            # Fetch the account ID that the user already has
            if "id" in user_account:
                account_id = user_account["id"]
            else:
                account_id = str(user_account["_id"])
            logger.info(f"🧩 Found account {account_id} for user {user_id}")

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
            user_id_str = str(user_id)

            # Construct the episode document with the handled values
            episode_item = {
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
                "audioUrl": validated_data.get("audioUrl"),
                "fileSize": validated_data.get("fileSize"),
                "fileType": validated_data.get("fileType"),
                "guid": validated_data.get("guid"),
                "season": validated_data.get("season"),
                "episode": validated_data.get("episode"),
                "episodeType": validated_data.get("episodeType"),
                "explicit": validated_data.get("explicit"),
                "imageUrl": validated_data.get("imageUrl"),
                "keywords": validated_data.get("keywords"),
                "chapters": validated_data.get("chapters"),
                "link": validated_data.get("link"),
                "subtitle": validated_data.get("subtitle"),
                "summary": validated_data.get("summary"),
                "author": validated_data.get("author"),
                "isHidden": validated_data.get("isHidden"),
            }

            result = self.collection.insert_one(episode_item)

            # Return success response
            return {
                "message": "Episode registered successfully",
                "episode_id": episode_id,
            }, 201

        except Exception as e:
            logger.error("❌ ERROR: %s", e)
            return {"error": f"Failed to register episode: {str(e)}"}, 500

    def get_episode(self, episode_id, user_id):
        """
        Get a single episode by ID
        """
        try:
            user_id_str = str(user_id)
            
            # Log the request
            logger.info(f"Fetching episode with episode_id: {episode_id} for user_id: {user_id_str}")

            # Fetch the episode using the string episode_id
            episode = self.collection.find_one(
                {"_id": episode_id, "userid": user_id_str}
            )

            if not episode:
                logger.info(f"Episode with episode_id: {episode_id} and user_id: {user_id_str} not found")
                return {"error": "Episode not found"}, 404

            # Convert _id to string
            episode["_id"] = str(episode["_id"])
            
            return {"episode": episode}, 200

        except Exception as e:
            logger.error("❌ ERROR: %s", e)
            return {"error": f"Failed to fetch episode: {str(e)}"}, 500

    def get_episodes(self, user_id):
        """
        Get all episodes for a user
        """
        try:
            user_id_str = str(user_id)
            episodes = list(self.collection.find({"userid": user_id_str}))

            for episode in episodes:
                episode["_id"] = str(episode["_id"])

            return {"episodes": episodes}, 200

        except Exception as e:
            logger.error("❌ ERROR: %s", e)
            return {"error": f"Failed to fetch episodes: {str(e)}"}, 500

    def delete_episode(self, episode_id, user_id):
        """
        Delete an episode by ID
        """
        try:
            user_id_str = str(user_id)
            episode = self.collection.find_one({"_id": episode_id})

            if not episode:
                return {"error": "Episode not found"}, 404

            if episode["userid"] != user_id_str:
                return {"error": "Permission denied"}, 403

            result = self.collection.delete_one({"_id": episode_id})

            if result.deleted_count == 1:
                return {"message": "Episode deleted successfully"}, 200
            else:
                return {"error": "Failed to delete episode"}, 500

        except Exception as e:
            logger.error("❌ ERROR: %s", e)
            return {"error": f"Failed to delete episode: {str(e)}"}, 500

    def update_episode(self, episode_id, user_id, data):
        """
        Update an episode by ID
        """
        try:
            user_id_str = str(user_id)

            # Check if episode exists and user has permission
            existing_episode = self.collection.find_one({"_id": episode_id})
            if not existing_episode:
                return {"error": "Episode not found"}, 404

            if existing_episode["userid"] != user_id_str:
                return {"error": "Permission denied"}, 403
                
            # Validate data with schema
            schema = EpisodeSchema(partial=True)  # partial=True allows partial updates
            errors = schema.validate(data)
            if errors:
                logger.error("Schema validation errors: %s", errors)
                return {"error": "Invalid data", "details": errors}, 400
                
            # Create update fields dictionary
            update_fields = {
                "updated_at": datetime.now(timezone.utc),
            }
            
            # Add all fields from data that are not None
            fields_to_update = [
                "title", "description", "publishDate", "duration", "status",
                "audioUrl", "fileSize", "fileType", "guid", "season", "episode", 
                "episodeType", "explicit", "imageUrl", "keywords", "chapters", 
                "link", "subtitle", "summary", "author", "isHidden"
            ]
            
            for field in fields_to_update:
                if field in data and data[field] is not None:
                    # Strip string values
                    if isinstance(data[field], str):
                        update_fields[field] = data[field].strip()
                    else:
                        update_fields[field] = data[field]

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
            logger.error("❌ ERROR: %s", e)
            return {"error": f"Failed to update episode: {str(e)}"}, 500

    def get_episodes_by_podcast(self, podcast_id, user_id):
        """
        Get episodes by podcast ID
        """
        try:
            user_id_str = str(user_id)
            episodes = list(
                self.collection.find({"podcast_id": podcast_id, "userid": user_id_str})
            )
            
            for episode in episodes:
                episode["_id"] = str(episode["_id"])
                
            return {"episodes": episodes}, 200
            
        except Exception as e:
            logger.error("❌ ERROR: %s", e)
            return {"error": f"Failed to fetch episodes by podcast: {str(e)}"}, 500

    # Delete episodes associated with user when user account is deleted
    def delete_by_user(self, user_id):
        try:
            result = self.collection.delete_many({"userid": str(user_id)})
            logger.info(f"🧹 Deleted {result.deleted_count} episodes for user {user_id}")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to delete episodes: {e}", exc_info=True)
            return 0
