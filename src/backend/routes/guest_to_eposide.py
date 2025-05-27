from flask import request, jsonify, Blueprint, g
from backend.utils.email_utils import send_booking_email
from backend.database.mongo_connection import database
from backend.repository.guest_repository import GuestRepository
from datetime import datetime, timedelta, timezone
from flask import url_for
import uuid
import logging

guesttoepisode_bp = Blueprint("guesttoepisode_bp", __name__)
invitations_collection = database.GuestInvitations
assignments_collection = database.GuestToEpisode
logger = logging.getLogger(__name__)

# Initialize guest_repo
guest_repo = GuestRepository()

@guesttoepisode_bp.route("/invite-guest", methods=["POST"])
def create_invitation():
    try:
        data = request.get_json()
        episode_id = str(data.get("episode_id"))
        guest_id = str(data.get("guest_id"))
        user_id = g.get("user_id")  # Assume user_id is set in Flask's global context

        if not all([episode_id, guest_id, user_id]):
            logger.error(f"Missing required fields: episode_id={episode_id}, guest_id={guest_id}, user_id={user_id}")
            return jsonify({"error": "episode_id, guest_id, and user_id are required"}), 400

        # Validate episode exists
        episode = database.Episodes.find_one({"_id": episode_id})
        if not episode:
            logger.error(f"Episode not found: {episode_id}")
            return jsonify({"error": "Episode not found"}), 404

        # Validate user is the episode's host
        host_id = str(episode.get("userid"))
        if not host_id or str(user_id) != host_id:
            logger.error(f"Unauthorized invitation attempt by user_id={user_id} for episode_id={episode_id}")
            return jsonify({"error": "Only the episode host can send invitations"}), 403

        # Fetch guest details
        guest = database.Guests.find_one({"_id": guest_id})
        if not guest:
            logger.error(f"Guest not found: {guest_id}")
            return jsonify({"error": "Guest not found"}), 404
        if not guest.get("email"):
            logger.error(f"Guest has no email address: {guest_id}")
            return jsonify({"error": "Guest has no email address"}), 400

        # Fetch podcast details
        podcast = database.Podcasts.find_one({"_id": episode.get("podcast_id")})
        pod_name = podcast.get("podName", "Your Podcast") if podcast else "Your Podcast"

        # Generate tokens
        invite_token = str(uuid.uuid4())
        invitation_id = str(uuid.uuid4())

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=7)  # 7-day expiry
        invitation = {
            "_id": invitation_id,
            "guest_id": guest_id,
            "episode_id": episode_id,
            "host_id": host_id,
            "email": guest.get("email"),
            "invite_token": invite_token,
            "status": "pending",
            "created_at": now,
            "expires_at": expires_at
        }

        invitations_collection.insert_one(invitation)
        logger.info(f"Invitation created for guest {guest_id} to episode {episode_id}")

        # Generate invite URL
        invite_url = url_for(
            'recording_studio_bp.greenroom',
            episodeId=episode_id,
            guestId=guest_id,
            token=invite_token,
            room=episode_id,
            _external=True
        )

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
                logger.error(f"Failed to send email for guest {guest_id}: {result['error']}")
                return jsonify({"error": f"Failed to send email: {result['error']}"}), 500
        except Exception as e:
            logger.error(f"Error sending invitation email for guest {guest_id}: {str(e)}")
            return jsonify({"error": f"Failed to send email: {str(e)}"}), 500

        return jsonify({
            "message": "Invitation created and email sent",
            "invite_url": invite_url,
            "token": invite_token
        }), 201
    except Exception as e:
        logger.error(f"Error creating invitation for guest {guest_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@guesttoepisode_bp.route("/accept-invite/<token>", methods=["GET"])
def accept_invitation(token):
    try:
        invite = invitations_collection.find_one({
            "invite_token": token,
            "status": "pending",
            "expires_at": {"$gte": datetime.now(timezone.utc)}
        })
        if not invite:
            logger.error(f"Invalid or expired invitation token: {token}")
            return jsonify({"error": "Invalid or expired invitation link"}), 404

        now = datetime.now(timezone.utc)
        # Mark invitation as accepted
        invitations_collection.update_one(
            {"invite_token": token},
            {"$set": {"status": "accepted", "accepted_at": now}}
        )

        # Assign guest to episode if not already assigned
        existing_assignment = assignments_collection.find_one({
            "guest_id": invite["guest_id"],
            "episode_id": invite["episode_id"]
        })
        if not existing_assignment:
            assignments_collection.insert_one({
                "guest_id": invite["guest_id"],
                "episode_id": invite["episode_id"],
                "assigned_at": now
            })
            logger.info(f"Guest {invite['guest_id']} assigned to episode {invite['episode_id']}")
        else:
            logger.info(f"Guest {invite['guest_id']} already assigned to episode {invite['episode_id']}")

        return jsonify({"message": f"Guest assigned to episode {invite['episode_id']} successfully!"}), 200
    except Exception as e:
        logger.error(f"Error accepting invitation with token {token}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@guesttoepisode_bp.route("/send_booking_email/<guest_id>", methods=["POST"])
def send_booking_email_endpoint(guest_id):
    try:
        data = request.get_json()
        recording_at = data.get("recordingAt")
        user_id = g.get("user_id")

        # Fetch the guest details
        guest = database.Guests.find_one({"_id": guest_id})
        if not guest:
            logger.error(f"Guest not found: {guest_id}")
            return jsonify({"error": "Guest not found"}), 404

        # Validate user_id
        if not user_id or str(guest.get("user_id")) != str(user_id):
            logger.error(f"Unauthorized attempt to send email by user_id={user_id} for guest {guest_id}")
            return jsonify({"error": "Unauthorized"}), 403

        # Fetch podcast details
        podcast = database.Podcasts.find_one({"_id": guest.get("podcastId")})
        if not podcast:
            logger.error(f"Podcast not found for guest {guest_id}")
            return jsonify({"error": "Podcast not found"}), 404

        pod_name = podcast.get("podName", "Your Podcast")

        # Send email
        result = send_booking_email(
            recipient_email=guest.get("email"),
            recipient_name=guest.get("name"),
            recording_at=recording_at,
            pod_name=pod_name
        )
        if "error" in result:
            logger.error(f"Failed to send email for guest {guest_id}: {result['error']}")
            return jsonify(result), 500

        # Update guest status
        update_payload = {"status": "accepted"}
        status_code = guest_repo.edit_guest(guest_id, update_payload, user_id)
        if status_code != 200:
            logger.error(f"Failed to update guest status for {guest_id}")
            return jsonify({"error": "Failed to update guest status"}), status_code

        logger.info(f"Booking email sent and guest status updated for {guest_id}")
        return jsonify({"message": "Booking email sent and guest status updated successfully!"}), 200
    except Exception as e:
        logger.error(f"Error in send_booking_email_endpoint for guest {guest_id}: {str(e)}")
        return jsonify({"error": f"Failed to send booking email: {str(e)}"}), 500