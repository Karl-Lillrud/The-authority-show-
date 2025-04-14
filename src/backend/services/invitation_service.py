from flask import url_for
from backend.database.mongo_connection import collection
from backend.utils.email_utils import send_guest_invitation_email
import logging

logger = logging.getLogger(__name__)

class InvitationService:
    @staticmethod
    def send_guest_invitation(user_id, guest_data):
        """
        Adds a guest to the database using the repository and sends an invitation email.
        """
        from backend.repository.guest_repository import GuestRepository
        
        try:
            # Fetch the user's googleCal token
            user = collection.database.Users.find_one({"_id": user_id}, {"googleCal": 1})
            google_cal_token = user.get("googleCal")
            if not google_cal_token:
                return {"error": "You need to connect your Google Calendar first"}, 400
                
            # Use repository to add guest to database
            guest_repo = GuestRepository()
            response, status_code = guest_repo.add_guest(guest_data, user_id)
            
            # If guest was added successfully, send invitation email
            if status_code == 201 and "guest_id" in response:
                guest_id = response["guest_id"]
                
                try:
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
                    return {"message": "Guest added and invitation email sent successfully", "guest_id": guest_id}, 201
                except Exception as email_error:
                    logger.warning(f"Guest added successfully but failed to send invitation email: {str(email_error)}")
                    return {"message": "Guest added successfully but failed to send invitation email", "guest_id": guest_id}, 201
            
            # If adding guest failed, return the error
            return response, status_code
            
        except Exception as e:
            logger.error(f"Failed to send guest invitation: {e}", exc_info=True)
            return {"error": f"Failed to send guest invitation: {str(e)}"}, 500
