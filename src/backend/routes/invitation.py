from flask import Blueprint, request, jsonify, render_template, url_for, g
from backend.utils.email_utils import send_email, send_team_invite_email
from backend.database.mongo_connection import collection
from backend.models.podcasts import PodcastSchema
from backend.services.TeamInviteService import TeamInviteService
from datetime import datetime, timezone
import uuid
import logging

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Create the blueprint
invitation_bp = Blueprint("invitation_bp", __name__)

# Initialize the service once
invite_service = TeamInviteService()


@invitation_bp.route("/send_invitation", methods=["POST"])
def send_invitation():
    """Send a beta invitation email to the logged-in user."""
    try:
        logger.info("Received send_invitation request")
        if not hasattr(g, "user_id") or not g.user_id:
            return jsonify({"error": "Unauthorized"}), 401

        # Fetch the account document from MongoDB for the logged-in user
        user_account = collection.database.Accounts.find_one({"userId": g.user_id})
        if not user_account:
            logger.error("No account associated with this user")
            return jsonify({"error": "No account associated with this user"}), 403

        # Fetch the account ID that the user already has (do not override with a new one)
        if "id" in user_account:
            account_id = user_account["id"]
        else:
            account_id = str(user_account["_id"])
        logger.info(f"Found account {account_id} for user {g.user_id}")

        # Send the invitation email
        body = render_template("beta-email/podmanager-beta-invite.html")
        send_email(user_account["email"], "Invitation to PodManager Beta", body)
        logger.info("Invitation email sent successfully")
        return (
            jsonify({"success": True, "message": "Invitation email sent successfully"}),
            201,
        )

    except Exception as e:
        logger.error(f"Failed to send invitation email: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"Failed to send invitation email: {str(e)}",
                }
            ),
            500,
        )


@invitation_bp.route("/invite_email_body", methods=["GET"])
def invite_email_body():
    """Returns the HTML template for the beta invitation email."""
    return render_template("beta-email/podmanager-beta-invite.html")


@invitation_bp.route("/send_team_invite", methods=["POST"])
def send_team_invite():
    """Sends an invitation email to join a team."""
    logger.info("Received /send_team_invite request")  # Debug log

    if not hasattr(g, "user_id") or not g.user_id:
        logger.error("Unauthorized access: Missing user_id")  # Debug log
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    logger.info("Request data: %s", data)  # Debug log

    email = data.get("email")
    team_id = data.get("teamId")
    role = data.get("role")

    if not email or not team_id or not role:
        logger.error("Validation failed: Missing email, teamId, or role")  # Debug log
        return jsonify({"error": "Missing email, teamId, or role"}), 400

    try:
        logger.info(
            "Creating invite for email: %s, teamId: %s, role: %s", email, team_id, role
        )  # Debug log
        result = invite_service.send_invite(
            g.user_id, team_id, email, role=role
        )  # Pass role to the invite service
        logger.info("Invite service result: %s", result)  # Debug log

        if isinstance(result, dict) and "inviteToken" in result:
            invite_token = result["inviteToken"]
        else:
            logger.error("Failed to generate invite token")  # Debug log
            return jsonify({"error": "Failed to generate invite token"}), 500

        team = collection.database.Teams.find_one({"_id": team_id})
        logger.info("Fetched team details: %s", team)  # Debug log
        team_name = team.get("teamName", "Unnamed Team")

        user = collection.database.Users.find_one({"_id": g.user_id})
        inviter_name = user.get("fullName") if user else None
        logger.info("Inviter name: %s", inviter_name)  # Debug log

        # Ensure the correct role is included in the registration URL
        registration_url = (
            f"http://127.0.0.1:8000/register_team_member?token={invite_token}"
            f"&teamName={team_name}&role={role}&email={email}"
        )
        logger.info("Generated registration URL: %s", registration_url)  # Debug log

        email_result = send_team_invite_email(
            email=email,
            invite_token=invite_token,
            team_name=team_name,
            inviter_name=inviter_name,
            role=role,  # Pass the correct role to the email template
        )
        logger.info("Email send result: %s", email_result)  # Debug log

        if "error" in email_result:
            logger.warning("Email sending issue: %s", email_result["error"])

        return (
            jsonify(
                {
                    "success": True,
                    "inviteId": invite_token,
                    "registrationUrl": registration_url,
                }
            ),
            201,
        )

    except ValueError as e:
        logger.error("ValueError: %s", e)  # Debug log
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Error in /send_team_invite: %s", e)  # Debug log
        return jsonify({"error": "Failed to send invite"}), 500


@invitation_bp.route("/verify_invite/<invite_token>", methods=["GET"])
def verify_invite(invite_token):
    """Verifies if an invite token is valid without accepting it."""
    try:
        invite_info = invite_service.get_invite_info(invite_token)
        if not invite_info:
            return jsonify({"error": "Invite not found"}), 404

        # Check if invite is still valid
        if invite_info.get("status") != "pending":
            return jsonify({"error": f"Invite is {invite_info.get('status')}"}), 400

        # Check if invite is expired
        expires_at = invite_info.get("expiresAt")
        if expires_at and expires_at < datetime.now(timezone.utc):
            return jsonify({"error": "Invite has expired"}), 400

        return (
            jsonify(
                {
                    "teamId": invite_info.get("teamId"),
                    "teamName": invite_info.get("teamName"),
                    "email": invite_info.get("email"),
                    "status": "valid",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error verifying invite: {e}")
        return jsonify({"error": "Failed to verify invite"}), 500


@invitation_bp.route("/accept_invite/<invite_token>", methods=["POST"])
def accept_invite(invite_token):
    """Accepts a team invitation and removes it after successful registration."""
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        result, success = invite_service.accept_invite(invite_token, g.user_id)
        if success:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error accepting invite: {e}")
        return jsonify({"error": "Failed to accept invite"}), 500


@invitation_bp.route("/cancel_invite/<invite_token>", methods=["POST"])
def cancel_invite(invite_token):
    """Cancels a pending team invitation."""
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        result, success = invite_service.cancel_invite(invite_token, g.user_id)
        if success:
            return jsonify(result), 200
        else:
            status_code = 403 if "Permission denied" in result.get("error", "") else 400
            return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error cancelling invite: {e}")
        return jsonify({"error": "Failed to cancel invite"}), 500


@invitation_bp.route("/team/<team_id>/invites", methods=["GET"])
def get_team_invites(team_id):
    """Gets all pending invites for a team."""
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Check if user has permission to view team invites
        is_member = invite_service.check_team_membership(team_id, g.user_id)
        if not is_member:
            return jsonify({"error": "Permission denied"}), 403

        invites = invite_service.get_team_invites(team_id)
        return jsonify({"invites": invites}), 200
    except Exception as e:
        logger.error(f"Error retrieving team invites: {e}")
        return jsonify({"error": "Failed to retrieve invites"}), 500


@invitation_bp.route("/user/invites", methods=["GET"])
def get_user_invites():
    """Gets all pending invites for the current user."""
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user = collection.database.Users.find_one({"_id": g.user_id})
        if not user or not user.get("email"):
            return jsonify({"error": "User email not found"}), 400

        invites = invite_service.get_user_invites(user["email"])
        return jsonify({"invites": invites}), 200
    except Exception as e:
        logger.error(f"Error retrieving user invites: {e}")
        return jsonify({"error": "Failed to retrieve invites"}), 500
