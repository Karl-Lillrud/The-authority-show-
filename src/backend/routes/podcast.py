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

@podcast_bp.route("/add_podcasts", methods=["POST"])
def podcast():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Validate Content-Type
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        # 🔍 Fetch the account document from MongoDB for the logged-in user
        user_account = collection.database.Accounts.find_one({"userId": g.user_id})
        if not user_account:
            return jsonify({"error": "No account associated with this user"}), 403

        # Fetch the account ID that the user already has (do not override with a new one)
        if "id" in user_account:
            account_id = user_account["id"]
        else:
            account_id = str(user_account["_id"])
        print(f"🧩 Found account {account_id} for user {g.user_id}")

        # Get the data from the request and inject the accountId from the user's account
        data = request.get_json()
        print("📩 Received Data:", data)
        data["accountId"] = account_id  # Populate the required field with the fetched accountId
        data["email"] = session.get("user_email", "")  # Add the user's email to the data

        # Validate data using PodcastSchema
        schema = PodcastSchema()
        errors = schema.validate(data)
        if errors:
            return jsonify({"error": "Invalid data", "details": errors}), 400

        validated_data = schema.load(data)

        # (Optional) Double-check that the account exists and belongs to the user
        account_query = {"userId": g.user_id}
        if "id" in user_account:
            account_query["id"] = account_id
        else:
            account_query["_id"] = user_account["_id"]
        account = collection.database.Accounts.find_one(account_query)
        if not account:
            return jsonify({
                "error": "Invalid account ID or you do not have permission to add a podcast to this account."
            }), 403

        # Generate a unique podcast ID
        podcast_id = str(uuid.uuid4())

        # Create the podcast document with the accountId from the account document
        podcast_item = {
            "_id": podcast_id,
            "teamId": validated_data.get("teamId", ""),
            "accountId": account_id,  # Use the fetched accountId
            "podName": validated_data.get("podName", "") or "",
            "ownerName": validated_data.get("ownerName", "") or "",
            "hostName": validated_data.get("hostName", "") or "",
            "rssFeed": validated_data.get("rssFeed", "") or "",
            "googleCal": validated_data.get("googleCal", "") or "",
            "podUrl": validated_data.get("podUrl", "") or "",
            "guestUrl": validated_data.get("guestUrl", "") or "",
            "socialMedia": validated_data.get("socialMedia", []),
            "email": validated_data.get("email", "") or "",
            "description": validated_data.get("description", "") or "",
            "logoUrl": validated_data.get("logoUrl", "") or "",
            "category": validated_data.get("category", "") or "",
            "defaultTasks": validated_data.get("defaultTasks", []),
            "created_at": datetime.now(timezone.utc),
        }

        # Insert the podcast document into the database
        print("📝 Inserting podcast into database:", podcast_item)
        result = collection.database.Podcasts.insert_one(podcast_item)

        if result.inserted_id:
            print("✅ Podcast added successfully!")
            return jsonify({
                "message": "Podcast added successfully",
                "podcast_id": podcast_id,
                "redirect_url": "/index.html",
            }), 201
        else:
            return jsonify({"error": "Failed to add podcast to the database."}), 500

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to add podcast: {str(e)}"}), 500

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