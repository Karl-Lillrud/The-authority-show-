from flask import request, jsonify, Blueprint, g  # Add g import
import random
from database.cosmos_connection import container
from datetime import datetime, timezone  # Update import

registerpodcast_bp = Blueprint('registerpodcast_bp', __name__)

@registerpodcast_bp.route('/register_podcast', methods=['POST'])
def register_podcast():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400

    pod_name = data.get("podName", "").strip()
    pod_rss = data.get("podRss", "").strip()

    if not pod_name or not pod_rss:
        return jsonify({"error": "Podcast Name and RSS URL are required"}), 400

    podcast_item = {
        "id": str(random.randint(100000, 999999)),
        "creator_id": g.user_id,
        "podName": pod_name,
        "podRss": pod_rss,
        "created_at": datetime.now(timezone.utc).isoformat()  # Update datetime usage
    }

    try:
        container.upsert_item(podcast_item)
        return jsonify({"message": "Podcast registered successfully", "redirect_url": "/production-team"}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to register podcast: {str(e)}"}), 500