from flask import request, jsonify, Blueprint, g
from database.mongo_connection import collection
from datetime import datetime, timezone
import uuid
from Entities.podcasts import PodcastSchema

# Define Blueprint
podcast_bp = Blueprint("podcast_bp", __name__)

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timezone
import uuid
from database.mongo_connection import collection
from Entities.podcasts import PodcastSchema  # Ensure this schema exists

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timezone
import uuid
from database.mongo_connection import collection
from Entities.podcasts import PodcastSchema

podcast_bp = Blueprint("podcast_bp", __name__)

@podcast_bp.route("/add_podcast", methods=["POST"])
def podcast():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Validate Content-Type
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        # 🔍 Fetch account ID from MongoDB (assuming `id` is stored as a STRING, not ObjectId)
        user_account = collection.database.Accounts.find_one({"userId": g.user_id})
        if not user_account:
            return jsonify({"error": "No account associated with this user"}), 403

        account_id = user_account["id"]  # Keep as string
        print(f"🧩 Found account {account_id} for user {g.user_id}")

        # Get the data from the request
        data = request.get_json()
        print("📩 Received Data:", data)

        # Validate data using PodcastSchema
        schema = PodcastSchema()
        errors = schema.validate(data)
        if errors:
            return jsonify({"error": "Invalid data", "details": errors}), 400

        validated_data = schema.load(data)

        # Ensure `accountId` exists and belongs to the user
        account = collection.database.Accounts.find_one({"id": account_id, "userId": g.user_id})
        if not account:
            return jsonify({"error": "Invalid account ID or you do not have permission to add a podcast to this account."}), 403

        # Generate unique podcast ID
        podcast_id = str(uuid.uuid4())

        # Create podcast document
        podcast_item = {
            "_id": podcast_id,
            "teamId": validated_data.get("teamId"),
            "accountId": account_id,  # Use the fetched string accountId
            "podName": validated_data.get("podName"),
            "ownerName": validated_data.get("ownerName"),
            "hostName": validated_data.get("hostName"),
            "rssFeed": validated_data.get("rssFeed"),
            "googleCal": validated_data.get("googleCal"),
            "podUrl": validated_data.get("podUrl"),
            "guestUrl": validated_data.get("guestUrl"),
            "socialMedia": validated_data.get("socialMedia", []),
            "email": validated_data.get("email"),
            "description": validated_data.get("description"),
            "logoUrl": validated_data.get("logoUrl"),
            "category": validated_data.get("category"),
            "defaultTasks": validated_data.get("defaultTasks", []),
            "created_at": datetime.now(timezone.utc),
        }

        # Insert into database
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



    
@podcast_bp.route("/get_podcast", methods=["GET"])
def get_podcast():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)

        # Find all accounts owned by the user
        user_accounts = list(collection.database.Account.find({"userId": user_id}, {"id": 1}))  # Get only `id`
        user_account_ids = [account["id"] for account in user_accounts]

        if not user_account_ids:
            return jsonify({"podcast": []}), 200  # No accounts, return empty list

        # Find podcasts linked to any of the user's accounts
        podcasts = list(collection.database.Podcasts.find({"accountId": {"$in": user_account_ids}}))

        # Convert `_id` fields to strings
        for podcast in podcasts:
            podcast["_id"] = str(podcast["_id"])

        return jsonify({"podcast": podcasts}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch podcasts: {str(e)}"}), 500
    
@podcast_bp.route("/get_podcast/<podcast_id>", methods=["GET"])
def get_podcast_by_id(podcast_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)

        # Find all accounts owned by the user
        user_accounts = list(collection.database.Accounts.find({"userId": user_id}, {"id": 1}))
        user_account_ids = [account["id"] for account in user_accounts]

        if not user_account_ids:
            return jsonify({"error": "No accounts found for user"}), 403

        # Find the podcast by ID and check if it belongs to one of the user's accounts
        podcast = collection.database.Podcasts.find_one({"id": podcast_id, "accountId": {"$in": user_account_ids}})

        if not podcast:
            return jsonify({"error": "Podcast not found or unauthorized"}), 404

        # Convert `_id` to string for JSON compatibility
        podcast["_id"] = str(podcast["_id"])

        return jsonify({"podcast": podcast}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch podcast: {str(e)}"}), 500


    
@podcast_bp.route("/delete_podcast/<podcast_id>", methods=["DELETE"])
def delete_podcast(podcast_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)

        # Find all accounts owned by the user
        user_accounts = list(collection.database.Account.find({"userId": user_id}, {"id": 1}))  # Get only `id`
        user_account_ids = [account["id"] for account in user_accounts]

        if not user_account_ids:
            return jsonify({"error": "No accounts found for user"}), 403

        # Check if the podcast belongs to one of the user's accounts
        podcast = collection.database.Podcast.find_one({"id": podcast_id, "accountId": {"$in": user_account_ids}})

        if not podcast:
            return jsonify({"error": "Podcast not found or unauthorized"}), 404

        # Delete the podcast
        collection.database.Podcasts.delete_one({"id": podcast_id})

        return jsonify({"message": "Podcast deleted successfully"}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to delete podcast: {str(e)}"}), 500


    
@podcast_bp.route("/edit_podcast/<podcast_id>", methods=["PUT"])
def edit_podcast(podcast_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)

        # Fetch all accounts owned by the user
        user_accounts = list(collection.database.Account.find({"userId": user_id}, {"id": 1}))
        user_account_ids = [account["id"] for account in user_accounts]

        if not user_account_ids:
            return jsonify({"error": "No accounts found for user"}), 403

        # Find the podcast by ID and check if it belongs to one of the user's accounts
        podcast = collection.database.Podcasts.find_one({"id": podcast_id, "accountId": {"$in": user_account_ids}})

        if not podcast:
            return jsonify({"error": "Podcast not found or unauthorized"}), 404

        # Get new data from the request
        data = request.get_json()

        # Validate data using PodcastSchema
        schema = PodcastSchema(partial=True)  # Allow partial updates
        errors = schema.validate(data)
        if errors:
            return jsonify({"error": "Invalid data", "details": errors}), 400

        # Prepare update data
        update_data = {key: value for key, value in data.items() if value is not None}

        # Update the podcast
        result = collection.database.Podcast.update_one(
            {"id": podcast_id},
            {"$set": update_data}
        )

        if result.modified_count == 1:
            return jsonify({"message": "Podcast updated successfully"}), 200
        else:
            return jsonify({"error": "No changes made to the podcast"}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to update podcast: {str(e)}"}), 500


