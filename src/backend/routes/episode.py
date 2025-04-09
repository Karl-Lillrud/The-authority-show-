from flask import request, jsonify, Blueprint, g, render_template, send_file
import logging
from pymongo import MongoClient
import gridfs
import os
from dotenv import load_dotenv
import base64
from io import BytesIO
from datetime import datetime, timezone

# Import the repository
from backend.repository.episode_repository import EpisodeRepository
from backend.repository.podcast_repository import PodcastRepository
from backend.database.mongo_connection import episodes
from backend.services.spotify_integration import (
    save_uploaded_files,
    get_spotify_access_token,
    upload_episode_to_spotify,
)
from backend.services.generate_rss_feed import create_rss_feed
from backend.services.upload_rss_to_google_cloud import upload_rss_to_google_cloud
from backend.repository.guest_repository import GuestRepository
from backend.services.upload_to_google_cloud import upload_to_google_cloud

# Create repository instances
guest_repo = GuestRepository()
episode_repo = EpisodeRepository()
podcast_repo = PodcastRepository()

# Logger setup
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "Podmanager"

client = MongoClient(MONGODB_URI)  # Use MongoDB URI from .env file
db = client[DATABASE_NAME]  # Specify the database name
fs = gridfs.GridFS(db)  # Initialize GridFS

# Define Blueprint
episode_bp = Blueprint("episode_bp", __name__)

def get_guests_for_episode(episode_id):
    guests_collection = db["Guests"]  # Replace with your actual guests collection name
    guests = guests_collection.find({"episodeId": episode_id})
    return list(guests)

@episode_bp.route("/register_episode", methods=["POST"])
def register_episode():
    try:
        # Validate User
        user_id = g.get("user_id")
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        # Parse form data
        data = request.form.to_dict()
        files = request.files.getlist("episodeFiles")
        image_file = request.files.get("image")  # Get the image file from the frontend

        if not files or files[0].filename == "":
            return jsonify({"error": "No audio files uploaded"}), 400

        # Save audio files to Google Cloud Storage
        saved_files = save_uploaded_files(files)
        if not saved_files:
            return jsonify({"error": "Failed to save uploaded audio files"}), 500
        data["audioUrl"] = saved_files[0]["url"]
        data["episodeFiles"] = saved_files
        logger.info(f"Audio files saved to Google Cloud Storage: {saved_files}")

        # Save image file to Google Cloud Storage (if provided)
        if image_file:
            image_filename = f"{image_file.filename}"
            image_url = upload_to_google_cloud(image_file.read(), image_filename)
            data["imageUrl"] = image_url
            logger.info(f"Image file '{image_file.filename}' saved to: {image_url}")
        else:
            # Provide a default image URL if no image file is uploaded
            data["imageUrl"] = "https://storage.googleapis.com/podmanager/images/default_image.png"
            logger.warning("No image file uploaded. Using default image URL.")

        # Validate required fields
        if not data.get("podcastId") or not data.get("title") or not data.get("publishDate"):
            return jsonify({"error": "Required fields missing: podcastId, title, and publishDate"}), 400

        # Register episode and save in the database
        response, status = episode_repo.register_episode(data, user_id)
        logger.info(f"Episode registered successfully with data: {data}")
        return jsonify(response), status
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

# Publish an episode
@episode_bp.route("/publish/<episode_id>", methods=["POST"])
def publish(episode_id):
    """
    Publish an episode.
    """
    logger.info(f"Received request to publish episode {episode_id}")
    try:
        episode = episode_repo.get_episode_by_id(episode_id)
        if not episode:
            return jsonify({"error": "Episode not found"}), 404

        # Validate required fields
        if not episode.get("audioUrl"):
            logger.error("Audio URL is missing for the episode.")
            return jsonify({"error": "Audio URL is missing for the episode."}), 400

        if not episode.get("imageUrl"):
            logger.warning("Episode image is missing. Using default image.")
            episode["imageUrl"] = "https://storage.googleapis.com/podmanager/images/default_image.png"

        podcast_data = {
            "title": episode.get("podcast_title", "Untitled Podcast"),
            "description": episode.get("podcast_description", "No description available"),
            "link": episode.get("podcast_link", "#"),
            "imageUrl": episode.get("imageUrl"),
        }
        episode_data = [
            {
                "title": episode.get("title", "Untitled Episode"),
                "description": episode.get("description", "No description available"),
                "audioUrl": episode.get("audioUrl"),
                "publishDate": episode.get("publishDate"),
                "guid": episode.get("guid", episode_id),
                "imageUrl": episode.get("imageUrl"),
                "duration": episode.get("duration"),
                "explicit": episode.get("explicit"),
            }
        ]

        rss_feed = create_rss_feed(podcast_data, episode_data)
        rss_feed_url = upload_rss_to_google_cloud(rss_feed, f"{episode_id}_feed.xml")
        logger.info(f"RSS feed uploaded to Google Cloud Storage: {rss_feed_url}")

        # Mark episode as published (update the episode document)
        episode_repo.collection.update_one(
            {"_id": episode_id},
            {
                "$set": {
                    "status": "Published",
                    "rss_feed_url": rss_feed_url,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        return jsonify({"message": "Episode published successfully", "rss_feed_url": rss_feed_url}), 200

    except Exception as e:
        logger.error(f"Error publishing episode {episode_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to publish episode"}), 500

# Other routes for episodes omitted for brevity
