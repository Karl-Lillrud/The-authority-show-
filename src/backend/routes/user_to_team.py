from flask import request, jsonify, Blueprint, g
from backend.database.mongo_connection import collection
from datetime import datetime, timedelta, timezone
from marshmallow import ValidationError
from backend.models.users_to_teams import UserToTeamSchema
from uuid import uuid4

usertoteam_bp = Blueprint("usertoteam_bp", __name__)

# Use TeamSchema when you're dealing with information specific to a team, such as the team's name, role, email, and other properties related to the team itself.
# Use UserToTeamSchema when you're dealing with the relationship between a user and a team, such as adding a user to a team or querying which teams a particular user belongs to.


@usertoteam_bp.route("/add_users_to_teams", methods=["POST"])
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
    
    # This is for inviting a user to a team (pending invite)
@usertoteam_bp.route("/invite_user_to_team", methods=["POST"])
def invite_user_to_team():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        data = request.get_json()
        print("📩 Received Invite Data:", data)

        # Validate invitation
        user_to_team_schema = UserToTeamSchema()
        validated_data = user_to_team_schema.load(data)

        # Check if the team exists
        team = collection.database.Teams.find_one({"_id": validated_data["teamId"]})
        if not team:
            return jsonify({"error": "Team not found"}), 404

        # Check if there's an existing pending invite or user already in team
        existing_invite = collection.database.UsersToTeams.find_one({
            "userId": validated_data["userId"],
            "teamId": validated_data["teamId"],
            "status": "pending"
        })
        if existing_invite:
            return jsonify({"error": "User is already invited or in this team."}), 400

        # Generate an invite ID and expiration date
        invite_id = str(uuid4())
        expiration_date = datetime.utcnow() + timedelta(hours=100) 

        invite_item = {
            "_id": invite_id,
            "userId": validated_data["userId"],
            "teamId": validated_data["teamId"],
            "role": validated_data["role"],
            "status": "pending",  # Invitation status
            "expiration_date": expiration_date,
            "assignedAt": datetime.utcnow(),
        }

        result = collection.database.UsersToTeams.insert_one(invite_item)

        if result.inserted_id:
            return jsonify({"message": "User invited to team successfully", "invite_id": invite_id}), 201
        else:
            return jsonify({"error": "Failed to send team invite."}), 500

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to invite user: {str(e)}"}), 500


@usertoteam_bp.route("/remove_users_from_teams", methods=["POST"])
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


@usertoteam_bp.route("/get_teams_members/<team_id>", methods=["GET"])
def get_team_members(team_id):
    """Retrieve all accepted members of a team."""
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Find all users with status "accepted" in the given team
        team_members = list(collection.database.UsersToTeams.find({"teamId": team_id, "status": "accepted"}, {"_id": 0}))

        if not team_members:
            return jsonify({"message": "No members found for this team"}), 404

        members_details = []
        for member in team_members:
            user_id = member["userId"]
            user_details = collection.database.Users.find_one({"_id": user_id}, {"_id": 0})

            if user_details:
                user_details["role"] = member.get("role", "member")
                members_details.append(user_details)

        return jsonify({"teamId": team_id, "members": members_details}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to retrieve team members: {str(e)}"}), 500
    
@usertoteam_bp.route("/respond_invite", methods=["POST"])
def respond_invite():
    """Allows a user to accept or decline a team invite."""
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        data = request.get_json()
        print("📩 Invite Response Data:", data)

        user_id = g.user_id  # Ensure the logged-in user is the one responding
        team_id = data.get("teamId")
        response = data.get("response")  # Should be "accepted" or "declined"

        if response not in ["accepted", "declined"]:
            return jsonify({"error": "Invalid response. Use 'accepted' or 'declined'."}), 400

        invite = collection.database.UsersToTeams.find_one({
            "userId": user_id,
            "teamId": team_id,
            "status": "pending"
        })

        if not invite:
            return jsonify({"error": "No pending invite found."}), 404

        if response == "declined":
            collection.database.UsersToTeams.delete_one({"_id": invite["_id"]})
            return jsonify({"message": "Invite declined successfully."}), 200

        # Update status to "accepted" and assign user to team
        collection.database.UsersToTeams.update_one(
            {"_id": invite["_id"]}, 
            {"$set": {"status": "accepted"}}
        )

        # Optionally, add the user to the team's member list (if applicable)
        # Additional code to assign the user as a member of the team.

        return jsonify({"message": "Invite accepted successfully!"}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to respond to invite: {str(e)}"}), 500



