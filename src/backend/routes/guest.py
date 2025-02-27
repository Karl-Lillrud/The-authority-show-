from flask import request, jsonify, Blueprint, g
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
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    try:
        # Validate incoming data using the schema
        data = request.get_json()
        print("📩 Received Data:", data)

        # Deserialize and validate data using the schema
        try:
            guest_data = GuestSchema().load(data)  # This will validate the data
        except ValidationError as err:
            return jsonify({"error": f"Validation error: {err.messages}"}), 400

        guest_id = str(uuid.uuid4())
        user_id = str(g.user_id)

        # Check if the podcast exists
        podcast = collection.database.Podcasts.find_one(
            {"_id": guest_data["podcastId"]}
        )
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
        }

        # Insert the guest into the database
        collection.database.Guests.insert_one(guest_item)

        print("✅ Guest added successfully!")
        return (
            jsonify({"message": "Guest added successfully", "guest_id": guest_id}),
            201,
        )

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to add guest: {str(e)}"}), 500


@guest_bp.route("/get_guests", methods=["GET"]) #http://127.0.0.1:8000/get_guests?podcastId=<podcastId>
def get_guests():                               #If guest is booked to podcast it should have a podcastId       
    # Check if podcastId is provided in the query parameters
    podcast_id = request.args.get("podcastId")
    if not podcast_id:
        return jsonify({"error": "podcastId is required"}), 400

    # Check if user_id is present in the session (g.user_id)
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)

        # Query for guests associated with the podcastId
        guests_cursor = collection.database.Guests.find({"podcastId": podcast_id})

        guests = []
        for guest in guests_cursor:
            guest["id"] = str(guest["_id"])  # Convert MongoDB ObjectId to string for JSON serialization
            if "created_at" in guest:
                guest["created_at"] = guest["created_at"].isoformat()  # Convert datetime to ISO format string
            guest.pop("_id", None)  # Remove MongoDB-specific _id field
            guests.append(guest)

        if not guests:
            return jsonify({"guests": []}), 200  # Return empty list if no guests are found

        return jsonify({"guests": guests}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch guests: {str(e)}"}), 500



    
@guest_bp.route("/edit_guests/<guest_id>", methods=["PUT"]) #Need som polishing
def edit_guest(guest_id):
    if not g.user_id: 
        return jsonify({"error": "Unauthorized"}), 401

    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

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


@guest_bp.route("/delete_guests/<guest_id>", methods=["DELETE"]) #probably need some polishing aswell
def delete_guest(guest_id):
    # Check for authentication
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # (Optional) Content-Type check: DELETE requests might not always have a JSON body.
    # If your client doesn't send a Content-Type header for DELETE, you can remove this check.
    if request.content_type and request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        user_id = str(g.user_id)
        
        # Delete the guest that belongs to the current user
        result = collection.database.Guests.delete_one({"_id": guest_id, "userid": user_id})
        
        if result.deleted_count == 0:
            return jsonify({"error": "Guest not found or unauthorized"}), 404

        return jsonify({"message": "Guest deleted successfully"}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to delete guest: {str(e)}"}), 500



