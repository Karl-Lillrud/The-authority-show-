from venv import logger
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
    """Updates a podtask for the given user and task ID."""
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        data = request.get_json()
        response, status_code = podtask_repo.update_podtask(g.user_id, task_id, data)
        return jsonify(response), status_code
    except Exception as e:
        logger.exception("❌ ERROR: Failed to update task")
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


@podtask_bp.route("/add_tasks_to_episode", methods=["POST"])
def add_tasks_to_episode():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415
    try:
        data = request.get_json()
        tasks = data.get("tasks")
        episode_id = data.get("episode_id")
        guest_id = data.get("guest_id")
        response, status_code = podtask_repo.add_tasks_to_episode(g.user_id, episode_id, guest_id, tasks)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@podtask_bp.route('/add_default_tasks_to_episode', methods=['POST'])
def add_default_tasks_to_episode_route():
    if not g.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401
    try:
        data = request.get_json()
        episode_id = data.get("episode_id")
        default_tasks = data.get("default_tasks")
        # Log input values for debugging
        print("Adding default tasks:", episode_id, default_tasks)
        result, status = podtask_repo.add_default_tasks_to_episode(g.user_id, episode_id, default_tasks)
        return jsonify(result), status
    except Exception as e:
        print("Error in add_default_tasks_to_episode_route:", e)
        return jsonify({"error": str(e)}), 500
