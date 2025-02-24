from flask import request, jsonify, Blueprint, g
from database.mongo_connection import collection
from datetime import datetime, timezone
import uuid
from marshmallow import ValidationError
from Entities.users_to_teams import UserToTeamSchema
from Entities.teams import TeamSchema

# Define Blueprint
team_bp = Blueprint("team_bp", __name__)

@team_bp.route("/add_teams", methods=["POST"])
def add_team():
    try:
        data = request.get_json()
        print("📩 Received Data:", data)

        # Validate with TeamSchema
        try:
            team_schema = TeamSchema()
            validated_data = team_schema.load(data)  # Validate and deserialize team data
        except ValidationError as err:
            return jsonify({"error": "Invalid data", "details": err.messages}), 400

        team_id = str(uuid.uuid4())  # Generate a unique team ID

        # Insert team data into the database
        team_item = {
            "_id": team_id,
            "name": validated_data.get("name", "").strip(),
            "role": validated_data.get("role", []),  # Can be a list of roles like ['owner', 'member']
            "email": validated_data.get("email", "").strip(),
            "phone": validated_data.get("phone", "").strip(),
            "isActive": validated_data.get("isActive", True),
            "joinedAt": validated_data.get("joinedAt", datetime.now(timezone.utc)),
            "lastActive": validated_data.get("lastActive", datetime.now(timezone.utc)),
        }

        # Insert into Teams collection
        result = collection.database.Teams.insert_one(team_item)

        print("✅ Team added successfully!")

        return jsonify(
            {
                "message": "Team added successfully",
                "team_id": team_id,
                "redirect_url": "/team.html",  # Example URL to redirect to after adding team
            }
        ), 201

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to add team: {str(e)}"}), 500
    
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
        result = collection.database.Teams.update_one({"_id": team_id}, {"$set": update_fields})
        if result.modified_count == 0:
            return jsonify({"error": "Team member not found or no changes made"}), 404
        return jsonify({"message": "Team member updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to update team member: {str(e)}"}), 500

@team_bp.route("/delete_teams/<team_id>", methods=["DELETE"])
def delete_team(team_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # First, delete the team from the Teams collection
        result = collection.database.Teams.delete_one({"_id": team_id})
        
        if result.deleted_count == 0:
            return jsonify({"error": "Team not found"}), 404
        
        # Then, remove any references to this team in the UserTeams collection
        result_user_team = collection.database.Teams.delete_many({"teamId": team_id})
        
        if result_user_team.deleted_count > 0: # If any usertoteam associations were removed
            print(f"🧹 Removed {result_user_team.deleted_count} user-team associations.")
        
        # Return success message
        return jsonify({"message": "Team and associated user memberships deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to delete team: {str(e)}"}), 500
