from flask import request, jsonify, Blueprint, g, redirect, url_for
from backend.database.mongo_connection import collection
from datetime import datetime, timezone
import uuid
from backend.models.podcasts import PodcastSchema
import logging

# Define Blueprint
podcast_bp = Blueprint("podcast_bp", __name__)

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@podcast_bp.route("/post_podcast_data", methods=["POST"])
def post_podcast_data():
    try:
        data = request.get_json()
        podName = data.get('podName')
        podRss = data.get('podRss')
        # Add your logic to handle the podcast data here
        # For example, save to the database and generate a redirect URL
        logger.info(f"Received podcast data: podName={podName}, podRss={podRss}")
        redirect_url = url_for('frontend.podprofile') + '#production-team-section'  # Ensure this matches the actual route
        return jsonify(success=True, redirectUrl=redirect_url)
    except Exception as e:
        logger.error(f"Error in post_podcast_data: {e}")
        return jsonify(success=False, error=str(e)), 500

@podcast_bp.route("/production_team", methods=["GET"])
def production_team():
    # Define the logic for the production team route
    return "Production Team Page"

@podcast_bp.route("/get_podcasts", methods=["GET"])
def get_podcast():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)

        # Find all accounts owned by the user.
        # Using "Accounts" to be consistent with the POST endpoint.
        user_accounts = list(
            collection.database.Accounts.find({"userId": user_id}, {"id": 1, "_id": 1})
        )
        # Extract the account ids, preferring the custom "id" if available.
        user_account_ids = [
            account["id"] if "id" in account else str(account["_id"])
            for account in user_accounts
        ]

        if not user_account_ids:
            return jsonify({"podcast": []}), 200  # No accounts found; return empty list

        # Find podcasts linked to any of the user's accounts.
        podcasts = list(
            collection.database.Podcasts.find({"accountId": {"$in": user_account_ids}})
        )

        # Convert MongoDB ObjectId fields to strings for JSON serialization.
        for podcast in podcasts:
            podcast["_id"] = str(podcast["_id"])

        return jsonify({"podcast": podcasts}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch podcasts: {str(e)}"}), 500

@podcast_bp.route("/get_podcasts/<podcast_id>", methods=["GET"])
def get_podcast_by_id(podcast_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)

        # Find all accounts owned by the user, retrieving both "id" and "_id" fields.
        user_accounts = list(
            collection.database.Accounts.find({"userId": user_id}, {"id": 1, "_id": 1})
        )
        user_account_ids = [
            account["id"] if "id" in account else str(account["_id"])
            for account in user_accounts
        ]

        if not user_account_ids:
            return jsonify({"error": "No accounts found for user"}), 403

        # Find the podcast by its _id (not "id") and ensure it belongs to one of the user's accounts.
        podcast = collection.database.Podcasts.find_one(
            {"_id": podcast_id, "accountId": {"$in": user_account_ids}}
        )

        if not podcast:
            return jsonify({"error": "Podcast not found or unauthorized"}), 404

        # Convert MongoDB's ObjectId to a string for JSON compatibility.
        podcast["_id"] = str(podcast["_id"])

        return jsonify({"podcast": podcast}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch podcast: {str(e)}"}), 500

@podcast_bp.route("/delete_podcasts/<podcast_id>", methods=["DELETE"])
def delete_podcast(podcast_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)

        # Find all accounts owned by the user (fetching both "id" and "_id")
        user_accounts = list(
            collection.database.Accounts.find({"userId": user_id}, {"id": 1, "_id": 1})
        )
        user_account_ids = [
            account["id"] if "id" in account else str(account["_id"])
            for account in user_accounts
        ]

        if not user_account_ids:
            return jsonify({"error": "No accounts found for user"}), 403

        # Check if the podcast belongs to one of the user's accounts using _id
        podcast = collection.database.Podcasts.find_one(
            {"_id": podcast_id, "accountId": {"$in": user_account_ids}}
        )

        if not podcast:
            return jsonify({"error": "Podcast not found or unauthorized"}), 404

        # Delete the podcast
        result = collection.database.Podcasts.delete_one({"_id": podcast_id})
        if result.deleted_count == 1:
            return jsonify({"message": "Podcast deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete podcast"}), 500

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to delete podcast: {str(e)}"}), 500

@podcast_bp.route("/edit_podcasts/<podcast_id>", methods=["PUT"])
def edit_podcast(podcast_id):
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)

        # Fetch all accounts owned by the user (retrieving both "id" and "_id")
        user_accounts = list(
            collection.database.Accounts.find({"userId": user_id}, {"id": 1, "_id": 1})
        )
        user_account_ids = [
            account["id"] if "id" in account else str(account["_id"])
            for account in user_accounts
        ]

        if not user_account_ids:
            return jsonify({"error": "No accounts found for user"}), 403

        # Find the podcast by its _id and ensure it belongs to one of the user's accounts
        podcast = collection.database.Podcasts.find_one(
            {"_id": podcast_id, "accountId": {"$in": user_account_ids}}
        )

        if not podcast:
            return jsonify({"error": "Podcast not found or unauthorized"}), 404

        # Get new data from the request
        data = request.get_json()

        # Validate data using PodcastSchema (allowing partial updates)
        schema = PodcastSchema(partial=True)
        errors = schema.validate(data)
        if errors:
            return jsonify({"error": "Invalid data", "details": errors}), 400

        # Prepare update data (ignoring keys with None values)
        update_data = {key: value for key, value in data.items() if value is not None}

        if not update_data:
            return jsonify({"message": "No update data provided"}), 200

        # Update the podcast document
        result = collection.database.Podcasts.update_one(
            {"_id": podcast_id}, {"$set": update_data}
        )

        if result.modified_count == 1:
            return jsonify({"message": "Podcast updated successfully"}), 200
        else:
            return jsonify({"message": "No changes made to the podcast"}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to update podcast: {str(e)}"}), 500


@podcast_bp.route('/get_user_podcasts', methods=['GET'])
def get_user_podcasts():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    # Fetch podcasts for the user from the database
    podcasts = collection.find({"user_id": user_id})
    podcast_list = []
    for podcast in podcasts:
        podcast_list.append({
            "name": podcast.get("name"),
            "image_url": podcast.get("image_url"),
            "open_episodes": podcast.get("open_episodes", 0)
        })

    return jsonify(podcast_list)
