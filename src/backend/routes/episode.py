from flask import request, jsonify, Blueprint, g
from backend.database.mongo_connection import collection, database
from datetime import datetime, timezone
import uuid

# Define Blueprint
episode_bp = Blueprint("episode_bp", __name__)


@episode_bp.route("/register_episode", methods=["POST"])
def register_episode():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Validate Content-Type
    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    try:
        data = request.get_json()
        print("📩 Received Episode Data:", data)

        episode_id = str(uuid.uuid4())  # Generate unique ID
        user_id = str(g.user_id)

        # Extracting data fields
        podcast_id = data.get("podcastId", "").strip()
        title = data.get("title", "").strip()
        description = data.get("description", "").strip()
        publish_date = data.get("publishDate")
        duration = data.get("duration", 0)
        guest_id = data.get("guestId", "").strip()
        status = data.get("status", "").strip()

        # Construct the episode document
        episode_item = {
            "_id": episode_id,
            "podcast_id": podcast_id,
            "title": title,
            "description": description,
            "publishDate": publish_date,
            "duration": duration,
            "guestId": guest_id,
            "status": status,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        # Correctly querying the User collection
        user = collection.database.User.find_one({"_id": user_id})
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Correctly inserting into the Episode collection
        print("📝 Inserting episode into database:", episode_item)
        result = collection.database["Episodes"].insert_one(
            episode_item
        )  # Ensure "Episodes" is correct

        print("✅ Episode registered successfully!")

        return (
            jsonify(
                {
                    "message": "Episode registered successfully",
                    "episode_id": episode_id,
                    "redirect_url": "/index.html",
                }
            ),
            201,
        )

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to register episode: {str(e)}"}), 500


@episode_bp.route("/get_episodes/<episode_id>", methods=["GET"])
def get_episode(episode_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)

        # Debugging: Print episode_id and user_id
        print(f"Fetching episode with episode_id: {episode_id} for user_id: {user_id}")

        # Fetch the episode using the string episode_id
        episode = collection.database.Episodes.find_one(
            {"_id": episode_id, "userid": user_id}
        )

        if not episode:
            print(
                f"Episode with episode_id: {episode_id} and user_id: {user_id} not found."
            )
            return jsonify({"error": "Episode not found"}), 404

        return jsonify(episode), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch episode: {str(e)}"}), 500


@episode_bp.route("/get_episodes", methods=["GET"])
def get_episodes():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)
        episodes = list(collection.database.Episodes.find({"userid": user_id}))

        for episode in episodes:
            episode["_id"] = str(episode["_id"])

        return jsonify({"episodes": episodes}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch episodes: {str(e)}"}), 500


@episode_bp.route("/delete_episods/<episode_id>", methods=["DELETE"])
def delete_episode(episode_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)
        episode = collection.database.Episodes.find_one({"_id": episode_id})

        if not episode:
            return jsonify({"error": "Episode not found"}), 404

        if episode["userid"] != user_id:
            return jsonify({"error": "Permission denied"}), 403

        result = collection.database.Episodes.delete_one({"_id": episode_id})

        if result.deleted_count == 1:
            return jsonify({"message": "Episode deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete episode"}), 500

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to delete episode: {str(e)}"}), 500


@episode_bp.route("/update_episodes/<episode_id>", methods=["PUT"])
def update_episode(episode_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    try:
        data = request.get_json()
        user_id = str(g.user_id)

        existing_episode = collection.database.Episodes.find_one({"_id": episode_id})
        if not existing_episode:
            return jsonify({"error": "Episode not found"}), 404

        if existing_episode["userid"] != user_id:
            return jsonify({"error": "Permission denied"}), 403

        update_fields = {
            "title": data.get("title", existing_episode["title"]).strip(),
            "description": data.get(
                "description", existing_episode["description"]
            ).strip(),
            "publishDate": data.get("publishDate", existing_episode["publishDate"]),
            "duration": data.get("duration", existing_episode["duration"]),
            "guestId": data.get("guestId", existing_episode["guestId"]).strip(),
            "status": data.get("status", existing_episode["status"]).strip(),
            "updated_at": datetime.now(timezone.utc),
        }

        result = collection.database.Episodes.update_one(
            {"_id": episode_id}, {"$set": update_fields}
        )

        if result.modified_count == 1:
            return jsonify({"message": "Episode updated successfully"}), 200
        else:
            return jsonify({"message": "No changes made to the episode"}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to update episode: {str(e)}"}), 500


@episode_bp.route("/count_by_guests/<guest_id>", methods=["GET"])
def count_by_guest(guest_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)

        # Count the number of episodes for the given guest
        count = collection.database.Episodes.count_documents(
            {"guestId": guest_id, "userid": user_id}
        )

        return jsonify({"count": count}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch episode count: {str(e)}"}), 500


@episode_bp.route("/episodes/count_by_guest/<guest_id>", methods=["GET"])
def count_episodes_by_guest(guest_id):
    try:
        count = collection.database.Episodes.count_documents({"guestId": guest_id})
        return jsonify({"count": count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@episode_bp.route("/episodes/get_episodes_by_guest/<guest_id>", methods=["GET"])
def get_episodes_by_guest(guest_id):
    try:
        episodes = list(database.Episodes.find({"guestId": guest_id}))
        for episode in episodes:
            episode["_id"] = str(episode["_id"])
        return jsonify({"episodes": episodes}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
