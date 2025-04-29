from flask import request, jsonify, Blueprint, g, render_template
from backend.repository.episode_repository import EpisodeRepository
from backend.repository.podcast_repository import PodcastRepository
from backend.repository.guest_repository import GuestRepository
from backend.services.activity_service import ActivityService
import logging

guest_repo = GuestRepository()
episode_bp = Blueprint("episode_bp", __name__)
episode_repo = EpisodeRepository()
podcast_repo = PodcastRepository()
activity_service = ActivityService()  # Lägg till ActivityService
logger = logging.getLogger(__name__)


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
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    # Check if the episode is published before updating
    try:
        episode_data, status_code = episode_repo.get_episode(episode_id, g.user_id)
        if status_code != 200:
            return (
                jsonify(episode_data),
                status_code,
            )  # Return original error if not found or other issue
        if episode_data.get("status") == "published":
            return (
                jsonify({"error": "Published episodes cannot be modified"}),
                403,
            )  # Forbidden
    except Exception as e:
        logger.error(f"Error checking episode status before update: {e}")
        return jsonify({"error": "Failed to check episode status"}), 500

    data = request.get_json()
    response, status = episode_repo.update_episode(episode_id, g.user_id, data)
    if status == 200:
        # Logga aktivitet för att uppdatera episod
        activity_service.log_activity(
            user_id=g.user_id,
            activity_type="episode_updated",
            description=f"Updated episode '{data.get('title', 'Unknown')}'",
            details={"episodeId": episode_id},
        )
    return jsonify(response), status


@episode_bp.route("/episode/<episode_id>", methods=["GET"])
def episode_detail(episode_id):
    try:
        episode, podcast = episode_repo.get_episode_detail_with_podcast(episode_id)
        if not episode:
            return render_template("404.html")

        # Hämta gäster kopplade till avsnittet
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
