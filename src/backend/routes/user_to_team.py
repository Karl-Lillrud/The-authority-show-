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
