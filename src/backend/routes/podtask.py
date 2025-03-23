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
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        data = request.get_json()
        print("📩 Received Podtask Data:", data)

        response, status_code = podtask_repo.register_podtask(g.user_id, data)
        return jsonify(response), status_code

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to register podtask: {str(e)}"}), 500


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

