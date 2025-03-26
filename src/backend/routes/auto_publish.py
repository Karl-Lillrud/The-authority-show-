from flask import Blueprint, jsonify, g
from backend.repository.episode_repository import EpisodeRepository
from backend.services.spotify_integration import get_spotify_access_token, upload_episode_to_spotify
from backend.services.generate_rss_feed import create_rss_feed
from backend.services.upload_rss_to_cloudflare import upload_rss_to_cloudflare
import logging

auto_publish_bp = Blueprint('auto_publish_bp', __name__)
episode_repo = EpisodeRepository()
logger = logging.getLogger(__name__)

@auto_publish_bp.route('/auto_publish/<episode_id>', methods=['POST'])
def auto_publish(episode_id):
    """
    Automatically publish an episode by generating and uploading an RSS feed.
    """
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
            "title": episode.get('podcast_title', 'Untitled Podcast'),
            "description": episode.get('podcast_description', 'No description available'),
            "link": episode.get('podcast_link', '#')
        }
        episode_data = [{
            "title": episode.get('title', 'Untitled Episode'),
            "description": episode.get('description', 'No description available'),
            "audio_url": episode.get('audio_url'),
            "publish_date": episode.get('publishDate'),
            "guid": episode.get('guid', episode_id)
        }]
        rss_feed = create_rss_feed(podcast_data, episode_data)

        # Upload the RSS feed to Cloudflare R2
        rss_feed_url = upload_rss_to_cloudflare(rss_feed, f"{episode_id}_feed.xml")
        logger.info(f"RSS feed uploaded to Cloudflare R2: {rss_feed_url}")

        # Add the RSS feed URL to the episode data
        episode['rss_feed_url'] = rss_feed_url

        # Submit the RSS feed URL to Spotify
        result = upload_episode_to_spotify(access_token, episode)
        if result:
            return jsonify({"message": "Episode published successfully to Spotify!"}), 200
        else:
            logger.error("Failed to upload RSS feed to Spotify")
            return jsonify({"error": "Failed to upload RSS feed to Spotify"}), 400
    except Exception as e:
        logger.error(f"Error publishing episode {episode_id} to Spotify: {e}", exc_info=True)
        return jsonify({"error": "Failed to publish episode"}), 500

@auto_publish_bp.route('/publish_to_spotify/<episode_id>', methods=['POST'])
def publish_to_spotify(episode_id):
    """
    Publish an episode to Spotify.
    """
    logger.info(f"Received request to publish episode {episode_id}")

    try:
        episode = episode_repo.get_episode_by_id(episode_id)
        if not episode:
            return jsonify({"error": "Episode not found"}), 404

        access_token = get_spotify_access_token()
        if not access_token:
            return jsonify({"error": "Failed to retrieve Spotify access token"}), 500

        # Generate RSS feed and upload it to Cloudflare R2
        podcast_data = {
            "title": episode.get('podcast_title', 'Untitled Podcast'),
            "description": episode.get('podcast_description', 'No description available'),
            "link": episode.get('podcast_link', '#')
        }
        episode_data = [{
            "title": episode.get('title', 'Untitled Episode'),
            "description": episode.get('description', 'No description available'),
            "audio_url": episode.get('audio_url'),
            "publish_date": episode.get('publishDate'),
            "guid": episode.get('guid', episode_id)
        }]
        rss_feed = create_rss_feed(podcast_data, episode_data)

        # Upload the RSS feed to Cloudflare R2
        rss_feed_url = upload_rss_to_cloudflare(rss_feed, f"{episode_id}_feed.xml")
        logger.info(f"RSS feed uploaded to Cloudflare R2: {rss_feed_url}")

        # Add the RSS feed URL to the episode data
        episode['rss_feed_url'] = rss_feed_url

        # Submit the RSS feed URL to Spotify
        result = upload_episode_to_spotify(access_token, episode)
        if result:
            return jsonify({"message": "Episode published successfully to Spotify!"}), 200
        else:
            logger.error("Failed to upload RSS feed to Spotify")
            return jsonify({"error": "Failed to upload RSS feed to Spotify"}), 400
    except Exception as e:
        logger.error(f"Error publishing episode {episode_id} to Spotify: {e}", exc_info=True)
        return jsonify({"error": "Failed to publish episode"}), 500
