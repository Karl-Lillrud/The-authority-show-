from flask import (
    request,
    jsonify,
    Blueprint,
    g,
    render_template,
    send_from_directory,
)  # Lägg till send_from_directory
from backend.repository.episode_repository import EpisodeRepository
from backend.repository.podcast_repository import PodcastRepository
from backend.repository.guest_repository import GuestRepository
from backend.services.activity_service import ActivityService
import logging
import os  # Add os import for file handling
from werkzeug.utils import secure_filename  # For secure filenames

guest_repo = GuestRepository()
episode_bp = Blueprint("episode_bp", __name__)
episode_repo = EpisodeRepository()
podcast_repo = PodcastRepository()
activity_service = ActivityService()  # Lägg till ActivityService
logger = logging.getLogger(__name__)

# Define a simple upload folder (configure properly in production)
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "episode_audio")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure directory exists


@episode_bp.route("/add_episode", methods=["POST"])
def add_episode():
    if not getattr(g, "user_id", None):
        return jsonify({"error": "Unauthorized"}), 401
    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    data = request.get_json() or {}
    if not data.get("podcastId") or not data.get("title"):
        return jsonify({"error": "Missing required fields: podcastId or title"}), 400

    response, status = episode_repo.register_episode(data, g.user_id)

    return jsonify(response), status


