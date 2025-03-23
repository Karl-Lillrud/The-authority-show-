from flask import request, jsonify, Blueprint, g
import logging
from backend.repository.guest_repository import GuestRepository

# Define Blueprint
guest_bp = Blueprint("guest_bp", __name__)

# Create repository instance
guest_repo = GuestRepository()

# Configure logger
logger = logging.getLogger(__name__)

# SHOULD ONLY BE USED FOR SPECIFIC DATA CRUD OPERATIONS
# EXTRA FUNCTIONALITY BESIDES CRUD OPERATIONS SHOULD BE IN SERVICES

@guest_bp.route("/add_guests", methods=["POST"])
def add_guest():
    """Adds a guest to the system and optionally links them to an episode."""
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        data = request.get_json()
        response, status_code = guest_repo.add_guest(data, g.user_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
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
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        response, status_code = guest_repo.get_guests_by_episode(episode_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.error("❌ ERROR: %s", e)
        return jsonify({"error": f"Failed to fetch guests by episode: {str(e)}"}), 500