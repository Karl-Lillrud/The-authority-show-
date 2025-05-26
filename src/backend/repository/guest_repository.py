import json
import uuid
import logging
import email.utils
from datetime import datetime, timezone

from backend.database.mongo_connection import collection
from backend.services.activity_service import ActivityService
from pydantic import BaseModel, EmailStr, Field, HttpUrl, ValidationError
from typing import Optional, List

logger = logging.getLogger(__name__)

# Define Pydantic model for Guest
class Guest(BaseModel): # Renamed from GuestSchema for Pydantic convention
    id: Optional[str] = Field(default=None) # Removed alias="id"
    name: str
    email: EmailStr # Assuming email was part of GuestSchema
    phone: Optional[str] = None
    company: Optional[str] = None # Assuming company was part of GuestSchema
    bio: Optional[str] = None
    socialMedia: Optional[dict] = None # Assuming socialMedia was part of GuestSchema
    image: Optional[HttpUrl] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow) # Was created_at
    updatedAt: Optional[datetime] = None

    # Fields from original guest_item
    episodeId: Optional[str] = None
    description: Optional[str] = None # if different from bio
    areasOfInterest: Optional[List[str]] = Field(default_factory=list)
    status: Optional[str] = "Pending"
    scheduled: Optional[int] = 0 # Assuming this was a field
    completed: Optional[int] = 0 # Assuming this was a field
    calendarEventId: Optional[str] = None
    recordingAt: Optional[datetime] = None
    user_id: Optional[str] = None # If guests are user-specific
    tags: Optional[List[str]] = Field(default_factory=list) # from guest_list append
    linkedin: Optional[str] = None # from guest_list append
    twitter: Optional[str] = None # from guest_list append
    notes: Optional[str] = None # from edit_guest
    recommendedGuests: Optional[List[str]] = Field(default_factory=list) # from edit_guest
    futureOpportunities: Optional[str] = None # from edit_guest
    podcastId: Optional[str] = None # from send_booking_email_endpoint


