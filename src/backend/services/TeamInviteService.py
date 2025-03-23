from datetime import datetime, timedelta, timezone
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
            from backend.utils.email_utils import send_team_invite_email  # Import inside function
            
            # Normalize email
            email = email.lower().strip()

            # Check if user is already a team member
            existing_user = self.user_repo.get_user_by_email(email)
            if existing_user:
                is_member = self.user_to_team_repo.is_user_in_team(
                    existing_user["_id"], team_id
                )
                if is_member:
                    return {"error": "User is already a member of this team"}, 400

            # Save invite to database
            invite_token = self.invite_repo.save_invite(team_id, email, inviter_id)

            # Get inviter details for the email
            inviter = self.user_repo.get_user_by_id(inviter_id)
            inviter_name = (
                inviter.get("fullName", "A team member") if inviter else "A team member"
            )

            # Get team details
            invite = self.invite_repo.get_invite(invite_token)
            team_name = invite.get("teamName", "the team")

            # Call send_team_invite_email
            send_team_invite_email(email, invite_token, team_name, inviter_name)

            logger.info(f"✅ Team invite sent to {email} for team {team_id}")
            return {
                "message": "Invite sent successfully",
                "inviteToken": invite_token,
                "email": email,
            }, 201

        except ValueError as ve:
            logger.error(f"❌ Validation error sending invite: {ve}")
            return {"error": str(ve)}, 400
        except Exception as e:
            logger.error(f"❌ Error sending invite: {e}", exc_info=True)
            return {"error": f"Failed to send invite: {str(e)}"}, 500

    def process_registration(self, user_id, email, invite_token):
        """Processes user registration with an invite token."""
        try:
            # Fetch the invite
            invite = self.invite_repo.get_invite(invite_token)

            if not invite or invite.get("status") != "pending":
                return {"error": "Invalid or expired invite token."}, 400

            # Verify email matches invite
            if invite["email"].lower() != email.lower():
                return {"error": "Email does not match the invite."}, 400

            team_id = invite["teamId"]

            # Add user to the team
            add_result, status_code = self.user_to_team_repo.add_user_to_team(
                {"userId": user_id, "teamId": team_id, "role": "member"}
            )

            if status_code != 201:
                return {"error": "Failed to add user to team."}, 500

            # Mark invite as accepted
            result, success = self.invite_repo.mark_invite_accepted(invite_token)
            if not success:
                return {"error": "Failed to accept invite."}, 500

            return {
                "message": "User successfully linked to team.",
                "teamId": team_id,
            }, 201

        except Exception as e:
            logger.error(f"Error in process_registration: {str(e)}", exc_info=True)
            return {"error": f"Error processing registration: {str(e)}"}, 500
    
    def accept_invite(self, invite_token, user_id):
        """Accepts a team invitation."""
        try:
            # Fetch the invite
            invite = self.invite_repo.get_invite(invite_token)
            
            if not invite:
                logger.warning(f"Invite {invite_token} not found")
                return {"error": "Invite not found"}, 404
                
            # Ensure the invite is still valid
            if invite["status"] == "expired":
                logger.warning(f"Invite {invite_token} has expired")
                return {"error": "This invite has expired."}, 400
                
            # Check expiration date if available
            expires_at = invite.get("expiresAt")
            if expires_at:
                if isinstance(expires_at, str):
                    try:
                        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    except ValueError:
                        logger.error(f"Invalid datetime format for invite {invite_token}")
                        return {"error": "Invalid invite expiration format"}, 500
                        
                if expires_at < datetime.now(timezone.utc):
                    logger.warning(f"Invite {invite_token} has expired")
                    return {"error": "This invite has expired."}, 400

            if invite["status"] == "accepted":
                logger.info(f"Invite {invite_token} was already accepted")
                return {"message": "Invite already accepted."}, 200

            # Check if the user is already in the team
            is_member = self.user_to_team_repo.is_user_in_team(user_id, invite["teamId"])
            if is_member:
                logger.warning(f"User {user_id} is already in team {invite['teamId']}")
                return {"error": "User is already in the team"}, 400

            # Add user to the team
            add_result, status_code = self.user_to_team_repo.add_user_to_team({
                "userId": user_id,
                "teamId": invite["teamId"],
                "role": "member"
            })

            if status_code != 201:
                return {"error": "Failed to add user to team."}, 500
                
            # Delete the invite instead of marking as accepted
            result = self.invite_repo.invites_collection.delete_one({"_id": invite_token})
            
            if result.deleted_count == 1:
                logger.info(f"Invite {invite_token} was accepted and removed from the database")
                return {"message": "Invite accepted successfully and removed"}, 200
            else:
                logger.warning(f"Failed to delete invite {invite_token} after acceptance")
                return {"error": "Failed to complete invite acceptance"}, 500

        except Exception as e:
            logger.error(f"Error accepting invite: {str(e)}", exc_info=True)
            return {"error": f"Error accepting invite: {str(e)}"}, 500