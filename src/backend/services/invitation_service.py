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
            }).inserted_id

            # Generate the invitation link
            guest_form_url = url_for(
                "guest_form.guest_form",  # Corrected blueprint and endpoint name
                _external=True,
                guestId=str(guest_id),
                googleCal=google_cal_token,
            )

            # Send the invitation email
            send_guest_invitation_email(guest_data["name"], guest_data["email"], guest_form_url)

            logger.info(f"Guest invitation email sent to {guest_data['email']}")
            return {"message": "Guest added and invitation email sent successfully"}, 201

        except Exception as e:
            logger.error(f"Failed to send guest invitation: {e}", exc_info=True)
            return {"error": f"Failed to send guest invitation: {str(e)}"}, 500
