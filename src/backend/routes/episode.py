from flask import request, jsonify, Blueprint, g, render_template
import logging
from werkzeug.utils import secure_filename
from pymongo import MongoClient  # MongoDB client
import gridfs  # GridFS for file storage
from backend.repository.episode_repository import EpisodeRepository
from backend.database.mongo_connection import episodes
from backend.services.integration import get_spotify_access_token, upload_episode_to_spotify

# Initialize Blueprint and repository
episode_bp = Blueprint("episode_bp", __name__)
episode_repo = EpisodeRepository()

logger = logging.getLogger(__name__)

# MongoDB connection and GridFS setup
client = MongoClient("mongodb://localhost:27017/Podmanager")  # Replace with your MongoDB URI
db = client['Podmanager']
fs = gridfs.GridFS(db)  # Use GridFS for file storage

@episode_bp.route("/register_episode", methods=["POST"])
def register_episode():
    try:
        # Validate User
        user_id = g.get('user_id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        # Parse form data
        data = request.form.to_dict()
        files = request.files.getlist('episodeFiles')  # Assuming the field name is 'episodeFiles'
        data['episodeFiles'] = files

        # Log received data for debugging
        logger.info(f"Received data: {data}")
        logger.info(f"Received files: {files}")

        # Validate required fields
        if not data.get('podcastId') or not data.get('title') or not data.get('publishDate'):
            return jsonify({"error": "Required fields missing: podcastId, title, and publishDate"}), 400

        # Process the episode registration
        response, status = episode_repo.register_episode(data, user_id)
        return jsonify(response), status

    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


@episode_bp.route("/publish_to_spotify/<episode_id>", methods=["POST"])
def publish_to_spotify(episode_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    episode = episodes.find_one({"_id": episode_id})
    if not episode:
        return jsonify({"error": "Episode not found"}), 404

    try:
        # Fetch Spotify access token
        access_token = get_spotify_access_token()
        if not access_token:
            return jsonify({"error": "Failed to retrieve Spotify access token"}), 500

        # Attempt to upload episode to Spotify
        result = upload_episode_to_spotify(access_token, episode)
        if result:
            return jsonify({"message": "Episode published successfully to Spotify!"}), 200
        else:
            return jsonify({"error": "Failed to upload episode to Spotify"}), 500
    except Exception as e:
        return jsonify({"error": f"Error publishing to Spotify: {str(e)}"}), 500


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


@episode_bp.route("/delete_episodes/<episode_id>", methods=["DELETE"])
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
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

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
