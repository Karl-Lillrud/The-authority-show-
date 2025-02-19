from flask import request, jsonify, Blueprint, g
from database.mongo_connection import collection
from datetime import datetime, timezone
import uuid

# Define Blueprint
podcast_bp = Blueprint("podcast_bp", __name__)

@podcast_bp.route("/add_podcast", methods=["POST"])
def podcast():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Validate Content-Type
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        data = request.get_json()
        print("📩 Received Data:", data)

        podcast_id = str(uuid.uuid4())  
        user_id = str(g.user_id)  

        social_media_links = data.get("socialMedia", [])  # Expecting an array
        pod_email = data.get("podEmail", "").strip()
        guest_url = data.get("guestUrl", "").strip()

        podcast_item = {
            "_id": podcast_id,  
            "userid": user_id,  
            "podName": data.get("podName", "").strip(),
            "podRss": data.get("podRss", "").strip(),
            "socialMedia": social_media_links,  # Array
            "podEmail": pod_email,  
            "guestUrl": guest_url,  
            "created_at": datetime.now(timezone.utc),
        }

        user = collection.database.users.find_one({"_id": user_id})
        if not user:
            return jsonify({"error": "User not found"}), 404

        print("📝 Inserting podcast into database:", podcast_item)
        result = collection.database.podcast.insert_one(podcast_item)

        print("✅ Podcast added successfully!")

        return jsonify(
            {
                "message": "Podcast added successfully",
                "podcast_id": podcast_id,  
                "redirect_url": "/index.html",
            }
        ), 201

    except Exception as e:
        print(f"❌ ERROR: {e}")  
        return jsonify({"error": f"Failed to add podcast: {str(e)}"}), 500
    
@podcast_bp.route("/get_podcast", methods=["GET"])
def get_podcast():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)  

        podcast = list(collection.database.podcast.find({"userid": user_id}))

        for podcast in podcast:
            podcast["_id"] = str(podcast["_id"])

        return jsonify({"podcast": podcast}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch podcast: {str(e)}"}), 500
    
@podcast_bp.route("/delete_podcast/<podcast_id>", methods=["DELETE"])
def delete_podcast(podcast_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)

        # Find the podcast
        podcast = collection.database.podcast.find_one({"_id": podcast_id})

        if not podcast:
            return jsonify({"error": "Podcast not found"}), 404

        # Check if the user is the owner of the podcast
        if podcast["userid"] != user_id:
            return jsonify({"error": "Permission denied"}), 403

        # Delete the podcast
        result = collection.database.podcast.delete_one({"_id": podcast_id})

        if result.deleted_count == 1:
            return jsonify({"message": "Podcast deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete podcast"}), 500

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to delete podcast: {str(e)}"}), 500

    
@podcast_bp.route("/edit_podcast/<podcast_id>", methods=["PUT"])
def edit_podcast(podcast_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)

        # Fetch the podcast by ID
        podcast = collection.database.podcast.find_one({"_id": podcast_id})

        if not podcast:
            return jsonify({"error": "Podcast not found"}), 404

        # Check if the user is the owner of the podcast
        if podcast["userid"] != user_id:
            return jsonify({"error": "Permission denied"}), 403

        # Get new data from the request
        data = request.get_json()

        # Create the update dictionary with the fields that can be modified
        update_data = {}
        if "podName" in data:
            update_data["podName"] = data["podName"]
        if "podRss" in data:
            update_data["podRss"] = data["podRss"]
        if "socialMedia" in data:
            update_data["socialMedia"] = data["socialMedia"]
        if "podEmail" in data:
            update_data["podEmail"] = data["podEmail"]
        if "guestUrl" in data:
            update_data["guestUrl"] = data["guestUrl"]

        result = collection.database.podcast.update_one(
            {"_id": podcast_id},
            {"$set": update_data} 
        )

        if result.modified_count == 1:
            return jsonify({"message": "Podcast updated successfully"}), 200
        else:
            return jsonify({"error": "Failed to update podcast"}), 500

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to update podcast: {str(e)}"}), 500


