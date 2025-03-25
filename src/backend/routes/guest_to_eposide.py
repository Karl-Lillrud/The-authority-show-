from flask import request, jsonify, Blueprint, redirect
from backend.database.mongo_connection import database
from datetime import datetime, timezone
import uuid

guesttoepisode_bp = Blueprint("guesttoepisode_bp", __name__)
invitations_collection = database.GuestInvitations  # New collection just for invitations
assignments_collection = database.GuestToEpisode    # Keeps track of final assignments
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
