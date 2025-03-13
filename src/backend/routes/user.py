from flask import Blueprint, request, jsonify, url_for, g
from backend.database.mongo_connection import collection
from backend.models.users import UserSchema  
from werkzeug.security import check_password_hash

user_bp = Blueprint("user_bp", __name__)

#SHOULD ONLY BE USED FOR SPECIFIC DATA CRUD OPERATIONS, Users collection
#EXTRA FUNCTIONALITY BESIDES CRUD OPERATIONS SHOULD BE IN SERVICES


#Should delete all user data from the database and associated collections
@user_bp.route("/delete_user", methods=["DELETE"])
def delete_user():

    try:
        data = request.get_json() or {}
        input_email = data.get("deleteEmail")
        input_password = data.get("deletePassword")
        delete_confirm = data.get("deleteConfirm", "").strip().upper()

        if delete_confirm != "DELETE":
            return jsonify({"error": "Please type 'DELETE' exactly to confirm account deletion."}), 400

        if not input_email or not input_password:
            return jsonify({"error": "Email and password are required."}), 400

        print(f"Attempting to delete user: {input_email}")  # Debugging
        # Retrieve the user document by email (case-insensitive search)
        user = collection.database.Users.find_one({
            "email": {"$regex": f"^{input_email}$", "$options": "i"}
        })
        if not user:
            return jsonify({"error": "User does not exist in the database."}), 404
        print(f"User not found: {input_email}")
        # Verify the provided password using Werkzeug's check_password_hash
        stored_hash = user.get("passwordHash")
        if not stored_hash:
            return jsonify({"error": "User record is missing password hash."}), 500

        if not check_password_hash(stored_hash, input_password):
            return jsonify({"error": "Incorrect password."}), 400

        # Ensure the user's identifier exists (using "id" instead of "_id")
        user_id = user.get("_id")
        if not user_id:
            return jsonify({"error": "User identifier missing from record."}), 500

        # Delete associated data from UsersToTeams and Teams collections
        collection.database.UsersToTeams.delete_many({
            "userId": user_id
        })

        collection.database.Teams.delete_many({
            "UserID": user_id
        })

        # Delete the user document from the Users collection
        user_result = collection.database.Users.delete_one({
            "_id": user_id
        })
        if user_result.deleted_count == 0:
            return jsonify({"error": "User deletion failed."}), 500

        return jsonify({
            "message": "User account and associated data deleted successfully.",
            "redirect": url_for("auth_bp.signin")
        }), 200

    except Exception as e:
        return jsonify({"error": f"Error during deletion: {str(e)}"}), 500
    
@user_bp.route("/get_email", methods=["GET"])
def fetch_user_email():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)
        user = collection.database.Users.find_one({"_id": user_id}, {"email": 1, "_id": 0})

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"email": user["email"]}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch email: {str(e)}"}), 500
