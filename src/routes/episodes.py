from flask import Blueprint, jsonify, g
from database.mongo_connection import collection

# Define Blueprint
episodes_bp = Blueprint("episodes_bp", __name__)


@episodes_bp.route("/get_open_episodes", methods=["GET"])
def get_open_episodes():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        guests = collection.database.Guest.find()
        open_episodes = {}
        for guest in guests:
            guest_id = guest["ID"]
            count = collection.database.Episodes.count_documents({"guest_id": guest_id})
            open_episodes[guest_id] = count

        return jsonify(open_episodes), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch open episodes: {str(e)}"}), 500


@episodes_bp.route("/get_episodes_by_guest/<guest_id>", methods=["GET"])
def get_episodes_by_guest(guest_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        episodes = list(collection.database.Episodes.find({"guest_id": guest_id}))
        for episode in episodes:
            episode["_id"] = str(episode["_id"])

        return jsonify({"episodes": episodes}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch episodes: {str(e)}"}), 500
