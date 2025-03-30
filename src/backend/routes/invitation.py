from flask import Blueprint, request, jsonify, render_template, url_for, g
from backend.services.InvitationService import InvitationService
import logging

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Create the blueprint
invitation_bp = Blueprint("invitation_bp", __name__)

# Initialize the service once
invitation_service = InvitationService()


@invitation_bp.route("/send_invitation", methods=["POST"])
def send_invitation():
    """Send a beta invitation email to the logged-in user."""
    try:
        logger.info("Received send_invitation request")
        if not hasattr(g, "user_id") or not g.user_id:
            return jsonify({"error": "Unauthorized"}), 401

        # Fetch the user's email using InvitationService
        try:
            user_email = invitation_service.get_user_email(g.user_id)
        except ValueError as e:
            logger.error(str(e))
            return jsonify({"error": str(e)}), 400

        # Ensure the invitation type is valid
        invitation_type = "beta"  # Hardcoded for this endpoint
        result, status_code = invitation_service.send_invitation(
            invitation_type, user_email, inviter_id=g.user_id
        )
        return jsonify(result), status_code

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
        result, status_code = invitation_service.send_invitation(
            "team", email, inviter_id=g.user_id, team_id=team_id, role=role
        )
        return jsonify(result), status_code

    except Exception as e:
        logger.error("Error in /send_team_invite: %s", e)  # Debug log
        return jsonify({"error": "Failed to send invite"}), 500


@invitation_bp.route("/verify_invite/<invite_token>", methods=["GET"])
def verify_invite(invite_token):
    """Verifies if an invite token is valid without accepting it."""
    try:
        result, status_code = invitation_service.verify_invite(invite_token)
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Error verifying invite: {e}")
        return jsonify({"error": "Failed to verify invite"}), 500


@invitation_bp.route("/accept_invite/<invite_token>", methods=["POST"])
def accept_invite(invite_token):
    """Accepts a team invitation and removes it after successful registration."""
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        result, status_code = invitation_service.accept_invite(invite_token, g.user_id)
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error accepting invite: {e}")
        return jsonify({"error": "Failed to accept invite"}), 500


@invitation_bp.route("/cancel_invite/<invite_token>", methods=["POST"])
def cancel_invite(invite_token):
    """Cancels a pending team invitation."""
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        result, status_code = invitation_service.cancel_invite(invite_token, g.user_id)
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
        result, status_code = invitation_service.get_team_invites(team_id, g.user_id)
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error retrieving team invites: {e}")
        return jsonify({"error": "Failed to retrieve invites"}), 500


@invitation_bp.route("/user/invites", methods=["GET"])
def get_user_invites():
    """Gets all pending invites for the current user."""
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        result, status_code = invitation_service.get_user_invites(g.user_id)
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error retrieving user invites: {e}")
        return jsonify({"error": "Failed to retrieve invites"}), 500


@invitation_bp.route("/process_invitation", methods=["POST"])
def process_invitation():
    """
    Process an invitation by sending an email and optionally saving it to the database.
    """
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data or "email" not in data or "type" not in data:
        return jsonify({"error": "Missing required fields: email or type"}), 400

    email = data["email"]
    invitation_type = data["type"]
    team_id = data.get("teamId")
    role = data.get("role", "member")

    try:
        result, status_code = invitation_service.send_invitation(
            invitation_type, email, inviter_id=g.user_id, team_id=team_id, role=role
        )
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error processing invitation: {e}")
        return jsonify({"error": f"Failed to process invitation: {str(e)}"}), 500


@invitation_bp.route("/process_invitation_with_flag", methods=["POST"])
def process_invitation_with_flag():
    """
    Process an invitation based on a flag in the request.
    """
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data or "email" not in data or "type" not in data:
        return jsonify({"error": "Missing required fields: email or type"}), 400

    email = data["email"]
    invitation_type = data["type"]
    team_id = data.get("teamId")
    role = data.get("role", "member")
    send_email_flag = data.get("sendEmail", True)  # Default to sending the email

    try:
        if send_email_flag:
            # Send the invitation email
            result, status_code = invitation_service.send_invitation(
                invitation_type, email, inviter_id=g.user_id, team_id=team_id, role=role
            )
        else:
            # Only save the invitation to the database without sending an email
            invite_token = invitation_service.team_invite_repo.save_invite(
                team_id, email, g.user_id, role
            )
            result = {
                "message": "Invitation saved successfully",
                "inviteToken": invite_token,
            }
            status_code = 201

        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error processing invitation with flag: {e}")
        return jsonify({"error": f"Failed to process invitation: {str(e)}"}), 500
