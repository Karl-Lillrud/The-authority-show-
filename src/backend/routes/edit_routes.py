from flask import Blueprint, jsonify
from backend.database.mongo_connection import get_db
import logging

logger = logging.getLogger(__name__)
edit_bp = Blueprint("edit_bp", __name__)
db = get_db()

@edit_bp.route("/edits/<episode_id>", methods=["GET"])
def get_edits_for_episode(episode_id):
    try:
        edits = list(db.Edits.find({"episodeId": episode_id}))
        
        for edit in edits:
            edit["_id"] = str(edit["_id"])
            edit["episodeId"] = str(edit["episodeId"])
            edit["createdAt"] = edit.get("createdAt").isoformat() if edit.get("createdAt") else None

        return jsonify(edits), 200

    except Exception as e:
        logger.error(f"❌ Failed to fetch edits for episode {episode_id}: {e}")
        return jsonify({"error": "Could not fetch edits"}), 500