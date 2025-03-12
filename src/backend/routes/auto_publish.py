from flask import Blueprint, request, jsonify
from backend.services.spotify_integration import upload_episode_to_spotify

auto_publish_bp = Blueprint("auto_publish", __name__)

@auto_publish_bp.route("/publish/spotify", methods=["POST"])
def publish_to_spotify():
    episode_data = request.get_json()
    if not episode_data:
        return jsonify({"error": "Ingen data skickades."}), 400
    try:
        response = upload_episode_to_spotify(episode_data)
        if response.status_code == 201:
            return jsonify({"message": "Episoden publicerades på Spotify."}), 201
        else:
            return jsonify({
                "error": "Publicering misslyckades.",
                "details": response.json()
            }), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500
