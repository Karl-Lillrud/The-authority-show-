from flask import Blueprint, request, jsonify, g # Import g
import logging

podtask_bp = Blueprint("podtask_bp", __name__)
logger = logging.getLogger(__name__)


@podtask_bp.route("/podtasks", methods=["POST"])
def add_podtask():
    # Check for user_id from g
    user_id = getattr(g, 'user_id', None)
    if not user_id:
        logger.warning("Unauthorized attempt to add podtask.")
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    # Pass user_id to the service layer if needed
    response, status_code = podtask_service.add_podtask(data, user_id) 
    return jsonify(response), status_code


@podtask_bp.route("/podtasks/<task_id>", methods=["GET"])
def get_podtask(task_id):
    # Check for user_id from g
    user_id = getattr(g, 'user_id', None)
    if not user_id:
        logger.warning(f"Unauthorized attempt to get podtask {task_id}.")
        return jsonify({"error": "Unauthorized"}), 401

    # Pass user_id to the service layer for authorization checks if necessary
    response, status_code = podtask_service.get_podtask(task_id, user_id) 
    return jsonify(response), status_code


@podtask_bp.route("/podtasks", methods=["GET"])
def get_all_podtasks():
    # Check for user_id from g
    user_id = getattr(g, 'user_id', None)
    if not user_id:
        logger.warning("Unauthorized attempt to get all podtasks.")
        return jsonify({"error": "Unauthorized"}), 401

    # Pass user_id to the service layer to fetch tasks for this user
    response, status_code = podtask_service.get_all_podtasks(user_id) 
    return jsonify(response), status_code


@podtask_bp.route("/podtasks/<task_id>", methods=["PUT"])
def update_podtask(task_id):
    # Check for user_id from g
    user_id = getattr(g, 'user_id', None)
    if not user_id:
        logger.warning(f"Unauthorized attempt to update podtask {task_id}.")
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    # Pass user_id to the service layer for authorization checks
    response, status_code = podtask_service.update_podtask(task_id, data, user_id) 
    return jsonify(response), status_code


@podtask_bp.route("/podtasks/<task_id>", methods=["DELETE"])
def delete_podtask(task_id):
    # Check for user_id from g
    user_id = getattr(g, 'user_id', None)
    if not user_id:
        logger.warning(f"Unauthorized attempt to delete podtask {task_id}.")
        return jsonify({"error": "Unauthorized"}), 401

    # Pass user_id to the service layer for authorization checks
    response, status_code = podtask_service.delete_podtask(task_id, user_id) 
    return jsonify(response), status_code

# Add similar checks and usage of g.user_id to any other relevant routes 
# for episode-to-do functionality.