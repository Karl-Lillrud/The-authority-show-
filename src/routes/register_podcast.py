from flask import request, jsonify, Blueprint, g
from database.mongo_connection import collection
from datetime import datetime, timezone
import uuid

# Define Blueprint
registerpodcast_bp = Blueprint("registerpodcast_bp", __name__)

@registerpodcast_bp.route("/register_podcast", methods=["POST"])
def register_podcast():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Validate Content-Type
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        data = request.get_json()
        print("📩 Received Data:", data)

        # Generate UUID for _id (same way as in the registration route)
        podcast_id = str(uuid.uuid4())  # This generates a custom string UUID for _id
        user_id = str(g.user_id)  # Use the user_id directly as a string

        # Create podcast document with custom UUID as _id
        podcast_item = {
            "_id": podcast_id,  # Set the custom UUID as the _id
            "creator_id": user_id,  # Use user_id (UUID string) as creator_id
            "podName": data.get("podName", "").strip(),  # Optional: Pod name if provided
            "podRss": data.get("podRss", "").strip(),  # Optional: Pod RSS if provided
            "created_at": datetime.now(timezone.utc),
        }

        # Check if the user exists
        user = collection.database.users.find_one({"_id": user_id})
        if not user:
            return jsonify({"error": "User not found"}), 404

        print("📝 Inserting podcast into database:", podcast_item)
        result = collection.database.podcasts.insert_one(podcast_item)

        print("✅ Podcast registered successfully!")

        return jsonify(
            {
                "message": "Podcast registered successfully",
                "podcast_id": podcast_id,  # Return the custom UUID for the podcast_id
                "redirect_url": "/production-team",
            }
        ), 201

    except Exception as e:
        print(f"❌ ERROR: {e}")  # Log the error for debugging
        return jsonify({"error": f"Failed to register podcast: {str(e)}"}), 500
