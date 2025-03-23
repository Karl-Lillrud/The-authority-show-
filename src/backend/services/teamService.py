# team_service.py
import logging
from backend.database.mongo_connection import collection
from backend.repository.usertoteam_repository import UserToTeamRepository

logger = logging.getLogger(__name__)

class TeamService:
    def __init__(self):
        self.teams_collection = collection.database.Teams
        self.users_to_teams_collection = collection.database.UsersToTeams
        self.user_to_team_repo = UserToTeamRepository()
    
    def get_user_teams(self, user_id):
        """Get teams that the user is a member of."""
        team_membership, status_code = self.user_to_team_repo.get_teams_for_user(user_id)
        teams = team_membership.get("teams", []) if status_code == 200 else []
        logger.info(f"✅ User is part of teams: {teams}")
        return teams
    
    def find_team_owner(self, team_id):
        """Find the owner of a team."""
        team_owner_mapping = self.users_to_teams_collection.find_one(
            {"teamId": team_id, "role": "creator"},
            {"userId": 1}
        )
        
        if not team_owner_mapping:
            logger.warning(f"⚠️ No creator found for team ID: {team_id}")
            return None
            
        owner_id = team_owner_mapping.get("userId")
        logger.info(f"🔹 Found team owner ID: {owner_id}")
        return owner_id
    
    def find_any_team_member(self, team_id):
        """Find any member of a team."""
        any_team_member = self.users_to_teams_collection.find_one(
            {"teamId": team_id},
            {"userId": 1}
        )
        
        if not any_team_member:
            return None
            
        member_id = any_team_member.get("userId")
        logger.info(f"🔹 Found team member ID: {member_id}")
        return member_id
