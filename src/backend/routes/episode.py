from flask import (
    request,
    jsonify,
    Blueprint,
    g,
    render_template,
)
from backend.repository.episode_repository import EpisodeRepository
from backend.repository.podcast_repository import PodcastRepository
from backend.repository.guest_repository import GuestRepository
from backend.services.activity_service import ActivityService
import logging
import os
from datetime import datetime
from backend.database.mongo_connection import database

invitations_collection = database.GuestInvitations
guest_repo = GuestRepository()
episode_bp = Blueprint("episode_bp", __name__)
episode_repo = EpisodeRepository()
podcast_repo = PodcastRepository()
activity_service = ActivityService()
logger = logging.getLogger(__name__)

# Define a simple upload folder (configure properly in production)
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "episode_audio")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure directory exists


@episode_bp.route("/add_episode", methods=["POST"])
def add_episode():
    if not getattr(g, "user_id", None):
        logger.warning("Unauthorized attempt to add episode: No user_id in g")
        return jsonify({"error": "User not authenticated"}), 401

    if request.content_type != "application/json":
        logger.warning(f"Invalid content type for add_episode: {request.content_type}")
        return jsonify({"error": "Invalid content type, expected application/json"}), 415

    data = request.get_json() or {}

    if not data.get("podcastId") or not data.get("title"):
        logger.warning(f"Missing podcastId or title in add_episode request. Data: {data}")
        return jsonify({"error": "Missing podcastId or title"}), 400

    response, status = episode_repo.register_episode(data, g.user_id)

    return jsonify(response), status


@episode_bp.route("/get_episodes/<episode_id>", methods=["GET"])
def get_episode(episode_id):
    user_id = getattr(g, "user_id", None)

    if not user_id:

        token = (
            request.args.get("token")
            or request.headers.get("Authorization", "").replace("Bearer ", "")
        )

        if not token:
            logger.warning("Unauthorized attempt to get episode: Missing token")
            return jsonify({"error": "User not authenticated"}), 401

        invitation = invitations_collection.find_one({
            "invite_token": token,
            "episode_id": episode_id,
            "expires_at": {"$gt": datetime.utcnow()}
        })

        if not invitation:
            logger.warning("Unauthorized attempt: Invalid or expired token")
            return jsonify({"error": "Invalid or expired token"}), 403

        episode, status_code = episode_repo.get_episode(episode_id, None)

        if status_code != 200:
            return jsonify(episode), status_code

        return jsonify(episode), 200

    return episode_repo.get_episode(episode_id, user_id)


@episode_bp.route("/get_episodes", methods=["GET"])
def get_episodes():
    if not hasattr(g, "user_id") or not g.user_id:
        logger.warning("Unauthorized attempt to get episodes: No user_id in g")
        return jsonify({"error": "User not authenticated"}), 401
    return episode_repo.get_episodes(g.user_id)


@episode_bp.route("/delete_episodes/<episode_id>", methods=["DELETE"])
def delete_episode(episode_id):
    if not hasattr(g, "user_id") or not g.user_id:
        logger.warning("Unauthorized attempt to delete episode: No user_id in g")
        return jsonify({"error": "User not authenticated"}), 401

    response, status = episode_repo.delete_episode(episode_id, g.user_id)
    if status == 200:
        logger.info(f"Episode {episode_id} deleted successfully by user {g.user_id}")

    return jsonify(response), status


