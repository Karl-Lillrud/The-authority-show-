from backend.utils.email_utils import send_email, send_team_invite_email
from backend.repository.teaminviterepository import TeamInviteRepository
from backend.repository.user_repository import UserRepository
from flask import render_template
import logging

logger = logging.getLogger(__name__)


class InvitationService:
    def __init__(self):
        self.team_invite_repo = TeamInviteRepository()
        self.user_repo = UserRepository()

    def send_invitation(
        self, invitation_type, email, inviter_id=None, team_id=None, role=None
    ):
        """
        Handles sending different types of invitations.
        :param invitation_type: Type of invitation (e.g., 'guest', 'registration', 'team', 'beta').
        :param email: Recipient's email address.
        :param inviter_id: ID of the user sending the invitation (optional).
        :param team_id: ID of the team (optional, for team invitations).
        :param role: Role for the invitee (optional, for team invitations).
        :return: A dictionary with the result and status code.
        """
        try:
            if not email:
                raise ValueError("Email is required for sending an invitation.")

            email = email.lower().strip()

            # Validate invitation type
            valid_invitation_types = {"team", "guest", "registration", "beta"}
            if invitation_type not in valid_invitation_types:
                raise ValueError(f"Invalid invitation type: {invitation_type}")

            if invitation_type == "team":
                if not inviter_id or not team_id or not role:
                    raise ValueError("Missing required parameters for team invitation.")

                # Save the invite to the database
                invite_token = self.team_invite_repo.save_invite(
                    team_id, email, inviter_id, role
                )

                # Fetch team and inviter details
                team = self.team_invite_repo.teams_collection.find_one({"_id": team_id})
                inviter = self.user_repo.get_user_by_id(inviter_id)
                team_name = team.get("name", "Unnamed Team")
                inviter_name = (
                    inviter.get("fullName", "A team member")
                    if inviter
                    else "A team member"
                )

                # Send the team invitation email
                send_team_invite_email(
                    email, invite_token, team_name, inviter_name, role
                )
                logger.info(f"Team invitation sent to {email} for team {team_id}")
                return {
                    "message": "Team invitation sent successfully",
                    "inviteToken": invite_token,
                }, 201

            elif invitation_type == "guest":
                # Send a guest invitation email
                body = render_template("beta-email/guest-invite.html")
                send_email(email, "You're Invited as a Guest", body)
                logger.info(f"Guest invitation sent to {email}")
                return {"message": "Guest invitation sent successfully"}, 200

            elif invitation_type == "registration":
                # Send a registration invitation email
                body = render_template("beta-email/registration-invite.html")
                send_email(email, "Welcome to PodManager", body)
                logger.info(f"Registration invitation sent to {email}")
                return {"message": "Registration invitation sent successfully"}, 200

            elif invitation_type == "beta":
                # Send a beta invitation email
                body = render_template("beta-email/podmanager-beta-invite.html")
                send_email(email, "Invitation to PodManager Beta", body)
                logger.info(f"Beta invitation sent to {email}")
                return {"message": "Beta invitation sent successfully"}, 200

        except Exception as e:
            logger.error(
                f"Error sending {invitation_type} invitation: {e}", exc_info=True
            )
            return {
                "error": f"Failed to send {invitation_type} invitation: {str(e)}"
            }, 500

    def get_user_email(self, user_id):
        """
        Fetches the email address for a given user ID.
        """
        try:
            user = self.user_repo.get_user_by_id(user_id)
            if not user or not user.get("email"):
                raise ValueError("No email found for the user.")
            return user["email"]
        except Exception as e:
            logger.error(f"Error fetching email for user {user_id}: {e}")
            raise ValueError("Failed to fetch user email.")
