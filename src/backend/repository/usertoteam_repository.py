import logging
from datetime import datetime
from backend.database.mongo_connection import collection
from backend.models.users_to_teams import UserToTeamSchema
from marshmallow import ValidationError
from uuid import uuid4

logger = logging.getLogger(__name__)


class UserToTeamRepository:
    def __init__(self):
        self.users_to_teams_collection = collection.database.UsersToTeams
        self.teams_collection = collection.database.Teams
        self.users_collection = collection.database.Users

    def add_user_to_team(self, data):
        try:
            user_to_team_schema = UserToTeamSchema()
            validated_data = user_to_team_schema.load(data)

            user_id = str(validated_data.get("userId"))
            team_id = str(validated_data.get("teamId"))
            role = validated_data.get("role", "member")

            team = self.teams_collection.find_one({"_id": team_id})
            if not team:
                return {"error": "Team not found"}, 404

            user = self.users_collection.find_one({"_id": user_id})
            if not user:
                return {"error": "User not found"}, 404

            existing_user_team = self.users_to_teams_collection.find_one(
                {"userId": user_id, "teamId": team_id}
            )
            if existing_user_team:
                return {"error": "User is already a member of the team"}, 400

            user_to_team_id = str(uuid4())

            user_to_team_item = {
                "_id": user_to_team_id,
                "userId": user_id,
                "teamId": team_id,
                "role": role,
                "assignedAt": datetime.utcnow(),
            }

            result = self.users_to_teams_collection.insert_one(user_to_team_item)

            if result.inserted_id:
                return {
                    "message": "User added to team successfully",
                    "user_to_team_id": user_to_team_id,
                }, 201
            else:
                return {"error": "Failed to add user to team."}, 500

        except ValidationError as err:
            return {"error": "Invalid data", "details": err.messages}, 400
        except Exception as e:
            logger.error(f"Error adding user to team: {e}", exc_info=True)
            return {"error": f"Failed to add user to team: {str(e)}"}, 500

    def remove_user_from_team(self, data):
        try:
            user_to_team_schema = UserToTeamSchema()
            validated_data = user_to_team_schema.load(data)

            user_team_relation = self.users_to_teams_collection.find_one(
                {
                    "userId": validated_data["userId"],
                    "teamId": validated_data["teamId"],
                }
            )

            if not user_team_relation:
                return {"error": "User not found in this team."}, 404

            result = self.users_to_teams_collection.delete_one(
                {
                    "userId": validated_data["userId"],
                    "teamId": validated_data["teamId"],
                }
            )

            if result.deleted_count == 0:
                return {"error": "Failed to remove user from team."}, 500

            return {"message": "User removed from team successfully"}, 200

        except ValidationError as err:
            return {"error": "Invalid data", "details": err.messages}, 400
        except Exception as e:
            logger.error(f"Error removing user from team: {e}", exc_info=True)
            return {"error": f"Failed to remove user from team: {str(e)}"}, 500

    def get_team_members(self, team_id):
        try:
            team_members = list(
                self.users_to_teams_collection.find({"teamId": team_id}, {"_id": 0})
            )

            if not team_members:
                return {"message": "No members found for this team"}, 404

            members_details = []
            for member in team_members:
                user_id = member.get("userId")
                user_details = self.users_collection.find_one(
                    {"_id": user_id}, {"_id": 0, "fullName": 1, "email": 1, "phone": 1}
                )

                if user_details:
                    user_details["role"] = member.get("role", "member")
                    user_details["verified"] = (
                        True  # Mark as verified if in UsersToTeams
                    )
                    members_details.append(user_details)

            return {"teamId": team_id, "members": members_details}, 200

        except Exception as e:
            logger.error(f"Error retrieving team members: {e}", exc_info=True)
            return {"error": f"Failed to retrieve team members: {str(e)}"}, 500

    def get_teams_for_user(self, user_id):

        try:
            user_teams = list(
                self.users_to_teams_collection.find(
                    {"userId": user_id}, {"teamId": 1, "_id": 0}
                )
            )

            if not user_teams:
                return {"message": "User is not part of any team"}, 404

            team_ids = [team["teamId"] for team in user_teams]

            teams = list(
                self.teams_collection.find(
                    {"_id": {"$in": team_ids}}, {"_id": 1, "name": 1}
                )
            )

            return {"teams": teams}, 200

        except Exception as e:
            logger.error(
                f"Error retrieving teams for user {user_id}: {e}", exc_info=True
            )
            return {"error": f"Failed to retrieve teams: {str(e)}"}, 500

    def is_user_in_team(self, user_id, team_id):
        """Check if a user is already a member of a team."""
        try:
            existing_user_team = self.users_to_teams_collection.find_one(
                {"userId": user_id, "teamId": team_id}
            )
            return existing_user_team is not None
        except Exception as e:
            logger.error(f"Error checking if user is in team: {e}", exc_info=True)
            return False

    def get_all_team_members(self):
        try:
            team_members = list(self.users_to_teams_collection.find({}, {"_id": 0}))
            if not team_members:
                return {"message": "No members found"}, 404
            members_details = []
            for member in team_members:
                user_id = member.get("userId")
                user_details = self.users_collection.find_one(
                    {"_id": user_id}, {"_id": 0}
                )
                if user_details:
                    user_details["role"] = member.get("role", "member")
                    members_details.append(user_details)
            return {"members": members_details}, 200
        except Exception as e:
            logger.error(f"Error retrieving team members: {e}", exc_info=True)
            return {"error": f"Failed to retrieve team members: {str(e)}"}, 500
