from backend.database.mongo_connection import collection
from datetime import datetime, timezone
import uuid
import logging
from backend.models.guests import GuestSchema
from marshmallow import ValidationError
import email.utils  # Import to handle parsing date format

logger = logging.getLogger(__name__)


class GuestRepository:
    def __init__(self):
        self.collection = collection.database.Guests

    def add_guest(self, data, user_id):
        try:
            episode_id = data.get("episodeId")

            episode = collection.database.Episodes.find_one({"_id": episode_id})
            if not episode:
                return {"error": "Episode not found"}, 404

            current_date = datetime.now(timezone.utc)

            # Parse and make publish_date offset-aware
            try:
                publish_date_parsed = email.utils.parsedate(episode["publishDate"])
                publish_date = datetime(
                    *publish_date_parsed[:6]
                )  # Convert to datetime object
                publish_date = publish_date.replace(
                    tzinfo=timezone.utc
                )  # Make it offset-aware
            except Exception as e:
                return {"error": f"Invalid publish date format: {str(e)}"}, 400

            guest_data = GuestSchema().load(data)
            guest_id = str(uuid.uuid4())

            guest_item = {
                "_id": guest_id,
                "episodeId": episode_id,
                "name": guest_data["name"].strip(),
                "image": guest_data.get("image", ""),
                "tags": guest_data.get("tags", []),
                "description": guest_data.get("description", ""),
                "bio": guest_data.get("bio", guest_data.get("description", "")),
                "email": guest_data["email"].strip(),
                "linkedin": guest_data.get("linkedin", "").strip(),
                "twitter": guest_data.get("twitter", "").strip(),
                "areasOfInterest": guest_data.get("areasOfInterest", []),
                "status": "Pending",
                "scheduled": 0,
                "completed": 0,
                "created_at": datetime.now(timezone.utc),
                "user_id": user_id,
            }

            self.collection.insert_one(guest_item)

            return {"message": "Guest added successfully", "guest_id": guest_id}, 201

        except Exception as e:
            logger.exception("❌ ERROR: Failed to add guest")
            return {"error": f"Failed to add guest: {str(e)}"}, 500

    def get_guests(self, user_id):
        """
        Get all guests for a user
        """
        try:
            # Fetch guests for the logged-in user from the database
            guests_cursor = self.collection.find(
                {"user_id": user_id},
                {
                    "_id": 1,
                    "episodeId": 1,
                    "name": 1,
                    "image": 1,
                    "bio": 1,
                    "tags": 1,
                    "email": 1,
                    "linkedin": 1,
                    "twitter": 1,
                    "areasOfInterest": 1,
                },
            )

            # Prepare the guest list with necessary fields
            guest_list = []
            for guest in guests_cursor:
                guest_list.append(
                    {
                        "id": str(guest.get("_id")),
                        "episodeId": guest.get(
                            "episodeId", None
                        ),  # Default to None if episodeId is missing
                        "name": guest.get(
                            "name", "N/A"
                        ),  # Default to 'N/A' if name is missing
                        "image": guest.get(
                            "image", ""
                        ),  # Default to empty string if image is missing
                        "bio": guest.get("bio", ""),
                        "tags": guest.get("tags", []),
                        "email": guest.get("email", ""),
                        "linkedin": guest.get("linkedin", ""),
                        "twitter": guest.get("twitter", ""),
                        "areasOfInterest": guest.get("areasOfInterest", []),
                    }
                )

            # Return the list of guests with a success message
            return {"message": "Guests fetched successfully", "guests": guest_list}, 200

        except Exception as e:
            # Handle any errors during the database query or processing
            logger.exception("❌ ERROR: Failed to fetch guests")
            return {"error": f"An error occurred while fetching guests: {str(e)}"}, 500

    def edit_guest(self, guest_id, data, user_id):
        """
        Update a guest's information
        """
        try:
            logger.info("📩 Received Data: %s", data)

            if not guest_id:
                return {"error": "Guest ID is required"}, 400

            user_id_str = str(user_id)

            # Prepare update fields from the incoming request body
            update_fields = {
                "name": data.get("name", "").strip(),
                "image": data.get("image", "default-profile.png"),
                "tags": data.get("tags", []),
                "description": data.get("description", ""),
                "bio": data.get("bio", data.get("description", "")),
                "email": data.get("email", "").strip(),
                "linkedin": data.get("linkedin", "").strip(),
                "twitter": data.get("twitter", "").strip(),
                "areasOfInterest": data.get("areasOfInterest", []),
            }

            # If episodeId is provided, update the guest's episodeId
            episode_id = data.get("episodeId")
            if episode_id is not None:
                update_fields["episodeId"] = episode_id

            logger.info("📝 Update Fields: %s", update_fields)

            # Update the guest document based on guest_id and user_id to ensure the user can only edit their own guests
            result = self.collection.update_one(
                {"_id": guest_id, "user_id": user_id_str}, {"$set": update_fields}
            )

            if result.matched_count == 0:
                return {"error": "Guest not found or unauthorized"}, 404

            return {"message": "Guest updated successfully"}, 200

        except Exception as e:
            logger.exception("❌ ERROR: Failed to update guest")
            return {"error": f"Failed to update guest: {str(e)}"}, 500

    def delete_guest(self, guest_id, user_id):
        """
        Delete a guest by ID
        """
        try:
            user_id_str = str(user_id)
            # Use "user_id" to ensure proper matching
            result = self.collection.delete_one(
                {"_id": guest_id, "user_id": user_id_str}
            )
            if result.deleted_count == 0:
                return {"error": "Guest not found or unauthorized"}, 404

            return {"message": "Guest deleted successfully"}, 200

        except Exception as e:
            logger.exception("❌ ERROR: Failed to delete guest")
            return {"error": f"Failed to delete guest: {str(e)}"}, 500

    def get_guests_by_episode(self, episode_id):
        """
        Get all guests for a specific episode
        """
        try:
            # Fetch guests for the specific episode
            guests_cursor = self.collection.find({"episodeId": episode_id})
            guest_list = []
            for guest in guests_cursor:
                guest_list.append(
                    {
                        "id": str(guest.get("_id")),
                        "episodeId": guest.get("episodeId"),
                        "name": guest.get("name"),
                        "image": guest.get("image"),
                        "bio": guest.get("bio"),
                        "tags": guest.get("tags", []),
                        "email": guest.get("email"),
                        "linkedin": guest.get("linkedin"),
                        "twitter": guest.get("twitter"),
                        "areasOfInterest": guest.get("areasOfInterest", []),
                    }
                )

            if not guest_list:
                return {"message": "No guests found for this episode"}, 404

            return {"message": "Guests fetched successfully", "guests": guest_list}, 200

        except Exception as e:
            logger.exception("❌ ERROR: Failed to fetch guests for episode")
            return {"error": f"Failed to fetch guests: {str(e)}"}, 500

    def get_guest_by_id(self, user_id, guest_id):
        """
        Get a specific guest by ID
        """
        try:
            # Fetch guest for the logged-in user based on guest_id
            guest_cursor = self.collection.find_one(
                {"_id": guest_id, "user_id": user_id},
                {
                    "_id": 1,
                    "episodeId": 1,
                    "name": 1,
                    "image": 1,
                    "bio": 1,
                    "tags": 1,
                    "email": 1,
                    "linkedin": 1,
                    "twitter": 1,
                    "areasOfInterest": 1,
                },
            )

            if guest_cursor is None:
                return {"message": "Guest not found"}, 404

            guest = {
                "id": str(guest_cursor.get("_id")),
                "episodeId": guest_cursor.get("episodeId"),
                "name": guest_cursor.get("name", "N/A"),
                "image": guest_cursor.get("image", ""),
                "bio": guest_cursor.get("bio", ""),
                "tags": guest_cursor.get("tags", []),
                "email": guest_cursor.get("email", ""),
                "linkedin": guest_cursor.get("linkedin", ""),
                "twitter": guest_cursor.get("twitter", ""),
                "areasOfInterest": guest_cursor.get("areasOfInterest", []),
            }

            return {"message": "Guest fetched successfully", "guest": guest}, 200

        except Exception as e:
            logger.exception("❌ ERROR: Failed to fetch guest by ID")
            return {"error": f"An error occurred while fetching guest: {str(e)}"}, 500

    def get_episodes_by_guest(self, guest_id):
        """
        Get all episodes for a specific guest
        """
        try:
            # Fetch episodes for the specific guest
            episodes_cursor = self.collection.aggregate(
                [
                    {"$match": {"guests": guest_id}},  # Match episodes with this guest
                    {"$unwind": "$episodes"},
                    {
                        "$match": {"episodes.guests": guest_id}
                    },  # Match episodes with this guest
                    {
                        "$project": {
                            "_id": "$episodes._id",
                            "title": "$episodes.title",
                            "description": "$episodes.description",
                            "publish_date": "$episodes.publish_date",
                            "guests": "$episodes.guests",
                        }
                    },
                ]
            )

            episodes_list = []
            for episode in episodes_cursor:
                episodes_list.append(
                    {
                        "episode_id": str(episode["_id"]),
                        "title": episode["title"],
                        "description": episode["description"],
                        "publish_date": episode["publish_date"],
                        "guests": episode["guests"],
                    }
                )

            if not episodes_list:
                return {"message": "No episodes found for this guest"}, 404

            return {
                "message": "Episodes fetched successfully",
                "episodes": episodes_list,
            }, 200

        except Exception as e:
            logger.exception("❌ ERROR: Failed to fetch episodes by guest")
            return {"error": f"Failed to fetch episodes for guest: {str(e)}"}, 500

    # Delete guests associated with user when user account is deleted
    def delete_by_user(self, user_id):
        try:
            result = self.collection.delete_many({"user_id": str(user_id)})
            logger.info(f"🧹 Deleted {result.deleted_count} guests for user {user_id}")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to delete guests: {e}", exc_info=True)
            return 0
