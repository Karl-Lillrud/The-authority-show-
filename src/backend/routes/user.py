import logging
from flask import Blueprint, request, jsonify, g
from backend.repository.user_repository import UserRepository
import uuid
from datetime import datetime
from backend.database.mongo_connection import collection  # Add this import

# Define Blueprint
user_bp = Blueprint("user_bp", __name__)

# Instantiate the User Repository
user_repo = UserRepository()


# Route to fetch user profile data
@user_bp.route("/get_profile", methods=["GET"])
def get_profile():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    response, status_code = user_repo.get_profile(str(g.user_id))
    if status_code == 404:  # If profile not found, ensure account creation
        account = collection.database.Accounts.find_one({"userId": str(g.user_id)})
        if not account:
            account_data = {
                "id": str(uuid.uuid4()),
                "userId": str(g.user_id),
                "email": g.email,
                "created_at": datetime.utcnow(),
                "isActive": True,
            }
            collection.database.Accounts.insert_one(account_data)
    return jsonify(response), status_code


# Route to update user profile data//
@user_bp.route("/update_profile", methods=["PUT"])
def update_profile():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    response, status_code = user_repo.update_profile(str(g.user_id), data)
    return jsonify(response), status_code

"""
# Route to update password
@user_bp.route("/update_password", methods=["PUT"])
def update_password():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    response, status_code = user_repo.update_password(str(g.user_id), data)
    return jsonify(response), status_code

"""

# Route to delete user account and associated data
@user_bp.route("/delete_user", methods=["DELETE"])
def delete_user():
    try:
        data = request.get_json()
        response, status_code = user_repo.delete_user(data)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"error": f"Error during deletion: {str(e)}"}), 500
