# account_service.py
import logging
from backend.database.mongo_connection import collection

logger = logging.getLogger(__name__)

class AccountService:
    def __init__(self):
        self.account_collection = collection.database.Accounts
        self.team_service = None  # Will be set after initialization to avoid circular import
    
    def set_team_service(self, team_service):
        """Set the team service to avoid circular dependency."""
        self.team_service = team_service
    
    def get_user_account(self, user_id):
        """Get personal account for a user."""
        return self.account_collection.find_one({"userId": user_id})
    
    def get_account_by_user_id(self, user_id):
        """Get account by user ID."""
        account = self.account_collection.find_one({"userId": user_id})
        if account:
            logger.info(f"🔹 Found account for user: {account['_id']}")
            return account
        else:
            logger.warning(f"⚠️ No account found for user with ID: {user_id}")
            return None
    
    def determine_active_account(self, user_id, user_account, team_list):
        """Determine which account to use - personal or team."""
        # If user has personal account, use it
        if user_account:
            return user_account
        
        # If no personal account but user is in teams, try to use team account
        if not team_list:
            return None
            
        first_team = team_list[0]
        team_id = first_team.get("_id")
        logger.info(f"🔹 First team details: {first_team}")
        logger.info(f"🔹 Team ID: {team_id}")
        
        # Try to find team owner's account first
        owner_id = self.team_service.find_team_owner(team_id)
        if owner_id:
            owner_account = self.get_account_by_user_id(owner_id)
            if owner_account:
                return owner_account
        
        # Fallback: try to find any team member's account
        member_id = self.team_service.find_any_team_member(team_id)
        if member_id and member_id != user_id:  # Avoid finding the same user
            return self.get_account_by_user_id(member_id)
        
        return None
