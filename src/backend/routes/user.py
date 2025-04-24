from flask import Blueprint, request, jsonify, g
from backend.repository.user_repository import UserRepository
from backend.utils.blob_storage import upload_file_to_blob

import logging

user_bp = Blueprint("user_bp", __name__, url_prefix="/user")
user_repo = UserRepository()
logger = logging.getLogger(__name__)


@user_bp.route("/get_profile", methods=["GET"])
def get_profile():
    """Gets the profile details for the currently logged-in user."""
    if not hasattr(g, 'user_id') or not g.user_id:
        logger.warning("Unauthorized attempt to access /get_profile")
        return jsonify({"error": "Unauthorized"}), 401

    try:
        logger.info(f"Fetching profile for user_id: {g.user_id}")
        # Use UserRepository to get profile data
        profile_data, status_code = user_repo.get_profile(g.user_id)

        if status_code == 200:
            logger.info(f"Successfully fetched profile for user_id: {g.user_id}")
        else:
            logger.error(f"Failed to fetch profile for user_id: {g.user_id}, Status: {status_code}, Data: {profile_data}")

        return jsonify(profile_data), status_code
    except Exception as e:
        logger.exception(f"❌ ERROR fetching profile via user_bp for user_id {g.user_id}: {e}")
        return jsonify({"error": "Failed to fetch profile data"}), 500


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


@user_bp.route("/upload_profile_picture", methods=["POST"])
def upload_profile_picture():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        file = request.files.get("profile_picture")
        if not file:
            return jsonify({"error": "No file provided"}), 400

        # Define the container name and blob path
        container_name = "podmanagerfiles"
        blob_path = f"users/{g.user_id}/profile/{file.filename}"

        # Upload the file to Azure Blob Storage
        blob_url = upload_file_to_blob(container_name, blob_path, file)

        # Update the user's profile picture URL in the database
        user_repo.update_profile(g.user_id, {"profile_picture_url": blob_url})

        return jsonify({"message": "Profile picture uploaded successfully", "url": blob_url}), 200

    except Exception as e:
        logger.error(f"Error uploading profile picture: {e}", exc_info=True)
        return jsonify({"error": f"Failed to upload profile picture: {str(e)}"}), 500
