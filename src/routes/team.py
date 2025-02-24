from flask import request, jsonify, Blueprint, g
from database.mongo_connection import collection
from datetime import datetime, timezone
import uuid
from marshmallow import ValidationError
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

        # Insert team data into the database (without user roles)
        team_item = {
            "_id": team_id,
            "name": validated_data.get("name", "").strip(),
            "email": validated_data.get("email", "").strip(),
            "phone": validated_data.get("phone", "").strip(),
            "isActive": validated_data.get("isActive", True),
            "joinedAt": validated_data.get("joinedAt", datetime.now(timezone.utc)),
            "lastActive": validated_data.get("lastActive", datetime.now(timezone.utc)),
            "members": []  # Start with an empty list of members
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
def get_teams():
    try:
        # 1️⃣ Fetch all teams
        teams = list(collection.database.Teams.find({}, {"created_at": 0}))  # Exclude created_at
        
        if not teams:
            return jsonify({"error": "No teams found"}), 404

        # 2️⃣ Fetch all user-to-team relationships
        user_team_links = list(collection.database.UserToTeams.find({}))

        # 3️⃣ Fetch all users from Users collection
        user_ids = [ut["userId"] for ut in user_team_links]
        users = list(collection.database.Users.find({"userId": {"$in": user_ids}}, {"_id": 0}))

        # 4️⃣ Merge users into their respective teams
        for team in teams:
            team_id = team["_id"]
            team_members = []

            # Find all users for this team
            for user_team in user_team_links:
                if user_team["teamId"] == team_id:
                    user = next((u for u in users if u["userId"] == user_team["userId"]), None)
                    if user:
                        user["role"] = user_team.get("role", "member")  # Assign role from UserToTeams
                        team_members.append(user)

            team["members"] = team_members  # Add members list

        return jsonify(teams), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch teams: {str(e)}"}), 500
