from flask import Blueprint, render_template, url_for, request, jsonify, abort
from datetime import datetime, timezone, timedelta
from bson import ObjectId, errors as bson_errors # Import bson_errors for InvalidId
import logging # Add missing import for logging

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
    episode_id_str = request.args.get('episodeId') 
    
    if not room:
        logger.warning("Studio accessed without room ID.")
        abort(400, "Room ID is required.")
        
    if not episode_id_str or room != episode_id_str:
        logger.warning(f"Studio accessed with mismatched room ({room}) and episodeId ({episode_id_str}).")
        abort(400, "Room ID and Episode ID mismatch or Episode ID is missing.")

    query_filter = None
    if ObjectId.is_valid(episode_id_str):
        try:
            query_filter = {"_id": ObjectId(episode_id_str)}
        except bson_errors.InvalidId:
            logger.warning(f"ObjectId.is_valid passed but ObjectId() failed for: {episode_id_str}. Querying as string.")
            query_filter = {"_id": episode_id_str} # Fallback to string query
    else:
        # If it's not a valid ObjectId hex string, assume it's a string ID (e.g., UUID)
        query_filter = {"_id": episode_id_str}
    
    episode = episodes_collection.find_one(query_filter)

    if not episode:
        logger.error(f"Episode not found for ID: {episode_id_str} in /studio route using filter {query_filter}")
        abort(404, "Episode not found.")

    recording_at_iso = None
    if episode.get("recordingAt"):
        # Ensure recordingAt is datetime before calling isoformat
        recording_at_dt = episode["recordingAt"]
        if isinstance(recording_at_dt, datetime):
            recording_at_iso = recording_at_dt.isoformat()
        else:
            logger.warning(f"Episode {episode_id_str} has non-datetime recordingAt: {recording_at_dt}")
        
    # Check if recording time has passed by more than a reasonable duration (e.g., 12 hours)
    # This is a basic check; more sophisticated logic might be needed
    if episode.get("recordingAt") and isinstance(episode.get("recordingAt"), datetime) and \
       datetime.now(timezone.utc) > episode["recordingAt"] + timedelta(hours=12):
        logger.info(f"Recording time for episode {episode_id_str} has significantly passed. Studio access might be limited.")
        # Potentially redirect or show a message, but for now, just log

    return render_template(
        "recordingstudio/recording_studio.html", 
        room=room, 
        episode_id=episode_id_str,
        recording_at_iso=recording_at_iso,
        episode_title=episode.get("title", "Recording Studio")
    )


@recording_studio_bp.route('/greenroom', methods=['GET'])
def greenroom():
    episode_id_str = request.args.get('episodeId')
    guest_id_str = request.args.get('guestId') 
    # token = request.args.get('token') 

    if not episode_id_str:
        logger.warning("Greenroom accessed without episodeId.")
        abort(400, "Episode ID is required for the greenroom.")

    query_filter = None
    if ObjectId.is_valid(episode_id_str):
        try:
            query_filter = {"_id": ObjectId(episode_id_str)}
        except bson_errors.InvalidId:
            logger.warning(f"ObjectId.is_valid passed but ObjectId() failed for: {episode_id_str} in greenroom. Querying as string.")
            query_filter = {"_id": episode_id_str} # Fallback to string query
    else:
        query_filter = {"_id": episode_id_str}

    episode = episodes_collection.find_one(query_filter)

    if not episode:
        logger.error(f"Episode not found for ID: {episode_id_str} in /greenroom route using filter {query_filter}")
        abort(404, "Episode not found.")

    recording_at_iso = None
    if episode.get("recordingAt"):
        recording_at_dt = episode["recordingAt"]
        if isinstance(recording_at_dt, datetime):
            recording_at_iso = recording_at_dt.isoformat()
        else:
            logger.warning(f"Episode {episode_id_str} has non-datetime recordingAt in greenroom: {recording_at_dt}")


    # Basic validation: Greenroom access should ideally be before or around recording time
    # if episode.get("recordingAt") and isinstance(episode.get("recordingAt"), datetime) and \
    #    datetime.now(timezone.utc) > episode["recordingAt"] + timedelta(hours=2):
    #     logger.info(f"Greenroom accessed significantly after recording time for episode {episode_id_str}.")
        # Potentially show a message or restrict access

    return render_template(
        "greenroom/greenroom.html", 
        episode_id=episode_id_str,
        guest_id=guest_id_str, 
        recording_at_iso=recording_at_iso,
        episode_title=episode.get("title", "Green Room")
    )