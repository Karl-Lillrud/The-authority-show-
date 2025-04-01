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
from backend.services.upload_rss_to_cloudflare import (
    upload_rss_to_cloudflare,
)  # Ensure this import exists
from backend.repository.guest_repository import GuestRepository

# Create repository instance
guest_repo = GuestRepository()

# Define Blueprint
episode_bp = Blueprint("episode_bp", __name__)
episode_repo = EpisodeRepository()
podcast_repo = PodcastRepository()
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "Podmanager"

client = MongoClient(MONGODB_URI)  # Use MongoDB URI from .env file
db = client[DATABASE_NAME]  # Specify the database name
fs = gridfs.GridFS(db)  # Initialize GridFS


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
        if not files or files[0].filename == "":
            return (
                jsonify({"error": "No files uploaded"}),
                400,
            )  # Validate file presence

        # Reset file pointers and save files
        saved_files = save_uploaded_files(files)
        if not saved_files:
            return jsonify({"error": "Failed to save uploaded files"}), 500
        data["audioUrl"] = saved_files[0]["url"]
        data["episodeFiles"] = saved_files

        # Validera nödvändiga fält
        if (
            not data.get("podcastId")
            or not data.get("title")
            or not data.get("publishDate")
        ):
            return (
                jsonify(
                    {
                        "error": "Required fields missing: podcastId, title, and publishDate"
                    }
                ),
                400,
            )

        # Registrera episode och spara i databasen
        response, status = episode_repo.register_episode(data, user_id)
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

        access_token = get_spotify_access_token()
        if not access_token:
            return jsonify({"error": "Failed to retrieve Spotify access token"}), 500

        podcast_data = {
            "title": episode.get("podcast_title", "Untitled Podcast"),
            "description": episode.get(
                "podcast_description", "No description available"
            ),
            "link": episode.get("podcast_link", "#"),
        }
        episode_data = [
            {
                "title": episode.get("title", "Untitled Episode"),
                "description": episode.get("description", "No description available"),
                "audio_url": episode.get("audio_url"),
                "publish_date": episode.get("publishDate"),
                "guid": episode.get("guid", episode_id),
            }
        ]

        rss_feed = create_rss_feed(podcast_data, episode_data)
        rss_feed_url = upload_rss_to_cloudflare(rss_feed, f"{episode_id}_feed.xml")
        logger.info(f"RSS feed uploaded to Cloudflare R2: {rss_feed_url}")

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
        episode["status"] = "Published"  # update local representation

        logger.info("Spotify does not provide an API for RSS feed submission.")
        logger.info(
            f"Please submit the RSS feed URL manually via Spotify for Podcasters: {rss_feed_url}"
        )
        return (
            jsonify(
                {
                    "message": "Episode published successfully",
                    "rss_feed_url": rss_feed_url,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error publishing episode {episode_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to publish episode"}), 500


@episode_bp.route("/get_episodes/<episode_id>", methods=["GET"])
def get_episode(episode_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        response, status_code = episode_repo.get_episode(episode_id, g.user_id)
        # Convert binary data to a base64 encoded string
        if "episodeFiles" in response:
            for file in response["episodeFiles"]:
                if "data" in file:
                    file["data"] = base64.b64encode(file["data"]).decode("utf-8")
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
    return episode_repo.delete_episode(episode_id, g.user_id)


@episode_bp.route("/update_episodes/<episode_id>", methods=["PUT"])
def update_episode(episode_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
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
        episode, podcast = episode_repo.get_episode_detail_with_podcast(episode_id)
        if not episode:
            return render_template("404.html")
        # Pass the retrieved episode (which includes the published status) to the template
        return render_template("landingpage/episode.html", episode=episode)
    except Exception as e:
        logger.error("❌ ERROR in episode_detail: %s", str(e))
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
            status = ep.get("status", "Uncategorized")  # Include status field

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
                    "status": status,  # add status to the mapping
                }
            )

        # Return the mapped episodes list
        return jsonify({"episodes": mapped_episodes}), 200

    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to fetch episodes by podcast: {str(e)}"}), 500


@episode_bp.route("/get_guests_by_episode/<episode_id>", methods=["GET"])
def get_guests_by_episode(episode_id):
    """
    Fetch guests associated with a specific episode.
    """
    try:
        guests = guest_repo.get_guests_by_episode(episode_id)
        if not guests:
            return jsonify({"error": "No guests found for this episode"}), 404
        return jsonify({"guests": guests}), 200
    except Exception as e:
        logger.error(f"Error fetching guests for episode {episode_id}: {e}")
        return jsonify({"error": "Failed to fetch guests"}), 500


@episode_bp.route("/file/<file_id>", methods=["GET"])
def get_file(file_id):
    try:
        file = fs.get(file_id)
        return send_file(
            BytesIO(file.read()), attachment_filename=file.filename, as_attachment=True
        )
    except gridfs.errors.NoFile:
        return jsonify({"error": "File not found"}), 404


@episode_bp.route("/download_rss/<podcast_id>", methods=["GET"])
def download_rss(podcast_id):
    """
    Generate and return the RSS feed XML file for a podcast.
    """
    try:
        # Fetch the podcast and its episodes
        logger.info(f"Fetching podcast with ID: {podcast_id}")
        podcast = podcast_repo.get_podcast_by_id(podcast_id)
        if not podcast:
            logger.error(f"Podcast with ID {podcast_id} not found.")
            return jsonify({"error": "Podcast not found"}), 404

        logger.info(f"Podcast found: {podcast.get('podName', 'Unknown')}")
        episodes, status_code = episode_repo.get_episodes_by_podcast(
            podcast_id, g.user_id, return_with_status=True
        )
        if status_code != 200 or not episodes:
            logger.warning(f"No episodes found for podcast ID {podcast_id}.")
            episodes = []  # Ensure episodes is an empty list

        # Ensure all episodes are dictionaries
        episodes = [ep for ep in episodes if isinstance(ep, dict)]

        logger.info(f"Found {len(episodes)} valid episodes for podcast ID {podcast_id}.")

        # Generate the RSS feed
        rss_feed = create_rss_feed(podcast, episodes)
        logger.info(f"RSS feed generated successfully for podcast ID {podcast_id}.")

        # Return the RSS feed as a downloadable file
        response = send_file(
            BytesIO(rss_feed.encode("utf-8")),
            mimetype="application/xml",
            as_attachment=True,
            download_name=f"{podcast.get('podName', 'podcast')}_rss_feed.xml",
        )
        return response
    except Exception as e:
        logger.error(f"Error generating RSS feed for podcast {podcast_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to generate RSS feed"}), 500
