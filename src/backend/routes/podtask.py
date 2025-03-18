from flask import request, jsonify, Blueprint, g
from backend.database.mongo_connection import collection
from datetime import datetime, timezone
from backend.models.podtasks import PodtaskSchema
import uuid
import json
from flask import Blueprint, request, jsonify, g
from backend.repository.podtask_repository import PodtaskRepository

# Define Blueprint
podtask_bp = Blueprint("podtask_bp", __name__)

# SHOULD ONLY BE USED FOR SPECIFIC DATA CRUD OPERATIONS
# EXTRA FUNCTIONALITY BESIDES CRUD OPERATIONS SHOULD BE IN SERVICES
# Instantiate the Podtask Repository
podtask_repo = PodtaskRepository()


@podtask_bp.route("/add_podtasks", methods=["POST"])
def register_podtask():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401


    # Validate Content-Type
    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415,
        )

    try:
        data = request.get_json()
        print("📩 Received Podtask Data:", data)

        # Validate data using PodtaskSchema
        schema = PodtaskSchema()
        errors = schema.validate(data)
        if errors:
            return jsonify({"error": "Invalid data", "details": errors}), 400

        validated_data = schema.load(data)

        user_id = str(g.user_id)  # Get the user ID

        # Fetch accounts associated with the user using the correct field `userId`
        user_accounts = list(
            collection.database.Accounts.find({"userId": user_id}, {"_id": 1})
        )
        print(f"Found accounts: {user_accounts}")

        if not user_accounts:
            return jsonify({"error": "No accounts found for user"}), 403

        # Extract account IDs
        user_account_ids = [
            str(account["_id"]) for account in user_accounts
        ]  # Use _id as account ID

        # Fetch the podcasts associated with these account IDs
        podcasts = list(
            collection.database.Podcasts.find({"accountId": {"$in": user_account_ids}})
        )
        print(f"Found podcasts for the user: {podcasts}")

        if not podcasts:
            return jsonify({"error": "No podcasts found for user"}), 404

        # Assume we link the first podcast, or you could add logic to select one
        selected_podcast = podcasts[0]
        podcast_id = str(selected_podcast["_id"])  # Get the podcast ID

        # Set the podcastId for the podtask
        validated_data["podcastId"] = podcast_id

        # Add metadata to the podtask document
        validated_data["userid"] = user_id
        validated_data["created_at"] = datetime.now(timezone.utc)

        # Generate a unique `id` for the podtask manually (UUID as string)
        podtask_id = str(uuid.uuid4())  # Manually generate the `id` field as a string

        # Insert the podtask into the database
        podtask_document = {
            "_id": podtask_id,  # Set the UUID as the explicit _id field
            "podcastId": validated_data["podcastId"],
            "name": validated_data.get("name"),
            "action": validated_data.get("action"),
            "dayCount": validated_data.get("dayCount"),
            "description": validated_data.get("description"),
            "actionUrl": validated_data.get("actionUrl"),
            "urlDescribe": validated_data.get("urlDescribe"),
            "submissionReq": validated_data.get("submissionReq"),
            "status": validated_data.get("status"),
            "assignedAt": validated_data.get("assignedAt"),
            "dueDate": validated_data.get("dueDate"),
            "priority": validated_data.get("priority"),
            "userid": validated_data[
                "userid"
            ],  # not neccessary, Lazy way to test user session correctness #can be removed
            "created_at": validated_data["created_at"],
        }

        # Insert the podtask into the database
        print("📝 Inserting podtask into database:", podtask_document)
        result = collection.database["Podtasks"].insert_one(podtask_document)

        if result.inserted_id:
            print("✅ Podtask registered successfully!")
            return (
                jsonify(
                    {
                        "message": "Podtask registered successfully",
                        "podtask_id": podtask_id,
                    }
                ),
                201,
            )
        else:
            return jsonify({"error": "Failed to register podtask"}), 500

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to register podtask: {str(e)}"}), 500

    data = request.get_json()
    response, status_code = podtask_repo.register_podtask(g.user_id, data)
    return jsonify(response), status_code


@podtask_bp.route("/get_podtasks", methods=["GET"])
def get_podtasks():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    response, status_code = podtask_repo.get_podtasks(g.user_id)
    return jsonify(response), status_code


@podtask_bp.route("/delete_podtasks/<task_id>", methods=["DELETE"])
def delete_podtask(task_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    response, status_code = podtask_repo.delete_podtask(g.user_id, task_id)
    return jsonify(response), status_code


@podtask_bp.route("/update_podtasks/<task_id>", methods=["PUT"])
def update_podtask(task_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401


    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415,
        )

    try:
        # Parse the request data as JSON
        data = request.get_json()

        # Debugging: log the incoming data to see its structure
        print("Incoming data:", data)

        user_id = str(g.user_id)

        # Query the task using the task_id (ensure it's a string match)
        existing_task = collection.database.Podtasks.find_one({"_id": task_id})
        if not existing_task:
            return jsonify({"error": "Task not found"}), 404

        if existing_task["userid"] != user_id:
            return jsonify({"error": "Permission denied"}), 403

        # Prepare the fields to update
        update_fields = {
            "name": data.get("taskname", existing_task.get("name", "")).strip(),
            "description": data.get(
                "Description", existing_task.get("description", "")
            ).strip(),
            "dayCount": data.get("DayCount", existing_task.get("dayCount")),
            "action": data.get("action", existing_task.get("action", [])),
            "actionUrl": data.get(
                "actionurl", existing_task.get("actionUrl", "")
            ).strip(),
            "urlDescribe": data.get(
                "externalurl", existing_task.get("urlDescribe", "")
            ).strip(),
            "submissionReq": (
                True if data.get("submission", "Optional") == "Required" else False
            ),
            "updated_at": datetime.now(timezone.utc),
        }

        # Update the task in the database
        result = collection.database.Podtasks.update_one(
            {"_id": task_id}, {"$set": update_fields}  # Match on "_id" field (string)
        )

        if result.modified_count == 1:
            return jsonify({"message": "Task updated successfully"}), 200
        else:
            return jsonify({"message": "No changes made to the task"}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to update task: {str(e)}"}), 500


# New route to fetch default tasks from JSON file
@podtask_bp.route('/default_tasks', methods=['GET'])
def get_default_tasks():
    try:
        with open('frontend/static/defaulttaskdata/default_tasks.json') as f:
            default_tasks = json.load(f)
        return jsonify(default_tasks), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Register the blueprint
def register_podtask_routes(app):
    app.register_blueprint(podtask_bp)

    data = request.get_json()
    response, status_code = podtask_repo.update_podtask(g.user_id, task_id, data)
    return jsonify(response), status_code
