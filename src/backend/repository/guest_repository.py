import json
import uuid
import logging
import email.utils
from datetime import datetime, timezone

from backend.database.mongo_connection import collection
from backend.models.guests import GuestSchema
from backend.services.activity_service import ActivityService
from marshmallow import ValidationError

logger = logging.getLogger(__name__)


class GuestRepository:
    def __init__(self):
        self.collection = collection.database.Guests
        self.activity_service = ActivityService()

    def _parse_publish_date(self, publish_date_str, fallback_date):
        """Attempts to parse a publish date string into an aware datetime object."""
        try:
            parsed = email.utils.parsedate(publish_date_str)
            if parsed:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
        except Exception:
            logger.info(f"RFC 2822 date parsing failed: {publish_date_str}")

        try:
            return datetime.fromisoformat(publish_date_str.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)
        except Exception as e:
            logger.warning(f"ISO date parsing failed: {publish_date_str}, error: {e}")

        logger.warning(f"Using fallback date for unparsed date: {publish_date_str}")
        return fallback_date

    def add_guest(self, data, user_id):
        try:
            # Convert JSON string to dictionary if needed
            if isinstance(data, str):
                data = json.loads(data)

            episode_id = data.get("episodeId")
            episode = collection.database.Episodes.find_one({"_id": episode_id})
            if not episode:
                return {"error": "Episode not found"}, 404
            if "podcast_id" not in episode:
                return {"error": "Episode missing 'podcast_id' field"}, 400

            current_date = datetime.now(timezone.utc)

            try:
                guest_data = GuestSchema().load(data)
            except ValidationError as e:
                return {"error": f"Invalid guest data: {e.messages}"}, 400

            guest_id = str(uuid.uuid4())
            guest_item = {
                "_id": guest_id,
                "episodeId": episode_id,
                "name": guest_data["name"].strip(),
                "image": guest_data.get("image", ""),
                "description": guest_data.get("description", ""),
                "bio": guest_data.get("bio", guest_data.get("description", "")),
                "email": guest_data["email"].strip(),
                "areasOfInterest": guest_data.get("areasOfInterest", []),
                "status": "Pending",
                "scheduled": 0,
                "completed": 0,
                "created_at": current_date,
                "calendarEventId": guest_data.get("calendarEventId", ""),
                "recordingAt": episode.get("recordingAt", None),  
            }

            self.collection.insert_one(guest_item)

            try:
                self.activity_service.log_activity(
                    user_id=user_id,
                    activity_type="guest_added",
                    description=f"Added guest '{guest_item['name']}' to episode.",
                    details={
                        "guestId": guest_id,
                        "episodeId": episode_id,
                        "guestName": guest_item["name"],
                    },
                )
            except Exception as act_err:
                logger.error("Failed to log activity", exc_info=True)

            return {"message": "Guest added successfully", "guest_id": guest_id}, 201

        except Exception as e:
            logger.exception("Failed to add guest")
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
                        "calendarEventId": guest.get(
                            "calendarEventId", ""
                        ),  # Include calendar event ID
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
        Update a guest's information, including status.
        """
        try:
            logger.info(f"🔍 Starting edit_guest for guest_id: {guest_id}, user_id: {user_id}")

            if not guest_id:
                logger.error("❌ Guest ID is required but not provided.")
                return {"error": "Guest ID is required"}, 400

            # Fetch the guest to get the associated episode ID
            guest = self.collection.find_one({"_id": guest_id})
            logger.info(f"📝 Fetched guest: {guest}")
            if not guest:
                logger.error(f"❌ Guest with ID {guest_id} not found.")
                return {"error": "Guest not found"}, 404

            episode_id = guest.get("episode_id")
            logger.info(f"🔗 Guest is associated with episode_id: {episode_id}")
            if not episode_id:
                logger.error(f"❌ Guest with ID {guest_id} is not associated with any episode.")
                return {"error": "Guest is not associated with any episode"}, 400

            # Fetch the episode to verify the podcast owner
            episode = collection.database.Episodes.find_one({"_id": episode_id})
            logger.info(f"📝 Fetched episode: {episode}")
            if not episode:
                logger.error(f"❌ Episode with ID {episode_id} not found.")
                return {"error": "Episode not found"}, 404

            # Verify that the logged-in user owns the episode
            if episode.get("userid") != user_id:
                logger.error(f"❌ Unauthorized: User {user_id} does not own episode {episode_id}.")
                return {"error": "Unauthorized: You do not own this episode"}, 403

            # Prepare update fields dynamically
            update_fields = {}
            logger.info(f"📦 Data received for update: {data}")

            if "name" in data:
                update_fields["name"] = data["name"].strip()
            if "image" in data:
                update_fields["image"] = data["image"]
            if "bio" in data:
                update_fields["bio"] = data["bio"]
            if "email" in data:
                update_fields["email"] = data["email"].strip()
            if "areasOfInterest" in data:
                update_fields["areasOfInterest"] = data["areasOfInterest"]
            if "company" in data:
                update_fields["company"] = data["company"]
            if "phone" in data:
                update_fields["phone"] = data["phone"]
            if "notes" in data:
                update_fields["notes"] = data["notes"]
            if "scheduled" in data:
                update_fields["scheduled"] = data["scheduled"]
            if "recommendedGuests" in data:
                update_fields["recommendedGuests"] = data["recommendedGuests"]
            if "futureOpportunities" in data:
                update_fields["futureOpportunities"] = data["futureOpportunities"]
            if "socialmedia" in data:
                update_fields["socialmedia"] = data["socialmedia"]
            if "episodeId" in data:
                update_fields["episodeId"] = data["episodeId"]
            if "calendarEventId" in data:
                update_fields["calendarEventId"] = data["calendarEventId"]
            if "status" in data:
                update_fields["status"] = data["status"]

            if not update_fields:
                logger.error("❌ No valid fields provided for update.")
                return {"error": "No valid fields provided for update"}, 400

            logger.info(f"📝 Update Fields: {update_fields}")

            # Perform the update
            result = self.collection.update_one(
                {"_id": guest_id},
                {"$set": update_fields}
            )
            logger.info(f"🔄 Update result: Matched Count: {result.matched_count}, Modified Count: {result.modified_count}")

            if result.matched_count == 0:
                logger.error(f"❌ Guest with ID {guest_id} not found or unauthorized.")
                return {"error": "Guest not found or unauthorized"}, 404

            logger.info(f"✅ Guest with ID {guest_id} updated successfully.")
            return {
                "message": "Guest updated successfully",
                "episode_id": guest.get("episode_id")  # Include episode_id in the response
            }, 200

        except Exception as e:
            logger.exception("❌ ERROR: Failed to update guest")
            return {"error": f"Failed to update guest: {str(e)}"}, 500

    def delete_guest(self, guest_id, user_id):
        """
        Delete a guest by ID
        """
        try:
            user_id_str = str(user_id)
            result = self.collection.delete_one(
                {"_id": guest_id, "user_id": user_id_str}
            )
            if result.deleted_count == 0:
                return {"error": "Guest not found or unauthorized"}, 404

            # --- Log activity for guest deleted ---
            try:
                self.activity_service.log_activity(
                    user_id=user_id,
                    activity_type="guest_deleted",
                    description=f"Deleted guest with ID '{guest_id}'.",
                    details={"guestId": guest_id},
                )
            except Exception as act_err:
                logger.error(
                    f"Failed to log guest_deleted activity: {act_err}", exc_info=True
                )
            # --- End activity log ---

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
                        "calendarEventId": guest.get(
                            "calendarEventId", ""
                        ),  # Include calendar event ID
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
                "calendarEventId": guest_cursor.get(
                    "calendarEventId", ""
                ),  # Include calendar event ID
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
                upsert=True,
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
                {"_id": guest_id}, {"$set": {"calendarEventId": event_id}}
            )
            if result.modified_count > 0:
                logger.info(
                    f"Updated calendar event ID for guest {guest_id}: {event_id}"
                )
                return {"message": "Calendar event ID updated successfully"}, 200
            else:
                logger.warning(
                    f"Failed to update calendar event ID for guest {guest_id}"
                )
                return {"error": "Failed to update calendar event ID"}, 500
        except Exception as e:
            logger.exception(f"❌ ERROR: Failed to update calendar event ID: {e}")
            return {"error": f"Failed to update calendar event ID: {str(e)}"}, 500
