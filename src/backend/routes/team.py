from flask import request, jsonify, Blueprint, g
from backend.database.mongo_connection import collection
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
        teams = list(collection.database.Teams.find({}, {"created_at": 0}))
        if not teams:
            return jsonify({"error": "No teams found"}), 404

        user_team_links = list(collection.database.UsersToTeams.find({}))  # use UsersToTeams

        user_ids = [ut["userId"] for ut in user_team_links]
        users = list(collection.database.Users.find({"userId": {"$in": user_ids}}, {"_id": 0}))
        user_dict = {user["userId"]: user for user in users}

        team_members_map = {}
        for user_team in user_team_links:
            # Assign team_id from the user-team link
            team_id = user_team["teamId"]
            if team_id not in team_members_map:
                team_members_map[team_id] = []
            user = user_dict.get(user_team["userId"])
            if user:
                user["role"] = user_team.get("role", "member")
                team_members_map[team_id].append(user)

        # Merge users into their respective teams and convert _id to string
        for team in teams:
            team_id = team["_id"]
            team["members"] = team_members_map.get(team_id, [])
            team["_id"] = str(team["_id"])  # convert ObjectId to string

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

@team_bp.route("/edit_team/<team_id>", methods=["PUT"])
def edit_team(team_id):
    try:
        data = request.get_json()
        team = collection.database.Teams.find_one({"_id": team_id})
        if not team:
            return jsonify({"error": "Team not found"}), 404

        try:
            team_schema = TeamSchema()
            # Allow partial update
            validated_data = team_schema.load(data, partial=True)
        except ValidationError as err:
            return jsonify({"error": "Invalid data", "details": err.messages}), 400

        update_fields = {}
        if "name" in validated_data:
            update_fields["name"] = validated_data["name"].strip()
        if "email" in validated_data:
            update_fields["email"] = validated_data["email"].strip()
        if "description" in validated_data:
            update_fields["description"] = validated_data["description"].strip()
        if "members" in validated_data:
            update_fields["members"] = validated_data["members"]

        if update_fields:
            result = collection.database.Teams.update_one(
                {"_id": team_id}, {"$set": update_fields}
            )
            if result.modified_count > 0:
                return jsonify({"message": "Team updated successfully!"}), 200
            else:
                return jsonify({"message": "No changes made to the team."}), 200
        else:
            return jsonify({"message": "No valid fields provided for update."}), 400

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to edit team: {str(e)}"}), 500
