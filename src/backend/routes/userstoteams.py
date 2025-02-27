from flask import request, jsonify, Blueprint, g
from backend.database.mongo_connection import collection
from datetime import datetime, timezone
from marshmallow import ValidationError
from backend.models.users_to_teams import UserToTeamSchema
from uuid import uuid4

userstoteams_bp = Blueprint("userstoteams_bp", __name__)

# Use TeamSchema when you're dealing with information specific to a team, such as the team's name, role, email, and other properties related to the team itself.
# Use UserToTeamSchema when you're dealing with the relationship between a user and a team, such as adding a user to a team or querying which teams a particular user belongs to.


@userstoteams_bp.route("/add_users_to_teams", methods=["POST"])
def add_user_to_team():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    try:
        # Get incoming JSON data
        data = request.get_json()
        print("📩 Received Data:", data)

        # Validate with UserToTeamSchema
        try:
            user_to_team_schema = (
                UserToTeamSchema()
            )  # Validate relationship between user and team
            validated_data = user_to_team_schema.load(
                data
            )  # Validate and deserialize the user-team data
        except ValidationError as err:
            return jsonify({"error": "Invalid data", "details": err.messages}), 400

        user_to_team_id = str(uuid4())

        user_to_team_item = {
            "_id": user_to_team_id,
            "userId": validated_data["userId"],
            "teamId": validated_data["teamId"],
            "role": validated_data["role"],
            "assignedAt": datetime.utcnow(),
        }

        # Insert the user-team relationship into the database
        result = collection.database.UsersToTeams.insert_one(user_to_team_item)

        # Check if the insertion was successful
        if result.inserted_id:
            print("✅ User added to team successfully!")
            return (
                jsonify(
                    {
                        "message": "User added to team successfully",
                        "user_to_team_id": user_to_team_id,  # Return the generated ID
                    }
                ),
                201,
            )
        else:
            print("❌ Failed to insert user-team relationship")
            return jsonify({"error": "Failed to add user to team."}), 500

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to add user to team: {str(e)}"}), 500


@userstoteams_bp.route("/remove_users_from_teams", methods=["POST"])
def remove_user_from_team():
    if not g.user_id:  # Assuming user_id is stored in the global `g` object
        return jsonify({"error": "Unauthorized"}), 401

    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    try:
        # Get incoming JSON data
        data = request.get_json()
        print("📩 Received Data:", data)

        # Validate with UserToTeamSchema
        try:
            user_to_team_schema = (
                UserToTeamSchema()
            )  # Validate relationship between user and team
            validated_data = user_to_team_schema.load(
                data
            )  # Validate and deserialize the user-team data
        except ValidationError as err:
            return jsonify({"error": "Invalid data", "details": err.messages}), 400

        # Check if the user is actually assigned to this team
        user_team_relation = collection.database.UsersToTeams.find_one(
            {
                "userId": validated_data["userId"],  # The user to be removed
                "teamId": validated_data["teamId"],  # From the specified team
            }
        )

        if not user_team_relation:
            return jsonify({"error": "User not found in this team."}), 404

        # Delete the user-team relationship document
        result = collection.database.UsersToTeams.delete_one(
            {
                "userId": validated_data["userId"],  # The user to be removed
                "teamId": validated_data["teamId"],  # From the specified team
            }
        )

        if result.deleted_count == 0:
            return jsonify({"error": "Failed to remove user from team."}), 500

        print("✅ User removed from team successfully!")

        return (
            jsonify(
                {
                    "message": "User removed from team successfully",
                }
            ),
            200,
        )

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to remove user from team: {str(e)}"}), 500


@userstoteams_bp.route("/get_teams_members/<team_id>", methods=["GET"])
def get_team_members(team_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Find all users linked to the given teamId
        team_members = list(
            collection.database.UsersToTeams.find({"teamId": team_id}, {"_id": 0})
        )

        if not team_members:
            return jsonify({"message": "No members found for this team"}), 404

        # Fetch user details for each member
        members_details = []
        for member in team_members:
            user_id = member["userId"]
            user_details = collection.database.Users.find_one(
                {"_id": user_id}, {"_id": 0}
            )  # Assuming Users collection holds user details

            if user_details:
                # Add role and other details to the user data
                user_details["role"] = member.get(
                    "role", "member"
                )  # Default to 'member' if no role is assigned
                members_details.append(user_details)

        return jsonify({"teamId": team_id, "members": members_details}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to retrieve team members: {str(e)}"}), 500
