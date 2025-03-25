from flask import Blueprint, request, jsonify, g
from backend.repository.episode_repository import EpisodeRepository
from backend.services.spotify_integration import get_spotify_access_token, upload_episode_to_spotify
import logging

auto_publish_bp = Blueprint('auto_publish_bp', __name__)
episode_repo = EpisodeRepository()
logger = logging.getLogger(__name__)

@auto_publish_bp.route('/auto_publish/<episode_id>', methods=['POST'])
def auto_publish(episode_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    episode = episode_repo.get_episode_by_id(episode_id)
    if not episode:
        return jsonify({"error": "Episode not found"}), 404

    try:
        # Fetch Spotify access token
        access_token = get_spotify_access_token()
        if not access_token:
            logger.error("Failed to retrieve Spotify access token")
            return jsonify({"error": "Failed to retrieve Spotify access token"}), 500

        # Attempt to upload episode to Spotify
        result = upload_episode_to_spotify(access_token, episode)
        if result:
            return jsonify({"message": "Episode published successfully to Spotify!"}), 200
        else:
            logger.error("Failed to upload episode to Spotify")
            return jsonify({"error": "Failed to upload episode to Spotify"}), 400
    except Exception as e:
        logger.error(f"Error publishing to Spotify: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error publishing to Spotify: {str(e)}"}), 500
