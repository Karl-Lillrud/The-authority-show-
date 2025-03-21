import logging
import uuid
from datetime import datetime, timezone
from marshmallow import ValidationError
from backend.database.mongo_connection import collection
from backend.models.teams import TeamSchema

logger = logging.getLogger(__name__)


class TeamRepository:
    def __init__(self):
        self.teams_collection = collection.database.Teams
        self.user_to_teams_collection = collection.database.UsersToTeams
        self.podcasts_collection = collection.database.Podcasts

    def add_team(self, user_id, user_email, data):
        try:
            team_schema = TeamSchema()
            validated_data = team_schema.load(data)

            team_id = str(uuid.uuid4())  # Ensure team_id is a string

            team_item = {
                "_id": team_id,
                "name": validated_data.get("name", "").strip(),
                "email": validated_data.get("email", "").strip(),
                "description": validated_data.get(
                    "description", ""
                ).strip(),  # Ensure description is saved
                "phone": validated_data.get("phone", "").strip(),
                "isActive": validated_data.get("isActive", True),
                "joinedAt": datetime.now(timezone.utc),
                "lastActive": datetime.now(timezone.utc),
                "members": validated_data.get("members", []),
            }

            self.teams_collection.insert_one(team_item)

            # ✅ Explicitly set `_id` as a string UUID for `user_to_teams_collection`
            user_to_team_item = {
                "_id": str(uuid.uuid4()),  # Ensure _id is a string
                "userId": str(user_id),
                "teamId": team_id,
                "role": "creator",
                "assignedAt": datetime.now(timezone.utc),
            }

            self.user_to_teams_collection.insert_one(user_to_team_item)

            team_item["members"].append(
                {"userId": str(user_id), "email": user_email, "role": "creator"}
            )

            self.teams_collection.update_one(
                {"_id": team_id}, {"$set": {"members": team_item["members"]}}
            )

            return {
                "message": "Team and creator added successfully",
                "team_id": team_id,
                "redirect_url": "/team.html",
            }, 201

        except ValidationError as err:
            return {"error": "Invalid data", "details": err.messages}, 400
        except Exception as e:
            logger.error(f"Error adding team: {e}", exc_info=True)
            return {"error": f"Failed to add team: {str(e)}"}, 500

    def get_teams(self, user_id):
        try:
            created_teams = list(
                self.teams_collection.find({"createdBy": user_id}, {"created_at": 0})
            )

            user_team_links = list(
                self.user_to_teams_collection.find(
                    {"userId": user_id}, {"teamId": 1, "_id": 0}
                )
            )
            joined_team_ids = [ut["teamId"] for ut in user_team_links]

            joined_teams = list(
                self.teams_collection.find(
                    {"_id": {"$in": joined_team_ids}}, {"created_at": 0}
                )
            )

            teams = {str(team["_id"]): team for team in created_teams + joined_teams}
            for team in teams.values():
                team["_id"] = str(team["_id"])
                podcasts = list(self.podcasts_collection.find({"teamId": team["_id"]}))
                team["podNames"] = (
                    ", ".join([p.get("podName", "N/A") for p in podcasts])
                    if podcasts
                    else "N/A"
                )

            return list(teams.values()), 200

        except Exception as e:
            logger.error(f"Error retrieving teams: {e}", exc_info=True)
            return {"error": f"Failed to retrieve teams: {str(e)}"}, 500

    def delete_team(self, team_id):
        try:
            team = self.teams_collection.find_one({"_id": team_id})
            if not team:
                return {"error": "Team not found"}, 404

            self.user_to_teams_collection.delete_many({"teamId": team_id})

            result = self.teams_collection.delete_one({"_id": team_id})
            if result.deleted_count == 0:
                return {"error": "Failed to delete the team"}, 500

            update_result = self.podcasts_collection.update_many(
                {"teamId": team_id}, {"$set": {"teamId": None}}
            )

            return {
                "message": f"Team {team_id} and all members deleted successfully!",
            }, 200

        except Exception as e:
            logger.error(f"Error deleting team: {e}", exc_info=True)
            return {"error": f"Failed to delete team: {str(e)}"}, 500

    def edit_team(self, team_id, data):
        try:
            team = self.teams_collection.find_one({"_id": team_id})
            if not team:
                return {"error": "Team not found"}, 404

            team_schema = TeamSchema()
            validated_data = team_schema.load(data, partial=True)

            update_fields = {
                k: v.strip() if isinstance(v, str) else v
                for k, v in validated_data.items()
            }

            if update_fields:
                result = self.teams_collection.update_one(
                    {"_id": team_id}, {"$set": update_fields}
                )
                if result.modified_count > 0:
                    return {"message": "Team updated successfully!"}, 200
                else:
                    return {"message": "No changes made to the team."}, 200
            else:
                return {"message": "No valid fields provided for update."}, 400

        except ValidationError as err:
            return {"error": "Invalid data", "details": err.messages}, 400
        except Exception as e:
            logger.error(f"Error editing team: {e}", exc_info=True)
            return {"error": f"Failed to edit team: {str(e)}"}, 500
