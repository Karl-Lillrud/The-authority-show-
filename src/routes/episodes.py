from flask import Blueprint, jsonify, g
from database.mongo_connection import collection
from bson import ObjectId

# Define Blueprint
episodes_bp = Blueprint("episodes_bp", __name__)


@episodes_bp.route("/get_open_episodes", methods=["GET"])
def get_open_episodes():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        guests = collection.database.Guest.find()
        open_episodes = {}
        for guest in guests:
            guest_id = guest["ID"]
            count = collection.database.Episodes.count_documents({"guest_id": guest_id})
            open_episodes[guest_id] = count

        return jsonify(open_episodes), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch episodes: {str(e)}"}), 500


@episodes_bp.route("/get_episodes_by_guest/<guest_id>", methods=["GET"])
def get_episodes_by_guest(guest_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        episodes = list(collection.database.Episodes.find({"guest_id": guest_id}))
        for episode in episodes:
            episode["_id"] = str(episode["_id"])

        return jsonify({"episodes": episodes}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch episodes: {str(e)}"}), 500


@episodes_bp.route("/get_tasks_by_episode/<episode_id>", methods=["GET"])
def get_tasks_by_episode(episode_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        tasks = list(collection.database.EpisodeTasks.find({"episode_id": episode_id}))
        for task in tasks:
            task["_id"] = str(task["_id"])

        return jsonify({"tasks": tasks}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch tasks: {str(e)}"}), 500


@episodes_bp.route("/view_tasks_by_episode/<episode_id>", methods=["GET"])
def view_tasks_by_episode(episode_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        tasks = list(collection.database.EpisodeTasks.find({"episode_id": episode_id}))
        for task in tasks:
            task["_id"] = str(task["_id"])

        return jsonify({"tasks": tasks}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch tasks: {str(e)}"}), 500


@episodes_bp.route("/delete_episode_task/<task_id>", methods=["DELETE"])
def delete_episode_task(task_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        task = collection.database.EpisodeTasks.find_one({"_id": ObjectId(task_id)})

        if not task:
            return jsonify({"error": "Task not found"}), 404

        if task["userid"] != str(g.user_id):
            return jsonify({"error": "Permission denied"}), 403

        result = collection.database.EpisodeTasks.delete_one({"_id": ObjectId(task_id)})

        if result.deleted_count == 1:
            return jsonify({"message": "Task deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete task"}), 500

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to delete task: {str(e)}"}), 500
