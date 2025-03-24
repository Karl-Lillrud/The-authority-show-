from flask import Blueprint, request, jsonify
from backend.services.spotify_integration import upload_episode_to_spotify
from backend.routes.spotify_oauth import get_spotify_access_token
from backend.database.mongo_connection import get_fs

auto_publish_bp = Blueprint("auto_publish", __name__)

@auto_publish_bp.route("/publish/spotify", methods=["POST"])
def publish_to_spotify():
    episode_data = request.get_json()
    if not episode_data:
        return jsonify({"error": "No data sent."}), 400

    try:
        # Get access token
        access_token = get_spotify_access_token()

        # Get the audio file from GridFS
        fs = get_fs()
        audio_file_id = episode_data.get("audioFileId")
        if not audio_file_id:
            return jsonify({"error": "Audio file ID is required."}), 400

        # Construct the publicly accessible URL for the audio file
        audio_url = f"https://yourdomain.com/files/{audio_file_id}"

        # Publish episode to Spotify
        response = upload_episode_to_spotify(
            access_token,
            episode_data["title"],
            episode_data["description"],
            audio_url
        )

        if response:
            return jsonify({"message": "Episode published on Spotify."}), 201
        else:
            return jsonify({"error": "Publishing failed."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
