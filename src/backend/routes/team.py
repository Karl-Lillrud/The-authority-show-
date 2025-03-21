from flask import Blueprint, request, jsonify, g, session
from backend.repository.team_repository import TeamRepository

# Define Blueprint
team_bp = Blueprint("team_bp", __name__)

# Instantiate the Team Repository
team_repo = TeamRepository()


@team_bp.before_request
def before_request():
    g.user_id = session.get("user_id")
    g.email = session.get("email")


@team_bp.route("/add_teams", methods=["POST"])
def add_team():
    data = request.get_json()  # Ensure the request contains the `description` field
    response, status_code = team_repo.add_team(g.user_id, g.email, data)
    return jsonify(response), status_code


@team_bp.route("/get_teams", methods=["GET"])
def get_teams():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    response, status_code = team_repo.get_teams(g.user_id)
    return jsonify(response), status_code


@team_bp.route("/delete_team/<team_id>", methods=["DELETE"])
def delete_team(team_id):
    response, status_code = team_repo.delete_team(team_id)
    return jsonify(response), status_code


@team_bp.route("/edit_team/<team_id>", methods=["PUT"])
def edit_team(team_id):
    data = request.get_json()
    response, status_code = team_repo.edit_team(team_id, data)
    return jsonify(response), status_code
