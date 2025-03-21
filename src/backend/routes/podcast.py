from flask import request, jsonify, Blueprint, g
from backend.repository.podcast_repository import PodcastRepository
import logging

# Define Blueprint
podcast_bp = Blueprint("podcast_bp", __name__)
repository = PodcastRepository()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@podcast_bp.route("/add_podcasts", methods=["POST"])
def add_podcast():
    try:
        if not hasattr(g, "user_id") or not g.user_id:
            return jsonify({"error": "Unauthorized"}), 401

        if request.content_type != "application/json":
            return (
                jsonify({"error": "Invalid Content-Type. Expected application/json"}),
                415,
            )

        data = request.get_json()
        if not data:
            logger.error("No data provided")  # Added log
            return jsonify({"error": "No data provided"}), 400  # Handle empty data

        logger.info(f"Received data for adding podcast: {data}")  # Added log
        response, status = repository.add_podcast(g.user_id, data)
        return jsonify(response), status

    except Exception as e:
        logger.error(f"Error adding podcast: {str(e)}", exc_info=True)  # Added log
        return jsonify({"error": "Failed to add podcast", "details": str(e)}), 500


@podcast_bp.route("/get_podcasts", methods=["GET"])
def get_podcasts():
    try:
        if not hasattr(g, "user_id") or not g.user_id:
            return jsonify({"error": "Unauthorized"}), 401

        response, status = repository.get_podcasts(g.user_id)
        return jsonify(response), status

    except Exception as e:
        logger.error(f"Error fetching podcasts: {str(e)}")
        return jsonify({"error": "Failed to fetch podcasts", "details": str(e)}), 500


@podcast_bp.route("/get_podcasts/<podcast_id>", methods=["GET"])
def get_podcast_by_id(podcast_id):
    try:
        if not hasattr(g, "user_id") or not g.user_id:
            return jsonify({"error": "Unauthorized"}), 401

        response, status = repository.get_podcast_by_id(g.user_id, podcast_id)
        return jsonify(response), status

    except Exception as e:
        logger.error(f"Error fetching podcast by ID {podcast_id}: {str(e)}")
        return (
            jsonify({"error": "Failed to fetch podcast by ID", "details": str(e)}),
            500,
        )


@podcast_bp.route("/delete_podcasts/<podcast_id>", methods=["DELETE"])
def delete_podcast(podcast_id):
    try:
        if not hasattr(g, "user_id") or not g.user_id:
            return jsonify({"error": "Unauthorized"}), 401

        response, status = repository.delete_podcast(g.user_id, podcast_id)
        return jsonify(response), status

    except Exception as e:
        logger.error(f"Error deleting podcast {podcast_id}: {str(e)}")
        return jsonify({"error": "Failed to delete podcast", "details": str(e)}), 500


@podcast_bp.route("/edit_podcasts/<podcast_id>", methods=["PUT"])
def edit_podcast(podcast_id):
    try:
        if not hasattr(g, "user_id") or not g.user_id:
            return jsonify({"error": "Unauthorized"}), 401

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400  # Handle empty data

        response, status = repository.edit_podcast(g.user_id, podcast_id, data)
        return jsonify(response), status

    except Exception as e:
        logger.error(f"Error editing podcast {podcast_id}: {str(e)}")
        return jsonify({"error": "Failed to edit podcast", "details": str(e)}), 500


@podcast_bp.route("/fetch_rss", methods=["GET"])
def fetch_rss():
    """Server-side RSS feed fetching for clients that might have CORS issues."""
    rss_url = request.args.get("url")
    if not rss_url:
        return jsonify({"error": "No RSS URL provided"}), 400

    response, status_code = repository.fetch_rss_feed(rss_url)
    return jsonify(response), status_code