class GuestRepository:
    def __init__(self):
        self.collection = collection.database.Guests
        self.activity_service = ActivityService()
        self.episodes_collection = collection.database.Episodes # Added for find_one

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
            if isinstance(data, str):
                data = json.loads(data)

            episode_id_val = data.get("episodeId") # Renamed episode_id to episode_id_val
            episode_doc = self.episodes_collection.find_one({"id": episode_id_val}) # Query by id, Renamed episode to episode_doc
            if not episode_doc:
                return {"error": "Episode not found"}, 404
            
            # podcast_id is not standard, ensure it's podcastId or similar
            # if "podcast_id" not in episode_doc and "podcastId" not in episode_doc:
            #     return {"error": "Episode missing 'podcastId' field"}, 400


            data["user_id"] = str(user_id) # Add user_id for Pydantic model if it's part of it
            data["recordingAt"] = episode_doc.get("recordingAt", None) # Get from episode_doc

            try:
                # Assuming Guest is the Pydantic model
                validated_guest = Guest(**data)
            except ValidationError as e:
                return {"error": f"Invalid guest data: {e.errors()}"}, 400

            guest_data_dict = validated_guest.dict(exclude_none=True) # Use exclude_none=True, Renamed guest_item to guest_data_dict
            
            if "id" not in guest_data_dict or not guest_data_dict["id"]: # Ensure id is set
                guest_data_dict["id"] = str(uuid.uuid4())
            
            # Ensure all necessary fields are present, Pydantic model defaults should handle most
            guest_data_dict.setdefault("status", "Pending")
            guest_data_dict.setdefault("scheduled", 0)
            guest_data_dict.setdefault("completed", 0)


            self.collection.insert_one(guest_data_dict)

            try:
                self.activity_service.log_activity(
                    user_id=user_id,
                    activity_type="guest_added",
                    description=f"Added guest '{guest_data_dict['name']}' to episode.",
                    details={
                        "guestId": guest_data_dict["id"],
                        "episodeId": episode_id_val,
                        "guestName": guest_data_dict["name"],
                    },
                )
            except Exception as act_err:
                logger.error("Failed to log activity", exc_info=True)

            return {"message": "Guest added successfully", "guest_id": guest_data_dict["id"]}, 201

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
                {"user_id": user_id}, # Assuming guests are linked to a user_id
                {
                    "id": 1, # Changed _id to id
                    "episodeId": 1,
                    "name": 1,
                    "image": 1,
                    "bio": 1,
                    "tags": 1,
                    "email": 1,
                    "linkedin": 1,
                    "twitter": 1,
                    "areasOfInterest": 1,
                    "calendarEventId": 1,
                },
            )

            # Prepare the guest list with necessary fields
            guest_list = []
            for guest_doc in guests_cursor: # Renamed guest to guest_doc
                guest_doc["id"] = str(guest_doc.get("id", guest_doc.get("id"))) # Handle if DB still has _id
                if "id" in guest_doc and guest_doc["id"] != guest_doc["id"]: # remove _id if id is now primary
                    del guest_doc["id"]

                guest_list.append(
                    {
                        "id": guest_doc["id"],
                        "episodeId": guest_doc.get("episodeId", None),
                        "name": guest_doc.get("name", "N/A"),
                        "image": guest_doc.get("image", ""),
                        "bio": guest_doc.get("bio", ""),
                        "tags": guest_doc.get("tags", []),
                        "email": guest_doc.get("email", ""),
                        "linkedin": guest_doc.get("linkedin", ""),
                        "twitter": guest_doc.get("twitter", ""),
                        "areasOfInterest": guest_doc.get("areasOfInterest", []),
                        "calendarEventId": guest_doc.get("calendarEventId", ""),
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

            guest_doc = self.collection.find_one({"id": guest_id}) # Query by id, Renamed guest to guest_doc
            logger.info(f"📝 Fetched guest: {guest_doc}")
            if not guest_doc:
                logger.error(f"❌ Guest with ID {guest_id} not found.")
                return {"error": "Guest not found"}, 404
            
            # Verify ownership if guest has user_id field
            if "user_id" in guest_doc and str(guest_doc["user_id"]) != str(user_id):
                 logger.error(f"❌ Unauthorized: User {user_id} does not own guest {guest_id}.")
                 return {"error": "Unauthorized: You do not own this guest"}, 403


            episode_id_val = guest_doc.get("episodeId") # Renamed episode_id to episode_id_val
            logger.info(f"🔗 Guest is associated with episodeId: {episode_id_val}")
            
            # This part seems to verify episode ownership, which might be redundant if guest ownership is checked
            # Or if guest is not directly owned but linked via episode that user owns.
            # For now, assuming guest has a user_id or the logic is tied to episode ownership.
            if episode_id_val:
                episode_doc = self.episodes_collection.find_one({"id": episode_id_val}) # Query by id, Renamed episode to episode_doc
                logger.info(f"📝 Fetched episode: {episode_doc}")
                if not episode_doc:
                    logger.error(f"❌ Episode with ID {episode_id_val} not found.")
                    # This might be acceptable if guest can exist without episode or if episode link is being changed
                elif episode_doc.get("userid") != user_id and episode_doc.get("accountId") != user_id: # Check userid or accountId
                     logger.error(f"❌ Unauthorized: User {user_id} does not own episode {episode_id_val}.")
                     # return {"error": "Unauthorized: You do not own the associated episode"}, 403


            # Prepare update fields using Pydantic model for validation
            # Merge existing guest data with new data, then validate
            data_to_validate = {**guest_doc, **data}
            if "id" in data_to_validate: # if guest_doc came with _id
                data_to_validate["id"] = str(data_to_validate.pop("id"))
            
            try:
                validated_guest_update = Guest(**data_to_validate)
                update_fields = validated_guest_update.dict(exclude_unset=True, exclude_none=True)
            except ValidationError as e:
                logger.error(f"Validation error updating guest: {e.errors()}")
                return {"error": f"Invalid data: {e.errors()}"}, 400

            # Remove fields that should not be updated directly or are part of the query
            if "id" in update_fields: del update_fields["id"]
            if "user_id" in update_fields: del update_fields["user_id"] # user_id should not change here
            if "createdAt" in update_fields: del update_fields["createdAt"]

            update_fields["updatedAt"] = datetime.now(timezone.utc)


            if not update_fields:
                logger.info("✅ No valid fields provided for update or no changes detected.")
                return {"message": "No changes made to the guest."}, 200

            logger.info(f"📝 Update Fields: {update_fields}")

            result = self.collection.update_one(
                {"id": guest_id}, # Query by id
                {"$set": update_fields}
            )
            logger.info(f"🔄 Update result: Matched Count: {result.matched_count}, Modified Count: {result.modified_count}")

            if result.matched_count == 0: # Should not happen if find_one succeeded, unless guest deleted in interim
                logger.error(f"❌ Guest with ID {guest_id} not found for update (race condition?).")
                return {"error": "Guest not found or unauthorized"}, 404

            logger.info(f"✅ Guest with ID {guest_id} updated successfully.")
            return {
                "message": "Guest updated successfully",
                "episode_id": guest_doc.get("episodeId") 
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
            # First, find the guest to ensure it belongs to the user before deleting
            guest_to_delete = self.collection.find_one({"id": guest_id, "user_id": user_id_str})
            if not guest_to_delete:
                # Check if guest exists but doesn't belong to user, or doesn't exist at all
                exists_check = self.collection.find_one({"id": guest_id})
                if exists_check:
                    logger.warning(f"Unauthorized attempt to delete guest {guest_id} by user {user_id_str}")
                    return {"error": "Unauthorized"}, 403
                else:
                    logger.warning(f"Guest {guest_id} not found for deletion.")
                    return {"error": "Guest not found"}, 404


            result = self.collection.delete_one(
                {"id": guest_id, "user_id": user_id_str} # Query by id
            )
            if result.deleted_count == 0:
                # This case should ideally be caught by the find_one check above
                logger.error(f"Failed to delete guest {guest_id} (already deleted or race condition).")
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
            for guest_doc in guests_cursor: # Renamed guest to guest_doc
                guest_doc["id"] = str(guest_doc.get("id", guest_doc.get("id"))) # Handle if DB still has _id
                if "id" in guest_doc and guest_doc["id"] != guest_doc["id"]:
                     del guest_doc["id"]
                guest_list.append(
                    {
                        "id": guest_doc["id"],
                        "episodeId": guest_doc.get("episodeId"),
                        "name": guest_doc.get("name"),
                        "image": guest_doc.get("image"),
                        "bio": guest_doc.get("bio"),
                        "tags": guest_doc.get("tags", []),
                        "email": guest_doc.get("email"),
                        "linkedin": guest_doc.get("linkedin"),
                        "twitter": guest_doc.get("twitter"),
                        "areasOfInterest": guest_doc.get("areasOfInterest", []),
                        "calendarEventId": guest_doc.get(
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
            guest_cursor_doc = self.collection.find_one( # Renamed guest_cursor to guest_cursor_doc
                {"id": guest_id, "user_id": user_id}, # Query by id
                {
                    # Projections: 1 for include, 0 for exclude.
                    # If using "id" as primary, _id projection is not needed unless to explicitly exclude it if it co-exists.
                    # Assuming DB now uses "id", so "id":0 is not strictly needed if "id" is projected.
                    # For safety, if _id might still exist: "id": 0,
                    "id": 1,
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

            if guest_cursor_doc is None:
                return {"message": "Guest not found"}, 404

            guest_data_item = { # Renamed guest to guest_data_item
                "id": str(guest_cursor_doc.get("id")), # Ensure it's string
                "episodeId": guest_cursor_doc.get("episodeId"),
                "name": guest_cursor_doc.get("name", "N/A"),
                "image": guest_cursor_doc.get("image", ""),
                "bio": guest_cursor_doc.get("bio", ""),
                "tags": guest_cursor_doc.get("tags", []),
                "email": guest_cursor_doc.get("email", ""),
                "linkedin": guest_cursor_doc.get("linkedin", ""),
                "twitter": guest_cursor_doc.get("twitter", ""),
                "areasOfInterest": guest_cursor_doc.get("areasOfInterest", []),
                "calendarEventId": guest_cursor_doc.get(
                    "calendarEventId", ""
                ),  # Include calendar event ID
                "company": guest_cursor_doc.get("company", ""),
                "phone": guest_cursor_doc.get("phone", ""),
                "scheduled": guest_cursor_doc.get("scheduled", 0),
                "notes": guest_cursor_doc.get("notes", ""),
            }

            return {"message": "Guest fetched successfully", "guest": guest_data_item}, 200

        except Exception as e:
            logger.exception("❌ ERROR: Failed to fetch guest by ID")
            return {"error": f"An error occurred while fetching guest: {str(e)}"}, 500

    def get_episodes_by_guest(self, guest_id):
        """
        Get all episodes for a specific guest
        """
        try:
            # This aggregation implies 'guests' is an array of guest_ids in the Episodes collection.
            # And that Episodes collection items have an 'episodes' array field, which is unusual.
            # Assuming the intent is to find episodes where this guest_id is listed.
            # A more typical structure would be Episodes having a guest_ids array.
            # If Episodes collection has _id as primary key, it should be changed to id.
            # If the 'episodes' field within a document has an _id, that also needs to change.
            # The query "$match": {"guests": guest_id} implies 'guests' is a field in the root of the collection being aggregated.
            # If this is on 'Guests' collection and 'episodes' is an array of episode details:
            
            # Simpler approach if guests are linked from Episodes:
            # episodes_cursor = collection.database.Episodes.find({"guestIds": guest_id})
            # This aggregation is complex and depends heavily on the schema of "self.collection" (Guests)
            # and how episodes are related. Assuming "self.collection" is Guests.
            # And Guests documents have an array "episodes" which are sub-documents.
            
            # If the aggregation is on the Episodes collection:
            # episodes_cursor = collection.database.Episodes.find({"guests": guest_id})
            # For now, applying literal _id -> id change to the provided aggregation.

            episodes_cursor = self.collection.aggregate( # self.collection is Guests
                [
                    {"$match": {"id": guest_id}}, # Match the guest document itself
                    {"$unwind": "$episodes"}, # Assuming guest doc has an 'episodes' array field
                    {
                        "$project": { # Project fields from the 'episodes' sub-document
                            "episode_id": "$episodes.id", # Assuming episodes sub-doc uses 'id'
                            "title": "$episodes.title",
                            "description": "$episodes.description",
                            "publish_date": "$episodes.publish_date",
                            # "guests": "$episodes.guests", # This would be guests of that specific episode, not the main guest
                        }
                    },
                ]
            )
            # This aggregation needs review based on actual schema.
            # The original aggregation seemed to be on a collection that has an 'episodes' array,
            # and each item in that array has 'guests', 'title', etc.
            # If self.collection is Guests, and guest has a list of episode IDs or details:
            # Example: guest document has field `associated_episode_ids: [id1, id2]`
            # Then one would find the guest, then find episodes based on those IDs.

            # Applying literal change to the original structure:
            # This assumes self.collection (Guests) has documents with an 'episodes' array,
            # and each element in 'episodes' has an '_id' (now 'id') and a 'guests' array.
            # This is an unusual schema if self.collection is Guests.
            # If self.collection is something else (e.g. Podcasts that have episodes with guests):
            # {"$match": {"episodes.guests": guest_id}},
            # {"$unwind": "$episodes"},
            # {"$match": {"episodes.guests": guest_id}},
            # {"$project": {"id": "$episodes.id", ...}}

            # Given the original code, and applying literal replacement:
            # This implies self.collection (Guests) has an array field `episodes`
            # where each element is an episode document that itself has a `guests` field (array of guest_ids)
            # and an `_id` (now `id`) field.
            # The first $match should be on the guest's ID itself if we are trying to find episodes for *this* guest.
            # The original query was:
            # {"$match": {"guests": guest_id}},  -> This would match if the main document (Guest) has a 'guests' field matching guest_id. Unlikely.
            # {"$unwind": "$episodes"},
            # {"$match": {"episodes.guests": guest_id}}, -> This matches if sub-document episode has this guest.
            # {"$project": {"id": "$episodes._id", ...}}
            # This seems to be querying a collection (not necessarily Guests) that has an array of episodes.

            # Let's assume the method means "get episodes this guest is part of" from the Episodes collection.
            # This would be:
            # episodes_cursor = collection.database.Episodes.find({"guest_ids_array_field": guest_id})
            # The provided aggregation is confusing for a GuestRepository.
            # I will apply the literal change to the provided aggregation, assuming its logic was correct for its original context.

            episodes_cursor = self.collection.aggregate( # self.collection is Guests
                [
                    {"$match": {"guests": guest_id}}, 
                    {"$unwind": "$episodes"},
                    {
                        "$match": {"episodes.guests": guest_id}
                    },  
                    {
                        "$project": {
                            "episode_id": "$episodes.id", # Changed from _id
                            "title": "$episodes.title",
                            "description": "$episodes.description",
                            "publish_date": "$episodes.publish_date",
                            "guests": "$episodes.guests",
                        }
                    },
                ]
            )


            episodes_list = []
            for episode_item in episodes_cursor: # Renamed episode to episode_item
                episodes_list.append(
                    {
                        "episode_id": str(episode_item["episode_id"]), # episode_id is already projected as "episode_id"
                        "title": episode_item["title"],
                        "description": episode_item["description"],
                        "publish_date": episode_item["publish_date"],
                        "guests": episode_item["guests"],
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
                {"id": str(user_id)}, # Query by id
                {"$set": {"googleRefresh": refresh_token}}, 
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
                {"id": guest_id}, {"$set": {"calendarEventId": event_id}} # Query by id
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
