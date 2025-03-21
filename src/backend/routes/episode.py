from flask import request, jsonify, Blueprint, g, render_template
import logging

# Import the repository
from backend.repository.episode_repository import EpisodeRepository
from backend.repository.podcast_repository import PodcastRepository  # ✅ Import Podcast Repo
from backend.database.mongo_connection import episodes, podcasts  # ✅ Ensure we can fetch podcasts

# Define Blueprint
episode_bp = Blueprint("episode_bp", __name__)

# Create repository instance
episode_repo = EpisodeRepository()
podcast_repo = PodcastRepository()

# SHOULD ONLY BE USED FOR SPECIFIC DATA CRUD OPERATIONS
# EXTRA FUNCTIONALITY BESIDES CRUD OPERATIONS SHOULD BE IN SERVICES

logger = logging.getLogger(__name__)


@episode_bp.route("/register_episode", methods=["POST"])
def register_episode():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Validate Content-Type
    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    try:
        data = request.get_json()
        response, status_code = episode_repo.register_episode(data, g.user_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to register episode: {str(e)}"}), 500


@episode_bp.route("/get_episodes/<episode_id>", methods=["GET"])
def get_episode(episode_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        response, status_code = episode_repo.get_episode(episode_id, g.user_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to fetch episode: {str(e)}"}), 500


@episode_bp.route("/get_episodes", methods=["GET"])
def get_episodes():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        response, status_code = episode_repo.get_episodes(g.user_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to fetch episodes: {str(e)}"}), 500


@episode_bp.route("/delete_episods/<episode_id>", methods=["DELETE"])
def delete_episode(episode_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        response, status_code = episode_repo.delete_episode(episode_id, g.user_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to delete episode: {str(e)}"}), 500


@episode_bp.route("/update_episodes/<episode_id>", methods=["PUT"])
def update_episode(episode_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Validate Content-Type
    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    try:
        data = request.get_json()
        response, status_code = episode_repo.update_episode(episode_id, g.user_id, data)
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to update episode: {str(e)}"}), 500


@episode_bp.route("/episode/<episode_id>", methods=["GET"])
def episode_detail(episode_id):
    try:
        # ✅ Fetch the episode document
        ep = episodes.find_one({"_id": episode_id})

        if not ep:
            return render_template("404.html")  # Handle missing episode case

        # ✅ Ensure `podcast_id` exists in episode
        podcast_id = ep.get("podcast_id")
        podcast_doc = podcasts.find_one({"_id": podcast_id}) or {}

        # ✅ Extract podcast logo safely
        podcast_logo = podcast_doc.get("logoUrl", "")

        # ✅ Validate `podcast_logo` (must be a valid URL or Base64)
        if not isinstance(podcast_logo, str) or not podcast_logo.startswith(("http", "data:image")):
            podcast_logo = "/static/images/default.png"  # Default fallback

        # ✅ Extract the episode's `audioUrl` safely
        audio_url = ep.get("audioUrl", "")

        # ✅ Validate `audio_url`
        if not isinstance(audio_url, str) or not audio_url.startswith(("http", "https")):
            audio_url = None  # Avoid passing invalid audio URLs

        # ✅ Pass episode, podcast logo, and audio URL to the template
        return render_template(
            "landingpage/episode.html",
            episode=ep,
            podcast_logo=podcast_logo,
            audio_url=audio_url,  # ✅ Make sure this is available in the template
        )

    except Exception as e:
        print("❌ ERROR:", str(e))  # Print the full error in console
        return f"Error: {str(e)}", 500




@episode_bp.route("/episodes/by_podcast/<podcast_id>", methods=["GET"])
def get_episodes_by_podcast(podcast_id):
    """Fetch all episodes for a given podcast."""
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    episodes, status_code = episode_repo.get_episodes_by_podcast(podcast_id, g.user_id)
    return jsonify(episodes), status_code
