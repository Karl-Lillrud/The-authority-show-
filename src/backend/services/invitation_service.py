from flask import url_for
from backend.database.mongo_connection import collection
from backend.utils.email_utils import send_guest_invitation_email
import logging

logger = logging.getLogger(__name__)

class InvitationService:
    @staticmethod
    def send_guest_invitation(user_id, guest_data):
        """
        Sends an invitation email to a guest and saves the guest to the database.
        """
        try:
            # Fetch the user's googleCal token
            user = collection.database.Users.find_one({"_id": user_id}, {"googleCal": 1})
            google_cal_token = user.get("googleCal")
            if not google_cal_token:
                return {"error": "User has not connected their Google Calendar"}, 400

            # Save the guest to the database
            guest_id = collection.database.Guests.insert_one({
                "name": guest_data["name"],
                "email": guest_data["email"],
                "description": guest_data.get("description", ""),
                "tags": guest_data.get("tags", []),
                "areasOfInterest": guest_data.get("areasOfInterest", []),
                "user_id": user_id,
                "episodeId": guest_data["episodeId"],  # Ensure episodeId is saved
            }).inserted_id

            # Fetch the podcast name using the episode ID
            episode = collection.database.Episodes.find_one({"_id": guest_data["episodeId"]}, {"podcast_id": 1})
            if not episode:
                logger.error(f"Episode with ID {guest_data['episodeId']} not found.")
                raise ValueError("Episode not found")
            if "podcast_id" not in episode:
                logger.error(f"Episode with ID {guest_data['episodeId']} is missing 'podcast_id' field.")
                raise ValueError("Episode missing 'podcast_id' field")

            podcast = collection.database.Podcasts.find_one({"_id": episode["podcast_id"]}, {"podName": 1})
            if not podcast:
                logger.error(f"Podcast with ID {episode['podcast_id']} not found.")
                raise ValueError("Podcast not found")

            podcast_name = podcast.get("podName", "Our Podcast")

            # Generate the invitation link
            guest_form_url = url_for(
                "guest_form.guest_form",
                _external=True,
                guestId=str(guest_id),
                googleCal=google_cal_token,
            )

            # Send the invitation email
            send_guest_invitation_email(
                guest_data["name"],
                guest_data["email"],
                guest_form_url,
                podcast_name,  # Pass the podcast name
            )

            logger.info(f"Guest invitation email sent to {guest_data['email']}")
            return {"message": "Guest added and invitation email sent successfully", "guest_id": str(guest_id)}, 201

        except Exception as e:
            logger.error(f"Failed to send guest invitation: {e}", exc_info=True)
            return {"error": f"Failed to send guest invitation: {str(e)}"}, 500
