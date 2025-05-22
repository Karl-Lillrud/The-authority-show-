from flask import request, jsonify, Blueprint, g
import logging
from backend.repository.podcast_repository import PodcastRepository

# Define Blueprint
podcast_bp = Blueprint("podcast_bp", __name__)

# Create repository instance
podcast_repo = PodcastRepository()  # Uses Podcasts collection internally

# Configure logger
logger = logging.getLogger(__name__)

# SHOULD ONLY BE USED FOR SPECIFIC DATA CRUD OPERATIONS
# EXTRA FUNCTIONALITY BESIDES CRUD OPERATIONS SHOULD BE IN SERVICES


@podcast_bp.route("/api/podcasts", methods=["POST"])  # Changed from /add_podcasts
def add_podcast():
    """Adds a podcast to the system."""
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        response, status_code = podcast_repo.add_podcast(g.user_id, data)
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to add podcast: {str(e)}"}), 500


@podcast_bp.route("/get_podcasts", methods=["GET"])
def get_podcasts():
    """Gets all podcasts for the current user."""
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        response, status_code = podcast_repo.get_podcasts(g.user_id)
        # Ensure the response includes the 'image' field for each podcast
        # If not, update the repository to include it in the returned data
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to fetch podcasts: {str(e)}"}), 500


@podcast_bp.route("/get_podcasts/<podcast_id>", methods=["GET"])
def get_podcast_by_id(podcast_id):
    """Gets a podcast by its ID."""
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        response, status_code = podcast_repo.get_podcast_by_id(g.user_id, podcast_id)
        # Ensure the response includes the 'image' field for the podcast
        # If not, update the repository to include it in the returned data
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to fetch podcast by ID: {str(e)}"}), 500


@podcast_bp.route("/api/podcasts/<podcast_id>", methods=["PUT"])  # Changed from /edit_podcasts/<podcast_id>
def edit_podcast(podcast_id):
    """Updates a podcast's information."""
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        response, status_code = podcast_repo.edit_podcast(g.user_id, podcast_id, data)
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to edit podcast: {str(e)}"}), 500


@podcast_bp.route("/delete_podcasts/<podcast_id>", methods=["DELETE"])
def delete_podcast(podcast_id):
    """Deletes a podcast by its ID."""
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        response, status_code = podcast_repo.delete_podcast(g.user_id, podcast_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to delete podcast: {str(e)}"}), 500


# NOTE: The endpoint '/add_episode' called by the frontend (registerEpisode in episodeRequest.js)
# is NOT defined in this blueprint. It should be handled in a separate
# episode-specific blueprint (e.g., episode_bp in episode.py) which uses
# an EpisodeRepository to save episode data linked to a podcastId and accountId.
# Ensure that endpoint exists and correctly handles user authentication and data saving.


@podcast_bp.route("/fetch_rss", methods=["POST"])
def fetch_rss():
    """
    Fetch RSS feed data or add a podcast based on RSS feed.
    """
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data or "rssUrl" not in data:
        return jsonify({"error": "No RSS URL provided"}), 400

    rss_url = data["rssUrl"]
    add_podcast_flag = data.get("addPodcast", False)  # Check if podcast should be added

    try:
        if add_podcast_flag:
            # Add podcast using RSS data
            response, status_code = podcast_repo.addPodcastWithRss(g.user_id, rss_url)
        else:
            # Fetch RSS data only
            response, status_code = podcast_repo.fetch_rss_feed(rss_url)

        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to process RSS feed: {str(e)}"}), 500
