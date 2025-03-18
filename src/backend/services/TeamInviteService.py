import logging
from backend.repository.teaminvitrepository import TeamInviteRepository
from backend.repository.usertoteam_repository import UserToTeamRepository
from backend.repository.user_repository import UserRepository

logger = logging.getLogger(__name__)

class TeamInviteService:
    def __init__(self):
        self.invite_repo = TeamInviteRepository()
        self.user_to_team_repo = UserToTeamRepository()
        self.user_repo = UserRepository()

    def send_invite(self, inviter_id, team_id, email):
        """Handles sending a team invite and email notification."""
        try:
            from backend.utils.email_utils import send_team_invite_email  # ✅ Import inside function
            
            # Normalize email
            email = email.lower().strip()

            # Check if user is already a team member
            existing_user = self.user_repo.get_user_by_email(email)
            if existing_user:
                is_member = self.user_to_team_repo.is_user_in_team(existing_user["_id"], team_id)
                if is_member:
                    return {"error": "User is already a member of this team"}, 400

            # Save invite to database
            invite_token = self.invite_repo.save_invite(team_id, email, inviter_id)

            # Get inviter details for the email
            inviter = self.user_repo.get_user_by_id(inviter_id)
            inviter_name = inviter.get("fullName", "A team member") if inviter else "A team member"

            # Get team details
            invite = self.invite_repo.get_invite(invite_token)
            team_name = invite.get("teamName", "the team")

            # ✅ Call send_team_invite_email
            send_team_invite_email(email, invite_token, team_name, inviter_name)

            logger.info(f"✅ Team invite sent to {email} for team {team_id}")
            return {
                "message": "Invite sent successfully",
                "inviteToken": invite_token,
                "email": email
            }, 201

        except ValueError as ve:
            logger.error(f"❌ Validation error sending invite: {ve}")
            return {"error": str(ve)}, 400
        except Exception as e:
            logger.error(f"❌ Error sending invite: {e}", exc_info=True)
            return {"error": f"Failed to send invite: {str(e)}"}, 500
