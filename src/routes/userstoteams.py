from flask import request, jsonify, Blueprint, g
from database.mongo_connection import collection
from datetime import datetime, timezone
from uuid import uuid4
from marshmallow import ValidationError
from Entities.users_to_teams import UserToTeamSchema

usertoteam_bp = Blueprint("usertoteam_bp", __name__)

#Use TeamSchema when you're dealing with information specific to a team, such as the team's name, role, email, and other properties related to the team itself.
#Use UserToTeamSchema when you're dealing with the relationship between a user and a team, such as adding a user to a team or querying which teams a particular user belongs to.

@usertoteam_bp.route("/add_users_to_teams", methods=["POST"])
def add_user_to_team():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        # Get incoming JSON data
        data = request.get_json()
        print("📩 Received Data:", data)

        # Validate with UserToTeamSchema
        try:
            user_to_team_schema = UserToTeamSchema()  # Validate relationship between user and team
            validated_data = user_to_team_schema.load(data)  # Validate and deserialize the user-team data
        except ValidationError as err:
            return jsonify({"error": "Invalid data", "details": err.messages}), 400

        # Generate a unique string-based _id (UUID)
        user_to_team_id = str(uuid4())

        # Create the user-to-team relationship document with the string _id
        user_to_team_item = {
            "_id": user_to_team_id,  # Set the _id to the generated UUID
            "userId": validated_data["userId"],  # User ID
            "teamId": validated_data["teamId"],  # Team ID
            "assignedAt": datetime.utcnow(),     # Timestamp when the user was added to the team
        }

        # Insert the user-team relationship into the database
        result = collection.database.UsersToTeams.insert_one(user_to_team_item)

        # Check if the insertion was successful
        if result.inserted_id:
            print("✅ User added to team successfully!")
            return jsonify(
                {
                    "message": "User added to team successfully",
                    "user_to_team_id": user_to_team_id,  # Return the generated ID
                }
            ), 201
        else:
            print("❌ Failed to insert user-team relationship")
            return jsonify({"error": "Failed to add user to team."}), 500

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to add user to team: {str(e)}"}), 500

    
@usertoteam_bp.route("/remove_users_from_teams", methods=["POST"])
def remove_user_from_team():
    if not g.user_id:  # Assuming user_id is stored in the global `g` object
        return jsonify({"error": "Unauthorized"}), 401

    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        # Get incoming JSON data
        data = request.get_json()
        print("📩 Received Data:", data)

        # Validate with UserToTeamSchema
        try:
            user_to_team_schema = UserToTeamSchema()  # Validate relationship between user and team
            validated_data = user_to_team_schema.load(data)  # Validate and deserialize the user-team data
        except ValidationError as err:
            return jsonify({"error": "Invalid data", "details": err.messages}), 400

        # Check if the user is actually assigned to this team
        user_team_relation = collection.database.UserTeams.find_one({
            "userId": validated_data["userId"],  # The user to be removed
            "teamId": validated_data["teamId"],  # From the specified team
        })

        if not user_team_relation:
            return jsonify({"error": "User not found in this team."}), 404

        # Delete the user-team relationship document
        result = collection.database.UserTeams.delete_one({
            "userId": validated_data["userId"],  # The user to be removed
            "teamId": validated_data["teamId"],  # From the specified team
        })

        if result.deleted_count == 0:
            return jsonify({"error": "Failed to remove user from team."}), 500

        print("✅ User removed from team successfully!")

        return jsonify({
            "message": "User removed from team successfully",
        }), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to remove user from team: {str(e)}"}), 500
    
    
