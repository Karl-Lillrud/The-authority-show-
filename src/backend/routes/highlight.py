from flask import Blueprint, request, jsonify
from backend.repository.episode_repository import EpisodeRepository

highlights_bp = Blueprint('highlights', __name__)
episode_repo = EpisodeRepository()



@highlights_bp.route('/edit_highlight', methods=['POST'])
def edit_highlight():
    data = request.json

    #Validation
    required_fields = ["episodeId", "title", "startTime", "endTime"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required highlight fields"}), 400

    try:
        episode = episode_repo.get_by_id(data["episodeId"])
        if not episode:
            return jsonify({"error": "Episode not found"}), 404

        #Initialize highlights array if missing
        highlights = episode.get("highlights", [])
        
        #Check if editing existing or adding new
        matched = False
        for h in highlights:
            if h["title"] == data["title"]:  
                h["startTime"] = data["startTime"]
                h["endTime"] = data["endTime"]
                matched = True
                break

        if not matched:
            highlights.append({
                "title": data["title"],
                "startTime": data["startTime"],
                "endTime": data["endTime"]
            })

        episode["highlights"] = highlights
        episode_repo.update_episode(data["episodeId"], episode)

        return jsonify({"message": "Highlight saved successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@highlights_bp.route('/verify_highlight', methods=['POST'])
def verify_highlight():
    data = request.json

    #Basic validation
    if not all(k in data for k in ("startTime", "endTime")):
        return jsonify({"error": "Missing startTime or endTime"}), 400

    if data["startTime"] >= data["endTime"]:
        return jsonify({"error": "startTime must be less than endTime"}), 400

    #Add other checks if needed (e.g., does it overlap with another highlight?)

    return jsonify({"message": "Highlight verified successfully"}), 200
