from backend.database.mongo_connection import collection
from datetime import datetime, timezone
import uuid
import logging
from backend.models.guests import GuestSchema
from marshmallow import ValidationError

logger = logging.getLogger(__name__)

class GuestRepository:
    def __init__(self):
        self.collection = collection.database.Guests

    def add_guest(self, data, user_id):
        """
        Add a new guest to the database
        """
        try:
            logger.info("📩 Received guest data: %s", data)

            # Validate guest data
            try:
                guest_data = GuestSchema().load(data)
            except ValidationError as err:
                logger.error("Validation error: %s", err.messages)
                return {"error": "Validation error", "details": err.messages}, 400

            guest_id = str(uuid.uuid4())

            # Get the episodeId if provided
            episode_id = data.get("episodeId")

            # Construct guest document
            guest_item = {
                "_id": guest_id,
                "episodeId": episode_id,  # Link to the episode if provided
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
                "user_id": user_id,  # Storing the logged-in user ID
            }

            # Insert guest into the database
            self.collection.insert_one(guest_item)
            logger.info("✅ Guest added successfully with ID: %s", guest_id)

            return {
                "message": "Guest added successfully", 
                "guest_id": guest_id
            }, 201

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
                        "episodeId": guest.get("episodeId", None),  # Default to None if episodeId is missing
                        "name": guest.get("name", "N/A"),  # Default to 'N/A' if name is missing
                        "image": guest.get("image", ""),  # Default to empty string if image is missing
                        "bio": guest.get("bio", ""),
                        "tags": guest.get("tags", []),
                        "email": guest.get("email", ""),
                        "linkedin": guest.get("linkedin", ""),
                        "twitter": guest.get("twitter", ""),
                        "areasOfInterest": guest.get("areasOfInterest", []),
                    }
                )

            # Return the list of guests with a success message
            return {
                "message": "Guests fetched successfully", 
                "guests": guest_list
            }, 200

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