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
        logger.info(f"Received podcast data: podName={podName}, podRss={podRss}")
        redirect_url = url_for('frontend.podprofile') + '#production-team-section'
        return jsonify(success=True, redirectUrl=redirect_url)
    except Exception as e:
        logger.error(f"Error in post_podcast_data: {e}")
        return jsonify(success=False, error=str(e)), 500

@podcast_bp.route("/production_team", methods=["GET"])
def production_team():
    return "Production Team Page"

@podcast_bp.route("/get_podcasts", methods=["GET"])
def get_podcast():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)
        # Find all accounts for this user
        user_accounts = list(
            collection.database.Accounts.find({"userId": user_id}, {"id": 1, "_id": 1})
        )
        account_ids = [
            acc["id"] if "id" in acc else str(acc["_id"])
            for acc in user_accounts
        ]
        if not account_ids:
            return jsonify({"podcast": []}), 200

        # Find podcasts linked to these account IDs
        podcasts = list(
            collection.database.Podcasts.find({"accountId": {"$in": account_ids}})
        )
        for pod in podcasts:
            pod["_id"] = str(pod["_id"])
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
        user_accounts = list(
            collection.database.Accounts.find({"userId": user_id}, {"id": 1, "_id": 1})
        )
        account_ids = [
            acc["id"] if "id" in acc else str(acc["_id"])
            for acc in user_accounts
        ]
        if not account_ids:
            return jsonify({"error": "No accounts found for user"}), 403

        podcast = collection.database.Podcasts.find_one(
            {"_id": podcast_id, "accountId": {"$in": account_ids}}
        )
        if not podcast:
            return jsonify({"error": "Podcast not found or unauthorized"}), 404

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
        user_accounts = list(
            collection.database.Accounts.find({"userId": user_id}, {"id": 1, "_id": 1})
        )
        account_ids = [
            acc["id"] if "id" in acc else str(acc["_id"])
            for acc in user_accounts
        ]
        if not account_ids:
            return jsonify({"error": "No accounts found for user"}), 403

        podcast = collection.database.Podcasts.find_one(
            {"_id": podcast_id, "accountId": {"$in": account_ids}}
        )
        if not podcast:
            return jsonify({"error": "Podcast not found or unauthorized"}), 404

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
        user_accounts = list(
            collection.database.Accounts.find({"userId": user_id}, {"id": 1, "_id": 1})
        )
        account_ids = [
            acc["id"] if "id" in acc else str(acc["_id"])
            for acc in user_accounts
        ]
        if not account_ids:
            return jsonify({"error": "No accounts found for user"}), 403

        podcast = collection.database.Podcasts.find_one(
            {"_id": podcast_id, "accountId": {"$in": account_ids}}
        )
        if not podcast:
            return jsonify({"error": "Podcast not found or unauthorized"}), 404

        data = request.get_json()
        schema = PodcastSchema(partial=True)
        errors = schema.validate(data)
        if errors:
            return jsonify({"error": "Invalid data", "details": errors}), 400

        update_data = {k: v for k, v in data.items() if v is not None}
        if not update_data:
            return jsonify({"message": "No update data provided"}), 200

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