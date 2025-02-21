from flask import Blueprint, jsonify, g
from database.mongo_connection import collection

# Define Blueprint
episodes_bp = Blueprint("episodes_bp", __name__)


@episodes_bp.route("/get_open_episodes", methods=["GET"])
def get_open_episodes():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        ollina_episodes = collection.database.Episodes.count_documents(
            {"guest_id": "GUEST_ID_1"}
        )
        olle_episodes = collection.database.Episodes.count_documents(
            {"guest_id": "GUEST_ID_2"}
        )
        olga_episodes = collection.database.Episodes.count_documents(
            {"guest_id": "GUEST_ID_3"}
        )

        return (
            jsonify(
                {
                    "ollina": ollina_episodes,
                    "olle": olle_episodes,
                    "olga": olga_episodes,
                }
            ),
            200,
        )

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
