from backend.database.mongo_connection import collection
from datetime import datetime, timezone
import uuid
import logging
from backend.models.guests import GuestSchema
from marshmallow import ValidationError
import email.utils  # Import to handle parsing date format
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)


class GuestRepository:
    def __init__(self):
        self.collection = collection.database.Guests

    def add_guest(self, data, user_id):
        try:
            episode_id = data.get("episodeId")

            # Fetch the episode and ensure it contains the 'podcast_id' field
            episode = collection.database.Episodes.find_one({"_id": episode_id})
            if not episode:
                logger.error(f"Episode with ID {episode_id} not found.")
                return {"error": "Episode not found"}, 404
            if "podcast_id" not in episode:
                logger.warning(f"Episode with ID {episode_id} is missing 'podcast_id'.")
                return {"error": "Episode missing 'podcast_id' field"}, 400

            current_date = datetime.now(timezone.utc)

            # Parse and make publish_date offset-aware
            try:
                # Check if publishDate exists and is not None
                if "publishDate" in episode and episode["publishDate"] is not None:
                    publish_date = None
                    publish_date_str = episode["publishDate"]
                    
                    # Try parsing as RFC 2822 format first (email.utils.parsedate)
                    try:
                        publish_date_parsed = email.utils.parsedate(publish_date_str)
                        if publish_date_parsed:
                            publish_date = datetime(
                                *publish_date_parsed[:6]
                            ).replace(tzinfo=timezone.utc)
                    except Exception:
                        # If RFC 2822 parsing fails, log it but continue to try ISO format
                        logger.info(f"RFC 2822 date parsing failed for: {publish_date_str}")
                    
                    # If RFC 2822 parsing failed, try ISO format
                    if not publish_date:
                        try:
                            publish_date = datetime.fromisoformat(publish_date_str.replace('Z', '+00:00'))
                            publish_date = publish_date.replace(tzinfo=timezone.utc)
                        except Exception as e:
                            logger.warning(f"ISO date parsing failed for: {publish_date_str}, error: {str(e)}")
                    
                    # If both parsing methods failed, use current date
                    if not publish_date:
                        logger.warning(f"All date parsing methods failed for: {publish_date_str}, using current date")
                        publish_date = current_date
                else:
                    # If publishDate is missing or None, use current date
                    publish_date = current_date
            except Exception as e:
                logger.exception(f"Error parsing publish date: {str(e)}")
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
                "calendarEventId": guest_data.get("calendarEventId", "")  # Store calendar event ID
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
                    "calendarEventId": 1,  # Include calendar event ID
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
                        "calendarEventId": guest.get("calendarEventId", ""),  # Include calendar event ID
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

            # If calendarEventId is provided, update it
            calendar_event_id = data.get("calendarEventId")
            if calendar_event_id is not None:
                update_fields["calendarEventId"] = calendar_event_id

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
                        "calendarEventId": guest.get("calendarEventId", ""),  # Include calendar event ID
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
                    "calendarEventId": 1,  # Include calendar event ID
                    "company": 1,
                    "phone": 1,
                    "scheduled": 1,
                    "notes": 1,
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
                "calendarEventId": guest_cursor.get("calendarEventId", ""),  # Include calendar event ID
                "company": guest_cursor.get("company", ""),
                "phone": guest_cursor.get("phone", ""),
                "scheduled": guest_cursor.get("scheduled", 0),
                "notes": guest_cursor.get("notes", ""),
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

    def save_google_refresh_token(self, user_id, refresh_token):
        """
        Save the Google OAuth2 refresh token in the Users collection.
        """
        try:
            result = collection.database.Users.update_one(
                {"_id": str(user_id)},
                {"$set": {"googleRefresh": refresh_token}},  # Save as googleRefresh
                upsert=True
            )
            if result.modified_count > 0 or result.upserted_id:
                return {"message": "Google refresh token saved successfully"}, 200
            return {"error": "Failed to save Google refresh token"}, 500
        except Exception as e:
            logger.exception("❌ ERROR: Failed to save Google refresh token")
            return {"error": f"Failed to save Google refresh token: {str(e)}"}, 500
            
    def update_calendar_event_id(self, guest_id, event_id):
        """
        Update the calendar event ID for a guest.
        """
        try:
            result = self.collection.update_one(
                {"_id": guest_id},
                {"$set": {"calendarEventId": event_id}}
            )
            if result.modified_count > 0:
                logger.info(f"Updated calendar event ID for guest {guest_id}: {event_id}")
                return {"message": "Calendar event ID updated successfully"}, 200
            else:
                logger.warning(f"Failed to update calendar event ID for guest {guest_id}")
                return {"error": "Failed to update calendar event ID"}, 500
        except Exception as e:
            logger.exception(f"❌ ERROR: Failed to update calendar event ID: {e}")
            return {"error": f"Failed to update calendar event ID: {str(e)}"}, 500