@episode_bp.route("/episodes/<episode_id>", methods=["PUT"])
def update_episode(episode_id):
    # --- Debug Logging ---
    logger.debug(f"Update request received for episode {episode_id}")
    logger.debug(f"Request Headers: {dict(request.headers)}")
    logger.debug(f"Request Content-Type: {request.content_type}")
    logger.debug(f"Request Content-Length: {request.content_length}")
    # --- End Debug Logging ---

    # Check authentication
    if not hasattr(g, "user_id") or not g.user_id:
        logger.warning(f"Unauthorized attempt to update episode {episode_id}: No user_id in g")
        return jsonify({"error": "User not authenticated"}), 401

    # Ensure content type is multipart/form-data
    content_type = request.content_type
    if not content_type or not content_type.startswith("multipart/form-data"):
        logger.warning(f"Unsupported content type for episode update: {content_type}")
        return jsonify({"error": f"Expected multipart/form-data, received {content_type or 'none'}"}), 415

    # Extract form data and file (video or audio)
    data = request.form.to_dict()
    video_file = request.files.get("video")
    audio_file = request.files.get("audioFile")
    logger.debug(f"Form data: {data}")
    logger.debug(f"Video file: {video_file.filename if video_file else None}")
    logger.debug(f"Audio file: {audio_file.filename if audio_file else None}")

    # Validate input
    if not data and not video_file and not audio_file:
        logger.warning("No data or file provided for episode update")
        return jsonify({"error": "No data or file provided"}), 400

    # If a file is uploaded, set status to 'recorded'
    if video_file or audio_file:
        data["status"] = "recorded"

    try:
        # Prefer video file if present, otherwise audio
        file_to_upload = video_file if video_file else audio_file
        response, status = episode_repo.update_episode(episode_id, g.user_id, data, audio_file=file_to_upload)
        if status == 200:
            logger.info(f"Episode {episode_id} updated successfully by user {g.user_id}")
        return jsonify(response), status
    except Exception as e:
        logger.error(f"Error updating episode {episode_id}: {e}", exc_info=True)
        return jsonify({"error": f"Failed to update episode: {str(e)}"}), 500

@episode_bp.route("/episode/<episode_id>", methods=["GET"])
def episode_detail(episode_id):
    try:
        episode, podcast = episode_repo.get_episode_detail_with_podcast(episode_id)
        if not episode:
            return render_template("404.html")

        guests_response, status = guest_repo.get_guests_by_episode(episode_id)
        guests = guests_response.get("guests", []) if status == 200 else []

        podcast_logo = podcast.get("logoUrl", "")
        if not isinstance(podcast_logo, str) or not podcast_logo.startswith(("http", "data:image")):
            podcast_logo = "/static/images/default.png"

        audio_url = episode.get("audioUrl", "")
        if not isinstance(audio_url, str) or not audio_url.startswith(("http", "https")):
            audio_url = None

        return render_template(
            "landingpage/episode.html",
            episode=episode,
            podcast_logo=podcast_logo,
            audio_url=audio_url,
            guests=guests,
        )
    except Exception as e:
        logger.error("❌ ERROR in episode_detail: %s", str(e))
        return f"Error: {str(e)}", 500


@episode_bp.route("/episodes/by_podcast/<podcast_id>", methods=["GET"])
def get_episodes_by_podcast(podcast_id):
    if not hasattr(g, "user_id") or not g.user_id:
        logger.warning(f"Unauthorized attempt to get episodes for podcast {podcast_id}: No user_id in g")
        return jsonify({"error": "User not authenticated"}), 401
    
    # Get 'exclude_statuses' query parameter, e.g., ?exclude_statuses=published,archived
    exclude_statuses_str = request.args.get('exclude_statuses')
    statuses_to_exclude = [] # Default to empty list (no exclusion)
    if exclude_statuses_str:
        statuses_to_exclude = [status.strip() for status in exclude_statuses_str.split(',') if status.strip()]
        logger.info(f"Request to fetch episodes for podcast {podcast_id}, excluding statuses: {statuses_to_exclude}")

    # Pass the list of statuses to exclude to the repository method
    # If statuses_to_exclude is empty, the repository method will fetch all episodes.
    return episode_repo.get_episodes_by_podcast(podcast_id, g.user_id, exclude_statuses=statuses_to_exclude)


@episode_bp.route("/episode/new", methods=["GET"])
def new_episode():
    try:
        return jsonify({"message": "New episode endpoint is working!"}), 200
    except Exception as e:
        logger.error("❌ ERROR in new_episode: %s", str(e))
        return jsonify({"error": "Failed to process the request"}), 500
