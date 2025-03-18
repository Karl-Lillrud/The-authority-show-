import logging
import uuid
from datetime import datetime, timedelta, timezone
from backend.database.mongo_connection import collection

logger = logging.getLogger(__name__)

class TeamInviteRepository:
    def __init__(self):
        self.invites_collection = collection.database.Invites
        self.teams_collection = collection.database.Teams
        self.users_collection = collection.database.Users
        self.accounts_collection = collection.database.Accounts

    def save_invite(self, team_id, email, inviter_id):
        """
        Creates and stores an invite in the database.
        
        Args:
            team_id (str): ID of the team to invite to
            email (str): Email of the invitee
            inviter_id (str): ID of the user sending the invite
            
        Returns:
            str: Generated invite token
        """
        # Check if team exists
        team = self.teams_collection.find_one({"_id": team_id})
        if not team:
            logger.error(f"Team with ID {team_id} not found")
            raise ValueError(f"Team with ID {team_id} not found")
            
        # Check if user has permission to invite
        inviter_account = self.accounts_collection.find_one({"userId": inviter_id})
        if not inviter_account:
            logger.error(f"No account found for user {inviter_id}")
            raise ValueError("User not authorized to send invites")
            
        # Check if an active invite already exists for this email and team
        existing_invite = self.invites_collection.find_one({
            "teamId": team_id,
            "email": email.lower().strip(),
            "status": "pending",
            "createdAt": {"$gt": datetime.now(timezone.utc) - timedelta(days=7)}  # Within last 7 days
        })
        
        if existing_invite:
            logger.info(f"Found existing active invite for {email} to team {team_id}")
            return existing_invite["_id"]
            
        # Generate invite token
        invite_token = str(uuid.uuid4())
        
        # Create invite document
        invite_data = {
            "_id": invite_token,
            "teamId": team_id,
            "teamName": team.get("name", "Team"),  # Include team name for email
            "email": email.lower().strip(),  # Store email in lowercase
            "inviterId": inviter_id,
            "createdAt": datetime.now(timezone.utc),
            "expiresAt": (datetime.now(timezone.utc) + timedelta(days=7)),  # Expire after 7 days
            "status": "pending",
        }
        
        # Insert invite into database
        self.invites_collection.insert_one(invite_data)
        logger.info(f"Created new invite {invite_token} for {email} to team {team_id}")
        
        return invite_token

    def get_invite(self, invite_token):
        """
        Retrieves an invite by token and checks if it's still valid.
        
        Args:
            invite_token (str): The invite token to look up
            
        Returns:
            dict or None: The invite document if found, None otherwise
        """
        invite = self.invites_collection.find_one({"_id": invite_token})

        if invite and invite.get("status") == "pending":
            expires_at = invite.get("expiresAt")

            # ✅ Ensure expires_at is timezone-aware
            if isinstance(expires_at, str):
                try:
                    expires_at = datetime.fromisoformat(expires_at).replace(tzinfo=timezone.utc)
                except ValueError:
                    logger.error(f"Invalid datetime format in expiresAt for invite {invite_token}")
                    return None
            
            elif isinstance(expires_at, datetime) and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)  # Convert naive datetime to UTC
            
            # ✅ Compare with current UTC time safely
            if expires_at and expires_at < datetime.now(timezone.utc):
                # Auto-expire the invite
                self.invites_collection.update_one(
                    {"_id": invite_token},
                    {"$set": {"status": "expired"}}
                )
                invite["status"] = "expired"
                logger.info(f"Invite {invite_token} has expired")
                
        return invite

    def mark_invite_accepted(self, invite_token):
        """
        Marks an invite as accepted after successful registration.
        
        Args:
            invite_token (str): The invite token to update
            
        Returns:
            bool: True if the update was successful, False otherwise
        """
        result = self.invites_collection.update_one(
            {"_id": invite_token},
            {"$set": {
                "status": "accepted", 
                "acceptedAt": datetime.now(timezone.utc)
            }}
        )
        
        success = result.modified_count == 1
        if success:
            logger.info(f"Invite {invite_token} marked as accepted")
        else:
            logger.warning(f"Failed to mark invite {invite_token} as accepted")
            
        return success
            
    def get_pending_invites_by_team(self, team_id):
        """
        Gets all pending invites for a team.
        
        Args:
            team_id (str): ID of the team
            
        Returns:
            list: List of pending invite documents
        """
        return list(self.invites_collection.find({
            "teamId": team_id,
            "status": "pending",
            "expiresAt": {"$gt": datetime.now(timezone.utc)}
        }))

    def cancel_invite(self, invite_token, user_id):
        """
        Cancels a pending invite.
        
        Args:
            invite_token (str): The invite token to cancel
            user_id (str): ID of the user attempting to cancel
            
        Returns:
            tuple: (success message dict, status code)
        """
        invite = self.get_invite(invite_token)

        if not invite:
            return {"error": "Invite not found"}, 404
            
        # Check permission - only the inviter or team admin can cancel
        if invite["inviterId"] != user_id:
            # Check if user is team admin
            team_member = self.teams_collection.find_one({
                "_id": invite["teamId"],
                "members": {"$elemMatch": {"userId": user_id, "role": "admin"}}
            })
            
            if not team_member:
                return {"error": "Permission denied"}, 403
        
        result = self.invites_collection.update_one(
            {"_id": invite_token, "status": "pending"},
            {"$set": {"status": "cancelled"}}
        )
        
        if result.modified_count == 1:
            return {"message": "Invite cancelled successfully"}, 200
        else:
            return {"error": "Failed to cancel invite"}, 400
