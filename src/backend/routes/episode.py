from flask import request, jsonify, Blueprint, g, render_template
import logging

# Import the repository
from backend.repository.episode_repository import EpisodeRepository
from backend.database.mongo_connection import episodes

# Define Blueprint
episode_bp = Blueprint("episode_bp", __name__)

# Create repository instance
episode_repo = EpisodeRepository()

# SHOULD ONLY BE USED FOR SPECIFIC DATA CRUD OPERATIONS
# EXTRA FUNCTIONALITY BESIDES CRUD OPERATIONS SHOULD BE IN SERVICES

logger = logging.getLogger(__name__)


@episode_bp.route("/add_episode", methods=["POST"])
def add_episode():
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
        response, status_code = episode_repo.add_episode(data, g.user_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to add episode: {str(e)}"}), 500


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
        # Fetch the episode document using the episode ID
        ep = episodes.find_one({"_id": episode_id})
        if not ep:
            return render_template("404.html")

        # Render a dedicated episode page template and pass the episode data
        return render_template("landingpage/episode.html", episode=ep)
    except Exception as e:
        return f"Error: {str(e)}", 500


@episode_bp.route("/episodes/by_podcast/<podcast_id>", methods=["GET"])
def get_episodes_by_podcast(podcast_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Query the episodes collection for documents matching the given podcast_id
        episodes_cursor = episodes.find({"podcast_id": podcast_id})
        mapped_episodes = []

        for ep in episodes_cursor:
            title = ep.get("title", "No Title")
            description = ep.get("description", "No Description")
            publish_date = ep.get("publishDate")
            duration = ep.get("duration", "Unknown")
            episode_type = ep.get("episodeType", "Unknown")
            link = ep.get("link", "No Link")
            author = ep.get("author", "Unknown")
            file_size = ep.get("fileSize", "Unknown")
            file_type = ep.get("fileType", "Unknown")
            audio_url = ep.get("audioUrl", None)

            mapped_episodes.append(
                {
                    "_id": ep.get("_id"),
                    "title": title,
                    "description": description,
                    "publishDate": publish_date,
                    "duration": duration,
                    "episodeType": episode_type,
                    "link": link,
                    "author": author,
                    "fileSize": file_size,
                    "fileType": file_type,
                    "audioUrl": audio_url,
                }
            )

        # Return the mapped episodes list
        return jsonify({"episodes": mapped_episodes}), 200

    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to fetch episodes by podcast: {str(e)}"}), 500


@episode_bp.route("/episodes/get_episodes_by_guest/<guest_id>", methods=["GET"])
def get_episodes_by_guest(guest_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        response, status_code = episode_repo.get_episodes_by_guest(guest_id, g.user_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to fetch episodes by guest: {str(e)}"}), 500


@episode_bp.route("/episodes/view_tasks_by_episode/<episode_id>", methods=["GET"])
def view_tasks_by_episode(episode_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        response, status_code = episode_repo.get_tasks_by_episode(episode_id, g.user_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to fetch tasks by episode: {str(e)}"}), 500


@episode_bp.route("/episodes/add_tasks_to_episode", methods=["POST"])
def add_tasks_to_episode():
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
        response, status_code = episode_repo.add_tasks_to_episode(data, g.user_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to add tasks to episode: {str(e)}"}), 500


@episode_bp.route("/episodes/count_by_guest/<guest_id>", methods=["GET"])
def count_episodes_by_guest(guest_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        response, status_code = episode_repo.count_episodes_by_guest(guest_id, g.user_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to count episodes by guest: {str(e)}"}), 500