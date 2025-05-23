from flask import request, jsonify, Blueprint, redirect, g
from backend.utils.email_utils import send_booking_email
from backend.database.mongo_connection import database, collection
from backend.repository.guest_repository import GuestRepository
from datetime import datetime, timezone
import uuid
import logging

guesttoepisode_bp = Blueprint("guesttoepisode_bp", __name__)
invitations_collection = database.GuestInvitations  # New collection just for invitations
assignments_collection = database.GuestToEpisode    # Keeps track of final assignments
logger = logging.getLogger(__name__)

# Initialize guest_repo
guest_repo = GuestRepository()

#THIS SHOULD NOT BE CRUD FOR GUESTS, BUT FOR ASSIGNING GUESTS TO EPISODES BY SENDING INVITATIONS
#DISPLAYNG GUESTS FOR A EPIOSODE IS IN GUEST_REPOSITORY
# 1️⃣ Create an invitation link for a guest
@guesttoepisode_bp.route("/invite-guest", methods=["POST"])
def create_invitation():
    data = request.get_json()
    episode_id = data.get("episode_id")
    guest_id = data.get("guest_id")

    if not episode_id or not guest_id:
        return jsonify({"error": "Both episode_id and guest_id are required"}), 400

    invite_token = str(uuid.uuid4())
    invitation = {
        "guest_id": guest_id,
        "episode_id": episode_id,
        "token": invite_token,
        "created_at": datetime.now(timezone.utc),
        "accepted": False
    }

    invitations_collection.insert_one(invitation)
    invite_url = f"/accept-invite/{invite_token}"
    return jsonify({"message": "Invitation created", "invite_url": invite_url}), 201

# 2️⃣ Guest accepts the invite via URL
@guesttoepisode_bp.route("/accept-invite/<token>", methods=["GET"])
def accept_invitation(token):
    invite = invitations_collection.find_one({"token": token})

    if not invite:
        return jsonify({"error": "Invalid or expired invitation link"}), 404
    if invite.get("accepted"):
        return jsonify({"message": "Invitation already accepted"}), 200

    # Mark as accepted
    invitations_collection.update_one({"token": token}, {"$set": {"accepted": True, "accepted_at": datetime.now(timezone.utc)}})

    # Assign guest to episode
    assignments_collection.insert_one({
        "guest_id": invite["guest_id"],
        "episode_id": invite["episode_id"],
        "assigned_at": datetime.now(timezone.utc)
    })

    # You can redirect to frontend success page if needed
    return jsonify({"message": f"Guest assigned to episode {invite['episode_id']} successfully!"}), 200

@guesttoepisode_bp.route("/send_booking_email/<guest_id>", methods=["POST"])
def send_booking_email_endpoint(guest_id):
    """Endpoint to send a booking email to the guest and update their status."""
    try:
        data = request.get_json()
        recording_at = data.get("recordingAt")

        # Fetch the guest details
        guest = collection.database.Guests.find_one({"_id": guest_id})
        if not guest:
            return jsonify({"error": "Guest not found"}), 404

        # Validate that the user_id matches the guest's user_id
        user_id = g.get("user_id")
        if not user_id or str(guest.get("user_id")) != str(user_id):
            return jsonify({"error": "Unauthorized"}), 403

        # Fetch the podcast details dynamically from the Podcasts collection
        podcast = collection.database.Podcasts.find_one({"_id": guest.get("podcastId")})
        if not podcast:
            return jsonify({"error": "Podcast not found"}), 404

        pod_name = podcast.get("podName", "Your Podcast Name")  # Default fallback if podName is missing

        # Prepare email details
        recipient_email = guest.get("email")
        recipient_name = guest.get("name")

        # Call the utility function to send the email
        result = send_booking_email(recipient_email, recipient_name, recording_at, pod_name)
        if "error" in result:
            return jsonify(result), 500

        # Update the guest's status to "accepted" using the existing edit_guest method
        update_payload = {"status": "accepted"}
        status_code = guest_repo.edit_guest(guest_id, update_payload, user_id)
        if status_code != 200:
            return jsonify({"error": "Failed to update guest status"}), status_code

        return jsonify({"message": "Booking email sent and guest status updated successfully!"}), 200
    except Exception as e:
        logger.error(f"Error in send_booking_email_endpoint: {e}", exc_info=True)
        return jsonify({"error": f"Failed to send booking email: {str(e)}"}), 500
