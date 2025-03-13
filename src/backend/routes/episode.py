from flask import request, jsonify, Blueprint, g
from backend.database.mongo_connection import collection, database
from datetime import datetime, timezone
import uuid
import logging
from backend.models.episodes import EpisodeSchema

# Define Blueprint
episode_bp = Blueprint("episode_bp", __name__)

#SHOULD ONLY BE USED FOR SPECIFIC DATA CRUD OPERATIONS
#EXTRA FUNCTIONALITY BESIDES CRUD OPERATIONS SHOULD BE IN SERVICES

logger = logging.getLogger(__name__)


from flask import request, jsonify, Blueprint, g
from backend.database.mongo_connection import collection, database
from datetime import datetime, timezone
import uuid
import logging
from werkzeug.utils import secure_filename
import os

# Define Blueprint
episode_bp = Blueprint("episode_bp", __name__)

# Initialize logger
logger = logging.getLogger(__name__)


# Directory to save uploaded files
UPLOAD_FOLDER = '/path/to/upload/directory'  # Set your desired upload folder path
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename

@episode_bp.route("/register_episode", methods=["POST"])
def register_episode():
        
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    print(f"Content-Type: {request.content_type}")
    print(f"Request Files: {request.files}")

    # Validate Content-Type
    if 'multipart/form-data' not in request.content_type:
        return jsonify({"error": "Invalid Content-Type. Expected multipart/form-data"}), 415

    try:
        # Check if the post request has the file part
        if 'audio' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        # Process each uploaded file
        files = request.files.getlist('audio')
        file_paths = []

        for file in files:
            if file.filename == '':
                return jsonify({"error": "No selected file"}), 400
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                file_paths.append(file_path)
            else:
                return jsonify({"error": "Invalid file type. Allowed types are: MP3, M4A, MP4"}), 400

        # Handle other form data (podcastId, title, etc.)
        data = request.form.to_dict()  # Get the other form fields
        podcast_id = data.get("podcastId")
        title = data.get("title")
        description = data.get("description")
        publish_date = data.get("publishDate")
        duration = data.get("duration")
        guest_id = data.get("guestId")
        status = data.get("status")

        # Validate required fields
        if not podcast_id or not title:
            return jsonify({"error": "Required fields missing: podcastId and title"}), 400

        # Generate unique episode ID
        episode_id = str(uuid.uuid4())
        user_id = str(g.user_id)

        # Construct the episode document with the handled values
        episode_item = {
            "_id": episode_id,
            "podcast_id": podcast_id,
            "title": title,
            "description": description,
            "publishDate": publish_date,
            "duration": duration,
            "guestId": guest_id,
            "status": status,
            "audio_files": file_paths,  # Store the file paths in the database
            "userid": user_id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        # Insert the episode into the database
        result = collection.database["Episodes"].insert_one(episode_item)
        logger.info(f"Episode registered successfully with ID: {episode_id}")

        return jsonify({
            "message": "Episode registered successfully",
            "episode_id": episode_id,
            "redirect_url": "/index.html"
        }), 201

    except Exception as e:
        logger.error(f"Error: {str(e)}")
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
            "title": (
                data.get("title", existing_episode["title"]).strip()
                if data.get("title")
                else existing_episode["title"]
            ),
            "description": (
                data.get("description", existing_episode["description"]).strip()
                if data.get("description")
                else existing_episode["description"]
            ),
            "publishDate": data.get("publishDate", existing_episode["publishDate"]),
            "duration": data.get("duration", existing_episode["duration"]),
            "guestId": (
                data.get("guestId", existing_episode["guestId"]).strip()
                if data.get("guestId")
                else existing_episode["guestId"]
            ),
            "status": (
                data.get("status", existing_episode["status"]).strip()
                if data.get("status")
                else existing_episode["status"]
            ),
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


@episode_bp.route("/episodes/by_podcast/<podcast_id>", methods=["GET"])
def get_episodes_by_podcast(podcast_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        user_id = str(g.user_id)
        episodes = list(
            collection.database.Episodes.find(
                {"podcast_id": podcast_id, "userid": user_id}
            )
        )
        for episode in episodes:
            episode["_id"] = str(episode["_id"])
        return jsonify({"episodes": episodes}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500