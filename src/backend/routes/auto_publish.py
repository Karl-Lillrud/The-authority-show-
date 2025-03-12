from flask import Blueprint, request, jsonify
from backend.services.spotify_integration import upload_episode_to_spotify
from backend.services.spotify_oauth import get_spotify_access_token

auto_publish_bp = Blueprint("auto_publish", __name__)

@auto_publish_bp.route("/publish/spotify", methods=["POST"])
def publish_to_spotify():
    episode_data = request.get_json()
    if not episode_data:
        return jsonify({"error": "Ingen data skickades."}), 400

    try:
        # Hämta access token
        access_token = get_spotify_access_token()

        # Skicka data till Spotify för publicering
        response = upload_episode_to_spotify(
            access_token,
            episode_data["title"],
            episode_data["description"],
            episode_data["audioUrl"]
        )

        # Hantera API-responsen
        if response:
            return jsonify({"message": "Episoden publicerades på Spotify."}), 201
        else:
            return jsonify({
                "error": "Publicering misslyckades.",
                "details": response
            }), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
