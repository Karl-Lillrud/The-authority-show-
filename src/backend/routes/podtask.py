from flask import request, jsonify, Blueprint, g
from backend.repository.podtask_repository import PodtaskRepository

# Define Blueprint
podtask_bp = Blueprint("podtask_bp", __name__)

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
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        data = request.get_json()
        response, status_code = podtask_repo.update_podtask(g.user_id, task_id, data)
        return jsonify(response), status_code
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to update podtask: {str(e)}"}), 500

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