from flask import request, jsonify, Blueprint, g
from database.mongo_connection import collection
from datetime import datetime, timezone
import uuid

# Define Blueprint
team_bp = Blueprint("team_bp", __name__)

@team_bp.route("/add_team", methods=["POST"])
def add_team_member():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Validate Content-Type
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        data = request.get_json()
        print("📩 Received Data:", data)

        team_id = str(uuid.uuid4())
        user_id = str(g.user_id)

        team_item = {
            "_id": team_id,
            "UserID": user_id,
            "Name": data.get("name", "").strip(),
            "Role": data.get("role", "").strip(),
            "Email": data.get("email", "").strip(),
            "Phone": data.get("phone", "").strip(),
            "created_at": datetime.now(timezone.utc),
        }

        user = collection.database.User.find_one({"_id": user_id})
        if not user:
            return jsonify({"error": "User not found"}), 404

        print("📝 Inserting team member into database:", team_item)
        result = collection.database.Team.insert_one(team_item)

        print("✅ Team member added successfully!")

        return jsonify(
            {
                "message": "Team member added successfully",
                "team_id": team_id,
                "redirect_url": "/team.html",
            }
        ), 201

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to add team member: {str(e)}"}), 500

@team_bp.route("/get_team", methods=["GET"])
def get_team_members():
    try:
        team_members = list(collection.database.Team.find({}, {"_id": 0, "UserID": 0, "created_at": 0}))
        return jsonify(team_members), 200
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch team members: {str(e)}"}), 500
