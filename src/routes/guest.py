from flask import request, jsonify, Blueprint, g
from database.mongo_connection import collection
from datetime import datetime, timezone
import uuid
guest_bp = Blueprint("guest_bp", __name__)
from flask import Blueprint, request, jsonify, g
import uuid
from datetime import datetime, timezone

guest_bp = Blueprint("guest", __name__)

@guest_bp.route("/guest/add_guest", methods=["POST"])
def add_guest():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        data = request.get_json()
        print("📩 Received Data:", data)

        guest_id = str(uuid.uuid4())  
        user_id = str(g.user_id) 

        guest_item = {
            "_id": guest_id,
            "userid": user_id,  
            "name": data.get("name", "").strip(),
            "image": data.get("image", "default-profile.png"),
            "tags": data.get("tags", []),
            "description": data.get("description", ""),
            "bio": data.get("bio", data.get("description", "")),
            "email": data.get("email", "").strip(),
            "linkedin": data.get("linkedin", "").strip(),
            "twitter": data.get("twitter", "").strip(),
            "areasOfInterest": data.get("areasOfInterest", []),
            "status": "scheduled",
            "scheduled": 0,
            "completed": 0,
            "created_at": datetime.now(timezone.utc),
        }

        user = collection.database.User.find_one({"_id": user_id})
        if not user:
            return jsonify({"error": "User not found"}), 404

        print("📝 Inserting guest into database:", guest_item)
        collection.database.Guest.insert_one(guest_item)

        print("✅ Guest added successfully!")
        return jsonify({"message": "Guest added successfully", "guest_id": guest_id}), 201

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to add guest: {str(e)}"}), 500


@guest_bp.route("/guest/get_guests", methods=["GET"])
def get_guests():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)  # Ensure we filter by logged-in user
        guests_cursor = collection.database.Guest.find({"userid": user_id})

        guests = []
        for guest in guests_cursor:
            guest["id"] = guest["_id"]  # Keep ID for reference
            if "created_at" in guest:
                guest["created_at"] = guest["created_at"].isoformat()
            guest.pop("_id", None)  # Remove MongoDB-specific _id field
            guests.append(guest)

        return jsonify({"guests": guests}), 200
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch guests: {str(e)}"}), 500
