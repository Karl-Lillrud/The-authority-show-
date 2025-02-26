from flask import request, jsonify, Blueprint, g
from database.mongo_connection import collection
from datetime import datetime, timezone
from marshmallow import ValidationError
from backend.models.teams import TeamSchema
import uuid

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
            validated_data = team_schema.load(
                data
            )  # Validate and deserialize team data
        except ValidationError as err:
            return jsonify({"error": "Invalid data", "details": err.messages}), 400

        # Generate a unique team ID
        team_id = str(
            uuid.uuid4()
        )  # NÄR ETT TEAM SKA BORT SKA ALL USRTOTEAMS MED DETTA TEAMET OCKSÅ BORT

        # Prepare team data
        team_item = {
            "_id": team_id,
            "name": validated_data.get("name", "").strip(),
            "email": validated_data.get("email", "").strip(),
            "phone": validated_data.get("phone", "").strip(),
            "isActive": validated_data.get("isActive", True),
            "joinedAt": validated_data.get("joinedAt", datetime.now(timezone.utc)),
            "lastActive": validated_data.get("lastActive", datetime.now(timezone.utc)),
            "members": [],
        }

        # Insert the team into the Teams collection
        result = collection.database.Teams.insert_one(team_item)
        if result.inserted_id:
            print("✅ Team added successfully!")

        users_data = validated_data.get("users", [])

        for user in users_data:
            user_id = user.get("userId")
            role = user.get("role", "member")

            user_to_team_item = {
                "userId": user_id,
                "teamId": team_id,
                "role": role,
                "assignedAt": datetime.now(timezone.utc()),
            }

            collection.database.UsersToTeams.insert_one(user_to_team_item)

            team_item["members"].append({"userId": user_id, "role": role})

        # Update the team with its members (this step can be skipped if not needed)
        collection.database.Teams.update_one(
            {"_id": team_id}, {"$set": {"members": team_item["members"]}}
        )

        return (
            jsonify(
                {
                    "message": "Team and members added successfully",
                    "team_id": team_id,
                    "redirect_url": "/team.html",  # Example URL to redirect to after adding team
                }
            ),
            201,
        )

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to add team: {str(e)}"}), 500


@team_bp.route("/get_teams", methods=["GET"])
def get_teams():
    try:
        # 1️⃣ Fetch all teams
        teams = list(
            collection.database.Teams.find({}, {"created_at": 0})
        )  # Exclude created_at

        if not teams:
            return jsonify({"error": "No teams found"}), 404

        # 2️⃣ Fetch all user-to-team relationships
        user_team_links = list(collection.database.UserToTeams.find({}))

        # 3️⃣ Fetch all users from Users collection
        user_ids = [ut["userId"] for ut in user_team_links]
        users = list(
            collection.database.Users.find({"userId": {"$in": user_ids}}, {"_id": 0})
        )

        # 4️⃣ Create a dictionary of users for faster lookup by userId
        user_dict = {user["userId"]: user for user in users}

        # 5️⃣ Group user-to-team relationships by teamId for faster processing
        team_members_map = {}
        for user_team in user_team_links:
            team_id = user_team["teamId"]
            if team_id not in team_members_map:
                team_members_map[team_id] = []
            # Attach role to the user from the UserToTeams collection
            user = user_dict.get(user_team["userId"])
            if user:
                user["role"] = user_team.get(
                    "role", "member"
                )  # Default to "member" if role is not set
                team_members_map[team_id].append(user)

        # 6️⃣ Merge users into their respective teams
        for team in teams:
            team_id = team["_id"]
            # Set the members for the team from the map
            team["members"] = team_members_map.get(team_id, [])

        return jsonify(teams), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to retrieve teams: {str(e)}"}), 500


@team_bp.route("/delete_team/<team_id>", methods=["DELETE"])
def delete_team(team_id):
    try:
        # Step 1: Check if the team exists
        team = collection.database.Teams.find_one({"_id": team_id})

        if not team:
            return jsonify({"error": "Team not found"}), 404

        # Step 2: Delete associated user-team relationships
        user_team_relations = collection.database.UserToTeams.find({"teamId": team_id})

        if user_team_relations:
            # Remove all user-team relationships for the team
            collection.database.UsersToTeams.delete_many({"teamId": team_id})
            print(f"✅ Deleted all user-team relationships for team {team_id}!")

        # Step 3: Delete the team itself from the Teams collection
        result = collection.database.Teams.delete_one({"_id": team_id})

        if result.deleted_count == 0:
            return jsonify({"error": "Failed to delete the team"}), 500

        print(f"✅ Team {team_id} and all members deleted successfully!")

        return (
            jsonify(
                {"message": f"Team {team_id} and all members deleted successfully!"}
            ),
            200,
        )

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to delete the team: {str(e)}"}), 500
