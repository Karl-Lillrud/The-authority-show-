from flask import request, jsonify, Blueprint, g
from database.mongo_connection import collection
from datetime import datetime, timezone
import uuid

# Define Blueprint
team_bp = Blueprint("team_bp", __name__)

@team_bp.route("/add_teams", methods=["POST"])
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
            "Name": data.get("name", "").strip(),
            "Role": data.get("role", "").strip(),
            "Email": data.get("email", "").strip(),
            "Phone": data.get("phone", "").strip(),
            "created_at": datetime.now(timezone.utc),
        }

        user = collection.database.Users.find_one({"_id": user_id})
        if not user:
            return jsonify({"error": "User not found"}), 404

        print("📝 Inserting team member into database:", team_item)
        result = collection.database.Teams.insert_one(team_item)

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

@team_bp.route("/get_teams", methods=["GET"])
def get_team_members():
    try:
        # Fetch all teams and exclude the unnecessary fields (_id and created_at, if needed)
        team_members = list(collection.database.Teams.find({}, {"_id": 0, "created_at": 0})) 

        # Debug: Print the fetched team members to verify the data
        print("Fetched team members:", team_members)

        if not team_members:
            return jsonify({"error": "No team members found"}), 404

        return jsonify(team_members), 200
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch team members: {str(e)}"}), 500

@team_bp.route("/update_team/<team_id>", methods=["PUT"])
def update_team_member(team_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415
    try:
        data = request.get_json()
        update_fields = {
            "Name": data.get("name", "").strip(),
            "Role": data.get("role", "").strip(),
            "Email": data.get("email", "").strip(),
            "Phone": data.get("phone", "").strip()
        }
        result = collection.database.Team.update_one({"_id": team_id}, {"$set": update_fields})
        if result.modified_count == 0:
            return jsonify({"error": "Team member not found or no changes made"}), 404
        return jsonify({"message": "Team member updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to update team member: {str(e)}"}), 500

@team_bp.route("/delete_team/<team_id>", methods=["DELETE"])
def delete_team_member(team_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        result = collection.database.Team.delete_one({"_id": team_id})
        if result.deleted_count == 0:
            return jsonify({"error": "Team member not found"}), 404
        return jsonify({"message": "Team member deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to delete team member: {str(e)}"}), 500
