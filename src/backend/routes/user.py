from flask import Blueprint, request, jsonify, g
from backend.repository.user_repository import UserRepository

# from backend.services.accountService import AccountService
import logging

user_bp = Blueprint("user_bp", __name__, url_prefix="/user")
user_repo = UserRepository()
logger = logging.getLogger(__name__)


@user_bp.route("/get_profile", methods=["GET"])
def get_profile():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Obehörig"}), 401

    response, status_code = user_repo.get_profile(str(g.user_id))
    return jsonify(response), status_code


@user_bp.route("/update_profile", methods=["PUT"])
def update_profile():
    if not hasattr(g, "user_id") or not g.user_id:
        logger.error(f"Unauthorized access attempt by user {g.user_id}")
        return jsonify({"error": "Obehörig"}), 401

    data = request.get_json()
    logger.info(f"Received data to update profile: {data}")
    response, status_code = user_repo.update_profile(str(g.user_id), data)
    logger.info(f"Profile updated for user {g.user_id}: {response}")
    return jsonify(response), status_code


@user_bp.route("/delete_user", methods=["DELETE"])
def delete_user():
    try:
        data = request.get_json()
        response, status_code = user_repo.delete_user(data)
        return jsonify(response), status_code
    except Exception as e:
        logger.error(f"Fel vid radering av användare: {e}", exc_info=True)
        return jsonify({"error": f"Fel vid radering: {str(e)}"}), 500
