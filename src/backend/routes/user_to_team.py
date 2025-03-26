import logging

logger = logging.getLogger(__name__)

from flask import Blueprint, request, jsonify, g
from backend.repository.usertoteam_repository import UserToTeamRepository

# Define Blueprint
usertoteam_bp = Blueprint("usertoteam_bp", __name__)

# Instantiate the User-To-Team Repository
usertoteam_repo = UserToTeamRepository()


@usertoteam_bp.route("/add_users_to_teams", methods=["POST"])
def add_user_to_team():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    response, status_code = usertoteam_repo.add_user_to_team(data)
    return jsonify(response), status_code


@usertoteam_bp.route("/remove_users_from_teams", methods=["POST"])
def remove_user_from_team():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    response, status_code = usertoteam_repo.remove_user_from_team(data)
    return jsonify(response), status_code


@usertoteam_bp.route("/get_teams_members/<team_id>", methods=["GET"])
def get_team_members(team_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    response, status_code = usertoteam_repo.get_team_members(team_id)
    return jsonify(response), status_code


@usertoteam_bp.route("/get_team_members", methods=["GET"])
def get_all_team_members():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    response, status_code = usertoteam_repo.get_all_team_members()
    return jsonify(response), status_code


@usertoteam_bp.route("/edit_team_member", methods=["PUT"])
def edit_team_member():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    logger.info(f"Incoming payload for /edit_team_member: {data}")

    team_id = data.get("teamId")
    user_id = data.get("userId")
    new_role = data.get("role")
    full_name = data.get("fullName")  # New field
    phone = data.get("phone")  # New field

    if not team_id or not user_id or not new_role:
        logger.error("Missing required fields in /edit_team_member")
        return jsonify({"error": "Missing teamId, userId, or role"}), 400

    response, status_code = usertoteam_repo.edit_team_member(
        team_id, user_id, new_role, full_name, phone
    )
    return jsonify(response), status_code


@usertoteam_bp.route("/delete_team_member", methods=["DELETE"])
def delete_team_member():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    team_id = data.get("teamId")
    user_id = data.get("userId")
    email = data.get("email")

    if not team_id:
        return jsonify({"error": "Missing teamId"}), 400

    response, status_code = usertoteam_repo.delete_team_member(team_id, user_id, email)
    return jsonify(response), status_code
