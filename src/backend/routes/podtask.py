from flask import Blueprint, request, jsonify, g
from backend.repository.podtask_repository import PodtaskRepository

# Define Blueprint
podtask_bp = Blueprint("podtask_bp", __name__)

# Instantiate the Podtask Repository
podtask_repo = PodtaskRepository()


@podtask_bp.route("/add_podtasks", methods=["POST"])
def register_podtask():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

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

    data = request.get_json()
    response, status_code = podtask_repo.update_podtask(g.user_id, task_id, data)
    return jsonify(response), status_code
