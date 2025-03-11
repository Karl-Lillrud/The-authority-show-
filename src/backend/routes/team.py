from flask import request, jsonify, Blueprint, g
from backend.database.mongo_connection import collection
from datetime import datetime, timezone
from marshmallow import ValidationError
from backend.models.teams import TeamSchema
import uuid

# Define Blueprint
team_bp = Blueprint("team_bp", __name__)

#SHOULD ONLY BE USED FOR SPECIFIC DATA CRUD OPERATIONS
#EXTRA FUNCTIONALITY BESIDES CRUD OPERATIONS SHOULD BE IN SERVICES

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

        # Generate a unique team ID
        team_id = str(uuid.uuid4())

        # Prepare team data
        team_item = {
            "_id": team_id,
            "name": validated_data.get("name", "").strip(),
            "email": validated_data.get("email", "").strip(),
            "phone": validated_data.get("phone", "").strip(),
            "isActive": validated_data.get("isActive", True),
            "joinedAt": validated_data.get("joinedAt", datetime.now(timezone.utc)),
            "lastActive": validated_data.get("lastActive", datetime.now(timezone.utc)),
            "members": [],  # Initially no members, we'll add the creator first
        }

        # Insert the team into the Teams collection
        result = collection.database.Teams.insert_one(team_item)
        if result.inserted_id:
            print("✅ Team added successfully!")

        # Get current user ID (the creator)
        user_id = str(g.user_id)  # Ensure this comes from the current logged-in user
        print("👤 Team creator user ID:", user_id)

        # Add the creator to the user_to_team collection
        user_to_team_item = {
            "userId": user_id,
            "teamId": team_id,
            "role": "creator",  # The role of the user who created the team
            "assignedAt": datetime.now(timezone.utc),
        }

        # Insert the user-team relationship into the UsersToTeams collection
        collection.database.UsersToTeams.insert_one(user_to_team_item)

        # Update the team with its members, adding the creator to the team
        team_item["members"].append({"userId": user_id, "role": "creator"})

        # Update the team document with its creator
        collection.database.Teams.update_one(
            {"_id": team_id}, {"$set": {"members": team_item["members"]}}
        )

        return (
            jsonify(
                {
                    "message": "Team and creator added successfully",
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
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)

        # Get teams created by the user
        created_teams = list(collection.database.Teams.find({"createdBy": user_id}, {"created_at": 0}))

        # Get teams where the user is a member (from UsersToTeams)
        user_team_links = list(collection.database.UsersToTeams.find({"userId": user_id}, {"teamId": 1, "_id": 0}))
        joined_team_ids = [ut["teamId"] for ut in user_team_links]

        # Fetch those teams if not already included
        joined_teams = list(collection.database.Teams.find({"_id": {"$in": joined_team_ids}}, {"created_at": 0}))

        # Merge and remove duplicates
        teams = {str(team["_id"]): team for team in created_teams + joined_teams}
        for team in teams.values():
            team["_id"] = str(team["_id"])
            # Fetch all podcasts connected to this team
            podcasts = list(collection.database.Podcasts.find({"teamId": team["_id"]}))
            if podcasts:
                team["podNames"] = ", ".join([p.get("podName", "N/A") for p in podcasts])
            else:
                team["podNames"] = "N/A"

        return jsonify(list(teams.values())), 200

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve teams: {str(e)}"}), 500

@team_bp.route("/delete_team/<team_id>", methods=["DELETE"])
def delete_team(team_id):
    try:
        # Step 1: Check if the team exists
        team = collection.database.Teams.find_one({"_id": team_id})
        if not team:
            return jsonify({"error": "Team not found"}), 404

        # Step 2: Delete associated user-team relationships
        collection.database.UsersToTeams.delete_many({"teamId": team_id})
        print(f"✅ Deleted all user-team relationships for team {team_id}!")

        # Step 3: Delete the team itself from the Teams collection
        result = collection.database.Teams.delete_one({"_id": team_id})
        if result.deleted_count == 0:
            return jsonify({"error": "Failed to delete the team"}), 500

        print(f"✅ Team {team_id} and all members deleted successfully!")

        # Step 4: Remove the teamId from all podcasts connected to this team
        update_result = collection.database.Podcasts.update_many(
            {"teamId": team_id},
            {"$set": {"teamId": None}}
        )
        print(f"✅ Removed teamId from {update_result.modified_count} podcasts for team {team_id}")

        return jsonify({"message": f"Team {team_id} and all members deleted successfully!"}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to delete podcast or team: {str(e)}"}), 500

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
