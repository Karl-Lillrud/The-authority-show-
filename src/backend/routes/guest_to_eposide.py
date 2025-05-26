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

    # Validate episode exists
    episode = collection.database.Episodes.find_one({"_id": episode_id})
    if not episode:
        return jsonify({"error": "Episode not found"}), 404

    # Fetch guest details
    guest = collection.database.Guests.find_one({"_id": guest_id})
    if not guest:
        return jsonify({"error": "Guest not found"}), 404
    if not guest.get("email"):
        return jsonify({"error": "Guest has no email address"}), 400

    # Fetch podcast details
    podcast = collection.database.Podcasts.find_one({"_id": episode.get("podcastId")})
    pod_name = podcast.get("podName", "Your Podcast") if podcast else "Your Podcast"

    # Generate token and invitation record
    invite_token = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    invitation = {
        "guest_id": guest_id,
        "episode_id": episode_id,
        "email": guest.get("email"),
        "token": invite_token,
        "created_at": now,
        "accepted": True,
        "accepted_at": now
    }

    invitations_collection.insert_one(invitation)

    # Assign guest to episode
    assignments_collection.insert_one({
        "guest_id": guest_id,
        "episode_id": episode_id,
        "assigned_at": now
    })

    # Generate invite URL
    invite_url = f"{request.host_url}greenroom?episodeId={episode_id}&guestId={guest_id}&token={invite_token}"
    logger.info(f"Invitation created for guest {guest_id} to episode {episode_id}: {invite_url}")

    # Send booking email
    try:
        result = send_booking_email(
            recipient_email=guest.get("email"),
            recipient_name=guest.get("name", "Guest"),
            recording_at=episode.get("recordingAt"),
            pod_name=pod_name,
            invite_url=invite_url
        )
        if "error" in result:
            logger.error(f"Failed to send email: {result['error']}")
            return jsonify({"error": f"Failed to send email: {result['error']}"}), 500
    except Exception as e:
        logger.error(f"Error sending invitation email: {e}", exc_info=True)
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500

    return jsonify({
        "message": "Invitation created, guest assigned, and email sent",
        "invite_url": invite_url,
        "token": invite_token
    }), 201

    
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
