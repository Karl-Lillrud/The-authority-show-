from flask import request, jsonify, Blueprint, g, session, url_for
from backend.repository.guest_repository import GuestRepository
from backend.database.mongo_connection import collection
from backend.utils.email_utils import send_email, send_guest_invitation_email
from backend.services.invitation_service import InvitationService
from backend.utils.token_utils import decode_token
import logging

# Define Blueprint
guest_bp = Blueprint("guest_bp", __name__)

# Create repository instance
guest_repo = GuestRepository()

# Configure logger
logger = logging.getLogger(__name__)

# SHOULD ONLY BE USED FOR SPECIFIC DATA CRUD OPERATIONS
# EXTRA FUNCTIONALITY BESIDES CRUD OPERATIONS SHOULD BE IN SERVICES

@guest_bp.route("/add_guest", methods=["POST"])
def add_guest():
    """
    Adds a guest to the system and sends an invitation email.
    """
    try:
        data = request.json
        user_id = session.get("user_id")

        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        # ✅ Corrected argument order
        response, status_code = guest_repo.add_guest(data, user_id)

        return jsonify(response), status_code

    except Exception as e:
        logger.error(f"Failed to add guest: {e}", exc_info=True)
        return jsonify({"error": f"Failed to add guest: {str(e)}"}), 500


@guest_bp.route("/get_guests", methods=["GET"])
def get_guests():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        response, status_code = guest_repo.get_guests(g.user_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to fetch guests: {str(e)}"}), 500

@guest_bp.route("/edit_guests/<guest_id>", methods=["PUT"])
def edit_guest(guest_id):
    """Updates a guest's information, including the option to change the episode they are linked to."""
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        data = request.get_json()
        response, status_code = guest_repo.edit_guest(guest_id, data, g.user_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to update guest: {str(e)}"}), 500

@guest_bp.route("/delete_guests/<guest_id>", methods=["DELETE"])
def delete_guest(guest_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        response, status_code = guest_repo.delete_guest(guest_id, g.user_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to delete guest: {str(e)}"}), 500

@guest_bp.route("/get_guests_by_episode/<episode_id>", methods=["GET"])
def get_guests_by_episode(episode_id):
    """Fetch all guest profiles linked to a specific episode ID."""
    user_id = getattr(g, "user_id", None)

    # Om användaren inte är inloggad – kolla om ett giltigt token finns (från gäst)
    if not user_id:
        token = request.args.get("token") or request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"error": "Unauthorized"}), 401
        try:
            decoded = decode_token(token)
            guest_id = decoded.get("user_id") or decoded.get("guest_id")  # beroende på hur du kodar token
            if not guest_id:
                return jsonify({"error": "Invalid token"}), 403
        except Exception as e:
            logger.warning(f"Failed to decode guest token: {e}")
            return jsonify({"error": "Invalid or expired token"}), 403

    try:
        response, status_code = guest_repo.get_guests_by_episode(episode_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception("❌ ERROR: Failed to fetch guests by episode")
        return jsonify({"error": f"Failed to fetch guests by episode: {str(e)}"}), 500

@guest_bp.route("/get_guests_by_id/<guest_id>", methods=["GET"])
def get_guest_by_id(guest_id):
    """Fetch a guest by their unique guest_id."""
    try:
        # Fetch guest from the repository
        response, status_code = guest_repo.get_guest_by_id(g.user_id, guest_id)
        
        # If guest is found, return it
        if status_code == 200:
            return jsonify(response), status_code
        # If guest not found, return 404 error
        else:
            return jsonify(response), status_code
    except Exception as e:
        logger.error(f"Error fetching guest by ID: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

