from flask import Blueprint, jsonify, g
from backend.repository.episode_repository import EpisodeRepository
from backend.services.spotify_integration import get_spotify_access_token
from backend.services.submit_rss_to_spotify import submit_rss_to_spotify  # Import the submit_rss_to_spotify function
from backend.services.generate_rss_feed import create_rss_feed
from backend.services.upload_rss_to_cloudflare import upload_rss_to_cloudflare  # Import the upload function
import logging

auto_publish_bp = Blueprint('auto_publish_bp', __name__)
episode_repo = EpisodeRepository()
logger = logging.getLogger(__name__)

@auto_publish_bp.route('/auto_publish/<episode_id>', methods=['POST'])
def auto_publish(episode_id):
    logger.info(f"Received request to publish episode {episode_id}")

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

        # Generate RSS Feed
        podcast_data = {
            "title": episode['podcast_title'],
            "description": episode['podcast_description'],
            "link": episode['podcast_link']
        }
        episode_data = [{
            "title": episode['title'],
            "description": episode['description'],
            "audio_url": episode['audio_url'],  # Include the audio URL of the episode
            "publish_date": episode['publishDate'],
            "guid": episode['guid']
        }]
        
        # Generate the RSS feed
        rss_feed = create_rss_feed(podcast_data, episode_data)

        # Upload the RSS feed to Cloudflare R2
        rss_feed_url = upload_rss_to_cloudflare(rss_feed, f"{episode_id}_feed.xml")
        logger.info(f"RSS feed uploaded to Cloudflare R2: {rss_feed_url}")

        # Now submit the RSS feed URL to Spotify (not the raw audio file)
        result = submit_rss_to_spotify(access_token, rss_feed_url)

        if result:
            return jsonify({"message": "Episode published successfully to Spotify!"}), 200
        else:
            logger.error("Failed to upload RSS feed to Spotify")
            return jsonify({"error": "Failed to upload RSS feed to Spotify"}), 400
    except Exception as e:
        logger.error(f"Error publishing to

@auto_publish_bp.route('/publish_to_spotify/<episode_id>', methods=['POST'])
def publish_to_spotify(episode_id):
    """
    Publish an episode to Spotify.
    """
    try:
        episode = episode_repo.get_episode_by_id(episode_id)
        if not episode:
            return jsonify({"error": "Episode not found"}), 404

        access_token = get_spotify_access_token()
        if not access_token:
            return jsonify({"error": "Failed to retrieve Spotify access token"}), 500

        result = upload_episode_to_spotify(access_token, episode)
        if result:
            return jsonify({"message": "Episode published successfully to Spotify!"}), 200
        else:
            return jsonify({"error": "Failed to publish episode to Spotify"}), 400
    except Exception as e:
        logger.error(f"Error publishing episode {episode_id} to Spotify: {e}")
        return jsonify({"error": "Failed to publish episode"}), 500