@episode_bp.route("/get_episodes/<episode_id>", methods=["GET"])
def get_episode(episode_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    return episode_repo.get_episode(episode_id, g.user_id)


@episode_bp.route("/get_episodes", methods=["GET"])
def get_episodes():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    return episode_repo.get_episodes(g.user_id)


@episode_bp.route("/delete_episodes/<episode_id>", methods=["DELETE"])
def delete_episode(episode_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    response, status = episode_repo.delete_episode(episode_id, g.user_id)
    if status == 200:
        # Logga aktivitet för att ta bort episod
        activity_service.log_activity(
            user_id=g.user_id,
            activity_type="episode_deleted",
            description=f"Deleted episode with ID '{episode_id}'",
            details={"episodeId": episode_id},
        )
    return response, status


@episode_bp.route("/update_episodes/<episode_id>", methods=["PUT"])
def update_episode(episode_id):
    # --- Start Debug Logging ---
    logger.debug(f"Update request received for episode {episode_id}")
    # Log all headers for detailed debugging
    logger.debug(f"Request Headers: {request.headers}")
    logger.debug(f"Request Content-Type: {request.content_type}")
    logger.debug(f"Request Content-Length: {request.content_length}")
    # --- End Debug Logging ---

    if not hasattr(g, "user_id") or not g.user_id:
        logger.warning(f"Unauthorized attempt to update episode {episode_id}")
        return jsonify({"error": "Unauthorized"}), 401

    # Check if the episode exists and belongs to the user
    try:
        episode_data, status_code = episode_repo.get_episode(episode_id, g.user_id)
        if status_code != 200:
            logger.warning(
                f"Episode {episode_id} not found or access denied for user {g.user_id}. Status: {status_code}"
            )
            return jsonify(episode_data), status_code
    except Exception as e:
        logger.error(
            f"Error checking episode status before update for {episode_id}: {e}",
            exc_info=True,
        )
        return jsonify({"error": "Failed to check episode status"}), 500

    data = {}
    audio_file = None

    # Use request.mimetype for a cleaner check? Or stick with content_type
    content_type = request.content_type

    if content_type and content_type.startswith("multipart/form-data"):
        logger.debug("Processing request as multipart/form-data")
        try:
            # Accessing request.form or request.files might trigger parsing
            data = request.form.to_dict()
            logger.debug(f"Extracted form data: {data}")
            if "audioFile" in request.files:
                audio_file = request.files["audioFile"]
                # Avoid logging the entire file object, just filename
                logger.debug(
                    f"Audio file found in request.files: {audio_file.filename}, Content-Type: {audio_file.content_type}"
                )
            else:
                logger.debug("No 'audioFile' found in request.files")
        except Exception as e:
            # Log the specific error during parsing
            logger.error(f"Error parsing multipart/form/data: {e}", exc_info=True)
            return jsonify({"error": "Failed to parse multipart form data"}), 400

    elif content_type and content_type == "application/json":
        logger.debug("Processing request as application/json")
        try:
            # Ensure get_json is called correctly
            data = request.get_json(
                silent=True
            )  # Use silent=True to avoid exception on invalid JSON
            if data is None:
                # Check request.data if get_json returned None
                raw_data = request.data
                logger.warning(
                    f"Received application/json request but failed to parse JSON. Raw data: {raw_data[:200]}..."
                )  # Log first 200 chars
                return jsonify({"error": "Invalid JSON data received"}), 400
            logger.debug(f"Extracted JSON data: {data}")
        except Exception as e:
            # Catch any other unexpected errors during JSON processing
            logger.error(
                f"Error processing application/json request: {e}", exc_info=True
            )
            return jsonify({"error": "Failed to process JSON data"}), 400
    else:
        # Log if content_type is missing or unsupported
        logger.warning(f"Unsupported or missing Content-Type received: {content_type}")
        return (
            jsonify({"error": f"Unsupported or missing Content-Type: {content_type}"}),
            415,
        )

    # Check if data is empty after parsing attempts (could happen if form has only file)
    if not data and not audio_file:
        logger.warning("Request parsing resulted in no data fields and no audio file.")
        # Consider if this is an error. If only a file is sent, data might be empty.
        # If audio_file exists, proceed. If not, maybe return error.
        if not audio_file:
            return jsonify({"error": "No update data or file provided"}), 400

    # Process file upload if present
    if audio_file and audio_file.filename != "":
        logger.debug(f"Processing uploaded file: {audio_file.filename}")
        try:
            # Ensure filename is secure
            filename = secure_filename(f"{episode_id}_{audio_file.filename}")
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            logger.debug(f"Saving file to: {filepath}")
            audio_file.save(filepath)

            # Update data dictionary with file metadata
            # !!! IMPORTANT: Replace with actual cloud storage URL later !!!
            data["audioUrl"] = f"/uploads/episode_audio/{filename}"  # Placeholder
            data["fileSize"] = str(os.path.getsize(filepath))
            data["fileType"] = audio_file.content_type
            logger.info(
                f"Audio file saved for episode {episode_id} at {filepath}. Metadata added to data dict."
            )

        except Exception as e:
            logger.error(
                f"Error saving uploaded audio file for episode {episode_id}: {e}",
                exc_info=True,
            )
            return jsonify({"error": "Failed to process uploaded audio file"}), 500
    elif "audioFile" in request.files and request.files["audioFile"].filename == "":
        logger.debug(
            "An 'audioFile' part was present but no file was selected/uploaded."
        )
        # Decide if you need to clear existing audioUrl if no new file is provided
        # data['audioUrl'] = None # Example: Clear audioUrl if no file is uploaded

    # Convert duration back to int if present and valid
    if "duration" in data and data["duration"]:
        try:
            data["duration"] = int(data["duration"])
        except (ValueError, TypeError):
            logger.warning(
                f"Invalid duration value received: {data['duration']}. Setting to None."
            )
            data["duration"] = None  # Set to None if invalid
    elif "duration" in data and not data["duration"]:
        # Handle empty string for duration
        data["duration"] = None

    # Ensure boolean fields are handled correctly if needed (e.g., explicit, isHidden)
    # Example: data['explicit'] = str(data.get('explicit', '')).lower() in ['true', 'on', '1']

    # Log the final data being sent to the repository
    logger.debug(f"Calling episode_repo.update_episode with final data: {data}")
    response, status = episode_repo.update_episode(episode_id, g.user_id, data)
    logger.debug(f"Repository update response status: {status}, body: {response}")

    if status == 200:
        # Log activity for successful update
        try:
            activity_service.log_activity(
                user_id=g.user_id,
                activity_type="episode_updated",
                description=f"Updated episode '{data.get('title', episode_data.get('title', 'Unknown'))}'",
                details={"episodeId": episode_id},
            )
        except Exception as act_err:
            logger.error(
                f"Failed to log episode_updated activity: {act_err}", exc_info=True
            )

    return jsonify(response), status


# --- Ny route för att servera uppladdade ljudfiler (ENDAST FÖR UTVECKLING) ---
@episode_bp.route("/uploads/episode_audio/<filename>")
def uploaded_audio_file(filename):
    """Serves files from the UPLOAD_FOLDER. Development only."""
    logger.debug(f"Attempting to serve file: {filename} from {UPLOAD_FOLDER}")
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except FileNotFoundError:
        logger.error(f"File not found: {filename} in {UPLOAD_FOLDER}")
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        logger.error(f"Error serving file {filename}: {e}", exc_info=True)
        return jsonify({"error": "Error serving file"}), 500


# --- Slut på ny route ---


@episode_bp.route("/episode/<episode_id>", methods=["GET"])
def episode_detail(episode_id):
    try:
        episode, podcast = episode_repo.get_episode_detail_with_podcast(episode_id)
        if not episode:
            return render_template("404.html")

        # Get guests connected to episode
        guests_response, status = guest_repo.get_guests_by_episode(episode_id)
        guests = guests_response.get("guests", []) if status == 200 else []

        podcast_logo = podcast.get("logoUrl", "")
        if not isinstance(podcast_logo, str) or not podcast_logo.startswith(
            ("http", "data:image")
        ):
            podcast_logo = "/static/images/default.png"

        audio_url = episode.get("audioUrl", "")
        if not isinstance(audio_url, str) or not audio_url.startswith(
            ("http", "https")
        ):
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
        return jsonify({"error": "Unauthorized"}), 401
    return episode_repo.get_episodes_by_podcast(podcast_id, g.user_id)


@episode_bp.route("/episode/new", methods=["GET"])
def new_episode():
    try:
        # Example logic for creating a new episode
        return jsonify({"message": "New episode endpoint is working!"}), 200
    except Exception as e:
        logger.error("❌ ERROR in new_episode: %s", str(e))
        return jsonify({"error": "Failed to process the request"}), 500
