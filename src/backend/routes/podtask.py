from venv import logger
from flask import request, jsonify, Blueprint, g
from backend.database.mongo_connection import collection
from datetime import datetime, timezone
from backend.models.podtasks import PodtaskSchema
from backend.models.workflows import WorkflowSchema  # Import the schema
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


@podtask_bp.route('/get_podtask/<task_id>', methods=['GET'])
def get_podtask(task_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        task = podtask_repo.get_podtask_by_id(g.user_id, task_id)  # Using the repository method
        if task:
            return jsonify(task), 200
        else:
            return jsonify({'error': 'Task not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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

@podtask_bp.route("/save_workflow", methods=["POST"])
def save_workflow():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415
    try:
        data = request.get_json()
        episode_id = data.get("episode_id")
        tasks = data.get("tasks")
        # Get the name and description from the request data
        name = data.get("name", "Unnamed Workflow")  # Default if not provided
        description = data.get("description", "")  # Empty string if not provided

        # Create workflow
        workflow_id = str(uuid.uuid4())
        workflow_data = {
            "_id": workflow_id,
            "user_id": g.user_id,
            "episode_id": episode_id,
            "tasks": tasks,
            "name": name,  # Add name field
            "description": description,  # Add description field
            "created_at": datetime.now(timezone.utc),
        }

        # Save workflow to DB
        result = collection.database.Workflows.insert_one(workflow_data)

        if result.inserted_id:
            return jsonify({"message": "Workflow saved successfully", "workflow_id": workflow_id}), 201
        else:
            return jsonify({"error": "Failed to save workflow"}), 500

    except Exception as e:
        return jsonify({"error": f"Failed to save workflow: {str(e)}"}), 500

@podtask_bp.route("/import_workflow", methods=["GET"])
def import_workflow():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        # Extract the workflow_id from the query parameters
        workflow_id = request.args.get("workflow_id")
        
        if not workflow_id:
            return jsonify({"error": "Missing workflow ID"}), 400

        # Fetch the saved workflow from the database
        workflow = collection.database.Workflows.find_one({"_id": workflow_id, "user_id": g.user_id})
        if not workflow:
            return jsonify({"error": "Workflow not found"}), 404

        # Add the tasks from the workflow to the episode
        episode_id = request.args.get("episode_id")  # Ensure episode_id is passed as query parameter
        tasks_to_import = workflow["tasks"]
        
        response, status_code = podtask_repo.add_tasks_to_episode(g.user_id, episode_id, tasks_to_import)
        
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"error": f"Failed to import workflow: {str(e)}"}), 500

@podtask_bp.route('/get_workflows', methods=['GET'])
def get_workflows():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Fetch workflows from the database
        workflows = list(collection.database.Workflows.find({"user_id": g.user_id}))

        # Serialize the workflows to convert ObjectId to string
        schema = WorkflowSchema(many=True)
        workflows_data = schema.dump(workflows)

        return jsonify({"workflows": workflows_data}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch workflows: {str(e)}"}), 500

