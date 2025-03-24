from flask import request, jsonify, Blueprint, g, render_template
from backend.repository.episode_repository import EpisodeRepository
from backend.repository.podcast_repository import PodcastRepository
import logging

episode_bp = Blueprint("episode_bp", __name__)
episode_repo = EpisodeRepository()
podcast_repo = PodcastRepository()
logger = logging.getLogger(__name__)


@episode_bp.route("/register_episode", methods=["POST"])
def register_episode():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        data = request.get_json()
        return episode_repo.register_episode(data, g.user_id)
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": str(e)}), 500


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


@episode_bp.route("/delete_episods/<episode_id>", methods=["DELETE"])
def delete_episode(episode_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    return episode_repo.delete_episode(episode_id, g.user_id)


@episode_bp.route("/update_episodes/<episode_id>", methods=["PUT"])
def update_episode(episode_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415
    data = request.get_json()
    return episode_repo.update_episode(episode_id, g.user_id, data)


@episode_bp.route("/episode/<episode_id>", methods=["GET"])
def episode_detail(episode_id):
    try:
        episode, podcast = episode_repo.get_episode_detail_with_podcast(episode_id)
        if not episode:
            return render_template("404.html")

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
        )
    except Exception as e:
        logger.error("❌ ERROR in episode_detail: %s", str(e))
        return f"Error: {str(e)}", 500


@episode_bp.route("/episodes/by_podcast/<podcast_id>", methods=["GET"])
def get_episodes_by_podcast(podcast_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    return episode_repo.get_episodes_by_podcast(podcast_id, g.user_id)
