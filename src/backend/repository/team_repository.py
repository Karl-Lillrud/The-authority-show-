import logging
import uuid
import json
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Optional, List
from backend.database.mongo_connection import collection
from backend.services.activity_service import ActivityService  # Add this import

logger = logging.getLogger(__name__)

# Define Pydantic model for Team
class Team(BaseModel):
    id: Optional[str] = Field(default=None)  # Removed alias="id"
    name: str
    description: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: Optional[datetime] = None
    members: Optional[List[dict]] = None

class TeamRepository:
    def __init__(self):
        self.collection = collection.database.Teams
        # Added for consistency if used
        self.user_to_teams_collection = collection.database.UsersToTeams
        self.podcasts_collection = collection.database.Podcasts
        self.users_collection = collection.database.Users
        self.activity_service = ActivityService()

    def add_team(self, user_id, user_email, data):
        try:
            # Validate data using Pydantic
            validated_data = Team(**data)

            team_id_str = str(uuid.uuid4())  # Ensure team_id is a string

            # Convert to dictionary for MongoDB insertion
            team_item = validated_data.dict(exclude_none=True)  # Use exclude_none=True
            team_item["id"] = team_id_str  # Explicitly set id

            # Ensure description is saved
            team_item["description"] = validated_data.description or ""
            team_item["phone"] = validated_data.phone or ""  # Assuming phone is part of Team model
            team_item["isActive"] = validated_data.isActive if hasattr(validated_data, 'isActive') else True
            team_item["joinedAt"] = datetime.now(timezone.utc)
            team_item["lastActive"] = datetime.now(timezone.utc)


            self.collection.insert_one(team_item)

            user_to_team_item = {
                "id": str(uuid.uuid4()),  # Ensure id is a string
                "userId": str(user_id),
                "teamId": team_id_str,  # Use the generated team_id_str
                "role": "creator",
                "assignedAt": datetime.now(timezone.utc),
            }

            self.user_to_teams_collection.insert_one(user_to_team_item)

            # --- Log activity for team created ---
            try:
                self.activity_service.log_activity(
                    user_id=str(user_id),
                    activity_type="team_created",
                    description=f"Created team '{team_item.get('name', '')}'",
                    details={"teamId": team_id_str, "teamName": team_item.get("name", "")},
                )
            except Exception as act_err:
                logger.error(
                    f"Failed to log team_created activity: {act_err}", exc_info=True
                )
            # --- End activity log ---

            # Ensure members list exists before appending
            if "members" not in team_item or team_item["members"] is None:
                team_item["members"] = []
            
            team_item["members"].append(
                {"userId": str(user_id), "email": user_email, "role": "creator"}
            )

            self.collection.update_one(
                {"id": team_id_str}, {"$set": {"members": team_item["members"]}}
            )

            # Send invitation emails to new members (excluding the team creator)
            from backend.services.TeamInviteService import (
                TeamInviteService,
            )  # Import the service

            invite_service = TeamInviteService()
            for member_data in team_item["members"]: # Renamed member to member_data
                if member_data.get("role") != "creator":
                    try:
                        response, status_code = invite_service.send_invite(
                            user_id, team_id_str, member_data["email"] # Use member_data
                        )
                        logger.info(f"Invitation email sent to {member_data['email']}") # Use member_data
                    except Exception as e:
                        logger.error(
                            f"Error sending invitation email to {member_data['email']}: {e}" # Use member_data
                        )

            return {
                "message": "Team and creator added successfully",
                "team_id": team_id_str,
                "redirect_url": "/team.html",
            }, 201

        except ValidationError as err: # Assuming Pydantic's ValidationError
            return {"error": "Invalid data", "details": err.errors()}, 400
        except Exception as e:
            logger.error(f"Error adding team: {e}", exc_info=True)
            return {"error": f"Failed to add team: {str(e)}"}, 500

    def get_teams(self, user_id):
        try:
            # Assuming 'createdBy' field exists and stores user_id
            created_teams = list(
                self.collection.find({"createdBy": user_id}, {"created_at": 0})
            )

            user_team_links = list(
                self.user_to_teams_collection.find(
                    {"userId": user_id}, {"teamId": 1, "id": 0} # Changed _id to id
                )
            )
            joined_team_ids = [ut["teamId"] for ut in user_team_links]

            joined_teams_data = list( # Renamed joined_teams to joined_teams_data
                self.collection.find(
                    {"id": {"$in": joined_team_ids}}, {"created_at": 0} # Changed _id to id
                )
            )

            # Combine and deduplicate teams
            teams_dict = {str(team["id"]): team for team in created_teams + joined_teams_data} # Changed _id to id

            for team_obj in teams_dict.values(): # Renamed team to team_obj
                team_obj["id"] = str(team_obj["id"]) # Changed _id to id
                podcasts = list(self.podcasts_collection.find({"teamId": team_obj["id"]})) # Changed _id to id
                team_obj["podNames"] = (
                    ", ".join([p.get("podName", "N/A") for p in podcasts])
                    if podcasts
                    else "N/A"
                )
                for member_data in team_obj.get("members", []): # Renamed member to member_data
                    if member_data.get("role") != "creator" and not member_data.get(
                        "verified", False
                    ):
                        user = self.users_collection.find_one(
                            {"email": member_data["email"].lower()}
                        )
                        if user and user.get("isTeamMember") is True:
                            member_data["verified"] = True

            return list(teams_dict.values()), 200

        except Exception as e:
            logger.error(f"Error retrieving teams: {e}", exc_info=True)
            return {"error": f"Failed to retrieve teams: {str(e)}"}, 500

    def delete_team(self, team_id):
        try:
            team_to_delete = self.collection.find_one({"id": team_id}) # Renamed team to team_to_delete, _id to id
            if not team_to_delete:
                return {"error": "Team not found"}, 404

            team_name = team_to_delete.get("name", "Unknown Team")
            creator_id = None
            for member_data in team_to_delete.get("members", []): # Renamed member to member_data
                if member_data.get("role") == "creator":
                    creator_id = member_data.get("userId")
                    break

            self.user_to_teams_collection.delete_many({"teamId": team_id})
            result = self.collection.delete_one({"id": team_id}) # Changed _id to id
            if result.deleted_count == 0:
                return {"error": "Failed to delete the team"}, 500

            update_result = self.podcasts_collection.update_many(
                {"teamId": team_id}, {"$set": {"teamId": None}}
            )
            for member_data in team_to_delete.get("members", []): # Renamed member to member_data
                if (
                    member_data.get("role") != "creator"
                    and member_data.get("verified", False)
                    and member_data.get("userId")
                ):
                    self.users_collection.delete_one({"id": member_data["userId"]}) # Changed _id to id

            if creator_id:
                try:
                    self.activity_service.log_activity(
                        user_id=str(creator_id),
                        activity_type="team_deleted",
                        description=f"Deleted team '{team_name}'",
                        details={"teamId": team_id, "teamName": team_name},
                    )
                except Exception as act_err:
                    logger.error(
                        f"Failed to log team_deleted activity: {act_err}", exc_info=True
                    )

            return {
                "message": f"Team '{team_name}' and all members deleted successfully!",
            }, 200

        except Exception as e:
            logger.error(f"Error deleting team: {e}", exc_info=True)
            return {"error": f"Failed to delete team: {str(e)}"}, 500

    def edit_team(self, team_id, data):
        try:
            team_to_edit = self.collection.find_one({"id": team_id}) # Renamed team to team_to_edit, _id to id
            if not team_to_edit:
                return {"error": "Team not found"}, 404

            # Assuming Team is a Pydantic model
            validated_data = Team(**data).dict(exclude_unset=True)


            update_fields = {}
            for key, new_value in validated_data.items():
                current_value = team_to_edit.get(key)
                # Simplified comparison, may need adjustment for complex types
                if current_value != new_value:
                    update_fields[key] = new_value
                    logger.debug(
                        f"[edit_team] Field '{key}' changed: OLD={current_value}, NEW={new_value}"
                    )
            
            update_fields["updatedAt"] = datetime.now(timezone.utc)


            logger.debug(f"[edit_team] Final update fields: {update_fields}")

            if update_fields:
                result = self.collection.update_one(
                    {"id": team_id}, {"$set": update_fields} # Changed _id to id
                )
                return {"message": "Team updated successfully!"}, 200
            else:
                return {"message": "No changes made to the team."}, 200

        except ValidationError as err: # Assuming Pydantic's ValidationError
            return {"error": "Invalid data", "details": err.errors()}, 400
        except Exception as e:
            logger.error(f"Error editing team: {e}", exc_info=True)
            return {"error": f"Failed to edit team: {str(e)}"}, 500

    def add_member_to_team(self, team_id, new_member_data): # Renamed new_member to new_member_data
        try:
            new_member_data["email"] = new_member_data["email"].strip().lower()
            new_member_data["verified"] = False

            existing_member_check = self.collection.find_one( # Renamed existing_member to existing_member_check
                {"id": team_id, "members.email": new_member_data["email"]} # Changed _id to id
            )
            if existing_member_check:
                for member_item in existing_member_check.get("members", []): # Renamed member to member_item
                    if member_item["email"] == new_member_data["email"]:
                        return {"error": "Member already exists in the team"}, 400

            result = self.collection.update_one(
                {"id": team_id}, {"$push": {"members": new_member_data}} # Changed _id to id
            )
            if result.modified_count > 0:
                return {"message": "Member added successfully"}, 201
            else:
                return {"error": "Failed to add member"}, 500

        except Exception as e:
            logger.error(f"Error adding member to team: {e}", exc_info=True)
            return {"error": f"Failed to add member: {str(e)}"}, 500

    def remove_member_or_delete_team(
        self, team_id: str, user_id: str, return_message_only=False
    ):
        try:
            team_data_obj = self.collection.find_one({"id": team_id}) # Renamed team to team_data_obj, _id to id
            if not team_data_obj:
                msg = {"error": f"Team {team_id} not found"}
                return msg if return_message_only else (msg, 404)

            is_creator = any(
                member_item.get("userId") == user_id and member_item.get("role") == "creator" # Renamed member to member_item
                for member_item in team_data_obj.get("members", []) # Renamed member to member_item
            )

            if is_creator:
                self.user_to_teams_collection.delete_many({"teamId": team_id})
                self.collection.delete_one({"id": team_id}) # Changed _id to id

                msg = {"message": f"Team {team_id} deleted by creator {user_id}"}
                return msg if return_message_only else (msg, 200)

            else:
                self.collection.update_one(
                    {"id": team_id}, {"$pull": {"members": {"userId": user_id}}} # Changed _id to id
                )
                self.user_to_teams_collection.delete_many(
                    {"teamId": team_id, "userId": user_id}
                )

                msg = {"message": f"User {user_id} removed from team {team_id}"}
                return msg if return_message_only else (msg, 200)

        except Exception as e:
            logger.error(f"Error removing user or deleting team: {e}", exc_info=True)
            msg = {"error": f"Failed to update team: {str(e)}"}
            return msg if return_message_only else (msg, 500)

    def edit_team_member_by_email(self, team_id, email, new_role):
        try:
            result = self.collection.update_one(
                {"id": team_id, "members.email": email}, # Changed _id to id
                {"$set": {"members.$.role": new_role}},
            )
            if result.modified_count > 0:
                return {"message": "Member role updated successfully!"}, 200
            else:
                return {"error": "No matching member found or role unchanged."}, 400
        except Exception as e:
            logger.error(f"Error editing member by email: {e}", exc_info=True)
            return {"error": f"Failed to edit member: {str(e)}"}, 500
