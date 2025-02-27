from flask import request, jsonify, Blueprint, g, session
from backend.database.mongo_connection import collection
from datetime import datetime, timezone
from marshmallow import ValidationError
from backend.models.guests import GuestSchema  # Import your GuestSchema here
import uuid

guest_bp = Blueprint("guest_bp", __name__)

@guest_bp.route("/add_guests", methods=["POST"])
def add_guest():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        data = request.get_json()
        print("📩 Received Data:", data)

        try:
            guest_data = GuestSchema().load(data)
        except ValidationError as err:
            return jsonify({"error": f"Validation error: {err.messages}"}), 400

        guest_id = str(uuid.uuid4())
        user_id = str(g.user_id)

        # Check if the podcast exists
        podcast = collection.database.Podcasts.find_one({"_id": guest_data["podcastId"]})
        if not podcast:
            return jsonify({"error": "Podcast not found"}), 404

        guest_item = {
            "_id": guest_id,
            "podcastId": guest_data["podcastId"],
            "name": guest_data["name"].strip(),
            "image": guest_data.get("image", ""),
            "tags": guest_data.get("tags", []),
            "description": guest_data.get("description", ""),
            "bio": guest_data.get("bio", guest_data.get("description", "")),
            "email": guest_data["email"].strip(),
            "linkedin": guest_data.get("linkedin", "").strip(),
            "twitter": guest_data.get("twitter", "").strip(),
            "areasOfInterest": guest_data.get("areasOfInterest", []),
            "status": "scheduled",
            "scheduled": 0,
            "completed": 0,
            "created_at": datetime.now(timezone.utc),
            "user_id": user_id
        }

        collection.database.Guests.insert_one(guest_item)

        print("✅ Guest added successfully!")
        return jsonify({"message": "Guest added successfully", "guest_id": guest_id}), 201

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to add guest: {str(e)}"}), 500

@guest_bp.route('/get_guests', methods=['GET'])
def get_guests():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    # First, fetch the user's account document to get the correct account ID
    user_account = collection.database.Accounts.find_one({"userId": user_id})
    if not user_account:
        return jsonify({"error": "Account not found for this user"}), 404

    # Use the custom 'id' field if available, otherwise use the MongoDB _id
    if "id" in user_account:
        account_id = user_account["id"]
    else:
        account_id = str(user_account["_id"])

    # Now query the Podcasts collection using the correct accountId
    podcast = collection.database.Podcasts.find_one({"accountId": account_id})
    if not podcast:
        return jsonify({"error": "Podcast not found for this user"}), 404

    podcast_id = podcast["_id"]

    guests_cursor = collection.database.Guests.find({"podcastId": podcast_id})
    guest_list = []
    for guest in guests_cursor:
        guest_list.append({
            "id": str(guest.get("_id")),
            "name": guest.get("name"),
            "image": guest.get("image"),
            "bio": guest.get("bio"),
            "tags": guest.get("tags", []),
            "email": guest.get("email"),
            "linkedin": guest.get("linkedin"),
            "twitter": guest.get("twitter"),
            "areasOfInterest": guest.get("areasOfInterest", [])
        })

    return jsonify({"guests": guest_list})

@guest_bp.route("/edit_guests/<guest_id>", methods=["PUT"])
def edit_guest(guest_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        data = request.get_json()
        print("📩 Received Data:", data)

        if not guest_id:
            return jsonify({"error": "Guest ID is required"}), 400

        user_id = str(g.user_id)
        update_fields = {
            "name": data.get("name", "").strip(),
            "image": data.get("image", "default-profile.png"),
            "tags": data.get("tags", []),
            "description": data.get("description", ""),
            "bio": data.get("bio", data.get("description", "")),
            "email": data.get("email", "").strip(),
            "linkedin": data.get("linkedin", "").strip(),
            "twitter": data.get("twitter", "").strip(),
            "areasOfInterest": data.get("areasOfInterest", []),
        }

        print("📝 Update Fields:", update_fields)

        result = collection.database.Guests.update_one(
            {"_id": guest_id, "userid": user_id}, {"$set": update_fields}
        )

        if result.matched_count == 0:
            return jsonify({"error": "Guest not found or unauthorized"}), 404

        return jsonify({"message": "Guest updated successfully"}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to update guest: {str(e)}"}), 500

@guest_bp.route("/delete_guests/<guest_id>", methods=["DELETE"])
def delete_guest(guest_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if request.content_type and request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        user_id = str(g.user_id)
        result = collection.database.Guests.delete_one({"_id": guest_id, "userid": user_id})
        if result.deleted_count == 0:
            return jsonify({"error": "Guest not found or unauthorized"}), 404

        return jsonify({"message": "Guest deleted successfully"}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to delete guest: {str(e)}"}), 500
