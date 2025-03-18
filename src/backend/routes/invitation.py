from flask import Blueprint, request, jsonify, render_template, url_for, g
from backend.utils.email_utils import send_email
from backend.database.mongo_connection import collection
from backend.models.podcasts import PodcastSchema
from backend.services.TeamInviteService import TeamInviteService
from datetime import datetime, timezone
import uuid
import logging

invitation_bp = Blueprint("invitation_bp", __name__)

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
invite_service = TeamInviteService()


@invitation_bp.route("/send_invitation", methods=["POST"])
def send_invitation():
    try:
        logger.info("Received send_invitation request")  # Added log
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
    return render_template("beta-email/podmanager-beta-invite.html")

from flask import Blueprint, request, jsonify, g
from backend.services.TeamInviteService import TeamInviteService  # ✅ Ensure correct import

invitation_bp = Blueprint("invitation_bp", __name__)

# ✅ Initialize the service
invite_service = TeamInviteService()

@invitation_bp.route("/send_team_invite", methods=["POST"])
def send_team_invite():
    """Sends an invitation email to join a team."""
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    email = data.get("email")
    team_id = data.get("teamId")

    if not email or not team_id:
        return jsonify({"error": "Missing email or teamId"}), 400

    # ✅ Ensure invite_service has `send_invite` method
    response, status_code = invite_service.send_invite(g.user_id, team_id, email)
    return jsonify(response), status_code

@invitation_bp.route("/verify_invite/<invite_token>", methods=["GET"])
def verify_invite(invite_token):
    """Verifies if an invite token is valid without registering."""
    response, status_code = invite_service.verify