from flask import (
    request,
    jsonify,
    Blueprint,
    g,
    render_template,
    send_from_directory,
    url_for,
)
from backend.repository.episode_repository import EpisodeRepository
from backend.repository.podcast_repository import PodcastRepository
from backend.repository.guest_repository import GuestRepository
from backend.services.activity_service import ActivityService
import logging
import os
from werkzeug.utils import secure_filename

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
    # Validate based on 'podcast_id' (snake_case)
    if not data.get("podcast_id") or not data.get("title"):
        logger.warning(f"Missing podcast_id or title in add_episode request. Data: {data}")
        return jsonify({"error": "Missing podcast_id or title"}), 400

    response, status = episode_repo.register_episode(data, g.user_id)

    return jsonify(response), status


@episode_bp.route("/get_episodes/<episode_id>", methods=["GET"])
def get_episode(episode_id):
    if not hasattr(g, "user_id") or not g.user_id:
        logger.warning("Unauthorized attempt to get episode: No user_id in g")
        return jsonify({"error": "User not authenticated"}), 401
    return episode_repo.get_episode(episode_id, g.user_id)


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


@episode_bp.route("/update_episodes/<episode_id>", methods=["PUT"])
def update_episode(episode_id):
    # --- Start Debug Logging ---
    logger.debug(f"Update request received for episode {episode_id}")
    logger.debug(f"Request Headers: {request.headers}")
    logger.debug(f"Request Content-Type: {request.content_type}")
    logger.debug(f"Request Content-Length: {request.content_length}")
    # --- End Debug Logging ---

    if not hasattr(g, "user_id") or not g.user_id:
        logger.warning(f"Unauthorized attempt to update episode {episode_id}: No user_id in g")
        return jsonify({"error": "User not authenticated"}), 401

    # Check if the episode exists and belongs to the user
    try:
        existing_episode, _ = episode_repo.get_episode(episode_id, g.user_id)
        if not existing_episode or existing_episode.get("error"):
            logger.warning(f"Episode {episode_id} not found or user {g.user_id} not authorized.")
            return jsonify({"error": "Episode not found or not authorized"}), 404
    except Exception as e:
        logger.error(f"Error checking episode existence for {episode_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to verify episode"}), 500

    data = {}
    audio_file = None

    content_type = request.content_type

    if content_type and content_type.startswith("multipart/form-data"):
        logger.debug("Processing multipart/form-data for episode update")
        data = request.form.to_dict()
        if "audioFile" in request.files:
            audio_file = request.files["audioFile"]
            logger.debug(f"Audio file '{audio_file.filename}' received in multipart form.")

    elif content_type and content_type == "application/json":
        logger.debug("Processing application/json for episode update")
        data = request.get_json() or {}

    else:
        logger.warning(f"Unsupported content type for episode update: {content_type}")
        return jsonify({"error": f"Unsupported content type: {content_type}"}), 415

    if not data and not audio_file:
        logger.warning("No data or audio file provided for episode update.")
        return jsonify({"error": "No data or audio file provided"}), 400

    if audio_file and audio_file.filename != "":
        filename = secure_filename(audio_file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        audio_file.save(file_path)
        data["audioUrl"] = url_for("episode_bp.uploaded_audio_file", filename=filename, _external=True)
        data["fileSize"] = os.path.getsize(file_path)
        data["fileType"] = audio_file.mimetype
        logger.info(f"Audio file saved: {file_path}, URL: {data['audioUrl']}")

    elif "audioFile" in request.files and request.files["audioFile"].filename == "":
        logger.debug("audioFile field present in form but no file was uploaded.")

    if "duration" in data and data["duration"]:
        try:
            data["duration"] = int(data["duration"])
        except (ValueError, TypeError):
            logger.warning(f"Invalid duration value '{data['duration']}', setting to None.")
            data["duration"] = None
    elif "duration" in data and not data["duration"]:
        logger.debug("Duration field is empty, setting to None.")
        data["duration"] = None

    logger.debug(f"Calling episode_repo.update_episode with final data: {data}")
    response, status = episode_repo.update_episode(episode_id, g.user_id, data)

    return jsonify(response), status


@episode_bp.route("/uploads/episode_audio/<filename>")
def uploaded_audio_file(filename):
    logger.debug(f"Serving uploaded audio file: {filename} from {UPLOAD_FOLDER}")
    return send_from_directory(UPLOAD_FOLDER, filename)


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
    return episode_repo.get_episodes_by_podcast(podcast_id, g.user_id)


@episode_bp.route("/episode/new", methods=["GET"])
def new_episode():
    try:
        return jsonify({"message": "New episode endpoint is working!"}), 200
    except Exception as e:
        logger.error("❌ ERROR in new_episode: %s", str(e))
        return jsonify({"error": "Failed to process the request"}), 500
