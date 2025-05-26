from flask import Blueprint, request, jsonify, send_file
from backend.database.mongo_connection import get_db, get_fs
from bson import ObjectId

episodes_bp = Blueprint("episodes", __name__)
db = get_db()
fs = get_fs()

@episodes_bp.route("/<episode_id>/audio", methods=["GET"])
def get_episode_audio(episode_id):
    """Get the audio file URL for a specific episode"""
    try:
        # Find the episode in the database
        episode = db.episodes.find_one({"_id": ObjectId(episode_id)})
        if not episode:
            return jsonify({"error": "Episode not found"}), 404

        # Get the audio file ID from the episode
        audio_file_id = episode.get("audio_file_id")
        if not audio_file_id:
            return jsonify({"error": "No audio file found for this episode"}), 404

        # Get the audio file from GridFS
        audio_file = fs.get(ObjectId(audio_file_id))
        if not audio_file:
            return jsonify({"error": "Audio file not found in storage"}), 404

        # Return the URL to access the audio file
        audio_url = f"/api/files/{audio_file_id}"
        return jsonify({"audio_url": audio_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500 