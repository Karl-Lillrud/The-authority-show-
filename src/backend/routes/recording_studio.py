from flask import Blueprint, render_template, url_for, request, jsonify
from datetime import datetime, timezone
import logging

from backend.database.mongo_connection import database


recording_studio_bp = Blueprint("recording_studio_bp", __name__)

# MongoDB collections
invitations_collection = database.GuestInvitations
episodes_collection = database.Episodes
guests_collection = database.Guests

# Configure logger
logger = logging.getLogger(__name__)


# Validate invitation
def validate_invitation(episode_id, guest_id, token):
    query = {
        "episode_id": episode_id,
        "guest_id": guest_id,
        "invite_token": token,
        "status": "pending",
        "expires_at": {"$gte": datetime.now(timezone.utc)}
    }
    invitation = invitations_collection.find_one(query)
    if invitation:
        logger.info(f"Valid invitation found: episode_id={episode_id}, guest_id={guest_id}")
        return True
    logger.warning(f"Invalid invitation: episode_id={episode_id}, guest_id={guest_id}")
    return False


@recording_studio_bp.route('/participants/<episode_id>', methods=['GET'])
def get_participants(episode_id):
    try:
        episode = episodes_collection.find_one({"_id": episode_id}, {"userid": 1})
        if not episode:
            logger.error(f"Episode not found: {episode_id}")
            return jsonify({"error": "Episode not found"}), 404

        guests = list(guests_collection.find({"episode_id": episode_id}, {"_id": 1}))
        participants = {
            "host": episode["userid"],
            "guests": [str(guest["_id"]) for guest in guests]
        }
        logger.info(f"Retrieved participants for episode: {episode_id}")
        return jsonify(participants), 200
    except Exception as e:
        logger.error(f"Error retrieving participants: {str(e)}")
        return jsonify({"error": str(e)}), 500

@recording_studio_bp.route('/verify_invite/<invite_token>', methods=['GET'])
def verify_invite(invite_token):
    try:
        invitation = invitations_collection.find_one({
            "invite_token": invite_token,
            "status": "pending",
            "expires_at": {"$gte": datetime.now(timezone.utc)}
        })
        if not invitation:
            logger.error(f"Invalid or expired invitation token")
            return jsonify({"error": "Invalid or expired invitation token"}), 404

        join_url = url_for("recording_studio_bp.recording_studio", _external=True, token=invite_token)
        logger.info(f"Valid invitation token for episode_id={invitation['episode_id']}")
        return jsonify({
            "message": "Invitation token is valid",
            "episode_id": invitation["episode_id"],
            "join_url": join_url
        }), 200
    except Exception as e:
        logger.error(f"Error verifying invite: {str(e)}")
        return jsonify({"error": str(e)}), 500

@recording_studio_bp.route('/studio')
def recording_studio():
    room = request.args.get('room')
    episode_id = request.args.get('episodeId')
    if not room:
        logger.warning(f"Missing room parameter for studio, using episodeId: {episode_id}")
        room = episode_id
    if not episode_id or room != episode_id:
        logger.error(f"Invalid studio parameters: room={room}, episodeId={episode_id}")
        return jsonify({"error": "Room must match episodeId"}), 400
    return render_template('recordingstudio/recording_studio.html')

@recording_studio_bp.route('/greenroom', methods=['GET'])
def greenroom():
    guest_id = request.args.get("guestId")
    token = request.args.get("token")
    episode_id = request.args.get("episodeId")
    room = request.args.get("room")

    if not all([guest_id, episode_id, room, token]):
        logger.error(f"Missing greenroom parameters: guestId={guest_id}, episodeId={episode_id}, room={room}")
        return jsonify({"error": "Missing required parameters"}), 400

    if room != episode_id:
        logger.error(f"Validation failed: Room {room} does not match episodeId {episode_id}")
        return jsonify({"error": "Room must match episodeId"}), 400

    if not validate_invitation(episode_id, guest_id, token):
        logger.error(f"Invalid invitation for episode_id={episode_id}, guest_id={guest_id}")
        return jsonify({"error": "Invalid or expired invitation"}), 403

    logger.info(f"Rendering greenroom: guestId={guest_id}, episodeId={episode_id}, room={room}")
    return render_template("greenroom/greenroom.html", guestId=guest_id, token=token, episodeId=episode_id, room=room)