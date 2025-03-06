from flask import request, jsonify, Blueprint, g, send_file, render_template
from backend.database.mongo_connection import collection, database
from datetime import datetime, timezone
import uuid
from bson import ObjectId
import io

# Define Blueprint
episode_bp = Blueprint("episode_bp", __name__)

episodes_collection = database["episodes"]
transcripts_collection = database["transcripts"]

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


# === Serve All Episodes (Prepare for Dynamic Pages) ===
@episode_bp.route("/episodes", methods=["GET"])
def get_latest_episode():
    """ Fetch and display the latest published episode """
    episode = episodes_collection.find_one(sort=[("_id", -1)])
    
    if not episode:
        return "No episode found", 404

    transcript = transcripts_collection.find_one({"episodeId": str(episode["_id"])})
    transcript_data = transcript["transcript"] if transcript else []

    return render_template("episode.html", episode=episode, transcript=transcript_data)


# === Serve Audio File for an Episode ===
@episode_bp.route("/<audio_id>", methods=["GET"])
def get_audio(audio_id):
    """ Serve podcast audio from GridFS """
    try:
        # TODO: Replace this with actual Azure Blob Storage retrieval
        return jsonify({"message": f"Fetch audio with ID: {audio_id} from Azure"}), 200
        
        
    except Exception as e:
        print("Error serving audio:", str(e))
        return jsonify({"error": "Audio not found"}), 404



# === Serve Video File from Azure Blob Storage ===
@episode_bp.route("/<video_id>", methods=["GET"])
def get_video(video_id):
    """ Serve video shorts from GridFS """
    try:
    # TODO: Replace this with actual Azure Blob Storage retrieval
        return jsonify({"message": f"Fetch video with ID: {video_id} from Azure"}), 200
    except Exception as e:
        print("Error serving video:", str(e))
        return jsonify({"error": "Video not found"}), 404


# === Get Transcript for a Specific Episode ===
#get trancript from db
@episode_bp.route("/transcript", methods=["GET"])
def get_transcript():
    """ Retrieve the transcript for a specific episode """
    episode_id = request.args.get("episode_id")

    if not episode_id:
        return jsonify({"error": "Missing episode ID"}), 400

    transcript = transcripts_collection.find_one({"episodeId": episode_id})
    
    if transcript:
        return jsonify(transcript["transcript"]), 200
    else:
        return jsonify({"error": "Transcript not found"}), 404


# === Fetch and Display a Specific Episode ===
@episode_bp.route("/episode/<episode_id>", methods=["GET"])
def get_episode_details(episode_id):
    """ Fetch and display details of a specific episode """
    try:
        episode = episodes_collection.find_one({"_id": ObjectId(episode_id)})
        if not episode:
            return "Episode not found", 404

        # Ensure all required data exists
        guest = episode.get("guest", {})
        key_learnings = episode.get("key_learnings", [])
        faq = episode.get("faq", [])
        shorts = episode.get("shorts", [])

        return render_template(
            "episode.html",
            episode=episode,
            guest=guest,
            key_learnings=key_learnings,
            faq=faq,
            shorts=shorts
        )

    except Exception as e:
        print("Error fetching episode details:", str(e))
        return jsonify({"error": "Failed to retrieve episode details"}), 500