from flask import request, jsonify, Blueprint, g
from database.mongo_connection import collection
from datetime import datetime, timezone
import uuid

guest_bp = Blueprint("guest_bp", __name__)

@guest_bp.route("/guest/add_guest", methods=["POST"])
def add_guest():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415
    try:
        data = request.get_json()
        guest_id = str(uuid.uuid4())
        guest_item = {
            "_id": guest_id,
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
            "created_at": datetime.now(timezone.utc)
        }
        result = collection.database.Guest.insert_one(guest_item)
        return jsonify({"message": "Guest added successfully", "guest_id": guest_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@guest_bp.route("/guest/get_guests", methods=["GET"])
def get_guests():
    try:
        guests_cursor = collection.database.Guest.find({})
        guests = []
        for guest in guests_cursor:
            guest["id"] = guest["_id"]
            if "created_at" in guest:
                guest["created_at"] = guest["created_at"].isoformat()
            guest.pop("_id", None)
            guests.append(guest)
        return jsonify({"guests": guests}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
