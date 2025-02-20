from flask import request, jsonify, Blueprint, g
from database.mongo_connection import collection
from datetime import datetime, timezone
import uuid

# Define Blueprint
podtask_bp = Blueprint("podtask_bp", __name__)

@podtask_bp.route("/register_podtask", methods=["POST"])
def register_podtask():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Validate Content-Type
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        data = request.get_json()
        print("📩 Received Podtask Data:", data)

        podtask_id = str(uuid.uuid4())  # Generate unique ID
        user_id = str(g.user_id)  

        # Extracting data fields
        day_count = data.get("Daycount", 0)
        description = data.get("Description", "").strip()
        action = data.get("action", [])  # Expecting an array
        action_url = data.get("actionurl", "").strip()
        external_url = data.get("externalurl", "").strip()
        submission = data.get("submission", "").strip()
        task_name = data.get("taskname", "").strip()

        # Construct the podtask document
        podtask_item = {

           "_id": podtask_id,
           "podcast_id": data.get("PodcastId", "").strip(),  # Mappas om
           "userid": user_id,
           "DayCount": day_count,                             # Ändrat fältnamn
           "Description": description,
           "Action": action,
           "ActionUrl": action_url,
           "UrlDescribe": external_url,
          "SubimissionReq": True if submission == "Required" else False,
          "created_at": datetime.now(timezone.utc),
}

        # Correctly querying the User collection
        user = collection.database.User.find_one({"_id": user_id})
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Correctly inserting into the Podtask collection
        print("📝 Inserting podtask into database:", podtask_item)
        result = collection.database["Podtask"].insert_one(podtask_item)  # Ensure "Podtask" is correct

        print("✅ Podtask registered successfully!")

        return jsonify(
            {
                "message": "Podtask registered successfully",
                "podtask_id": podtask_id,  
                "redirect_url": "/index.html",
            }
        ), 201

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to register podtask: {str(e)}"}), 500

    
@podtask_bp.route("/get_podtask/<task_id>", methods=["GET"])
def get_podtask(task_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)

        # Debugging: Print task_id and user_id
        print(f"Fetching task with task_id: {task_id} for user_id: {user_id}")

        # Fetch the task using the string task_id
        task = collection.database.Podtask.find_one({"_id": task_id, "userid": user_id})

        if not task:
            print(f"Task with task_id: {task_id} and user_id: {user_id} not found.")
            return jsonify({"error": "Task not found"}), 404

        return jsonify(task), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch task: {str(e)}"}), 500


    
@podtask_bp.route("/get_podtasks", methods=["GET"])
def get_podtasks():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)  
        podtasks = list(collection.database.Podtask.find({"userid": user_id}))

        for task in podtasks:
            task["_id"] = str(task["_id"])

        return jsonify({"podtasks": podtasks}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to fetch tasks: {str(e)}"}), 500
    
@podtask_bp.route("/delete_podtask/<task_id>", methods=["DELETE"])
def delete_podtask(task_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)
        task = collection.database.Podtask.find_one({"_id": task_id})

        if not task:
            return jsonify({"error": "Task not found"}), 404

        if task["userid"] != user_id:
            return jsonify({"error": "Permission denied"}), 403

        result = collection.database.Podtask.delete_one({"_id": task_id})

        if result.deleted_count == 1:
            return jsonify({"message": "Task deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete task"}), 500

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to delete task: {str(e)}"}), 500
    
@podtask_bp.route("/update_podtask/<task_id>", methods=["PUT"])
def update_podtask(task_id):
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        data = request.get_json()
        user_id = str(g.user_id)

        existing_task = collection.database.Podtask.find_one({"_id": task_id})
        if not existing_task:
            return jsonify({"error": "Task not found"}), 404

        if existing_task["userid"] != user_id:
            return jsonify({"error": "Permission denied"}), 403

        # Fields to update (only update provided fields)
        update_fields = {
            "taskname": data.get("taskname", existing_task["taskname"]).strip(),
            "Description": data.get("Description", existing_task["Description"]).strip(),
            "Daycount": data.get("Daycount", existing_task["Daycount"]),
            "action": data.get("action", existing_task["action"]),
            "actionurl": data.get("actionurl", existing_task["actionurl"]).strip(),
            "externalurl": data.get("externalurl", existing_task["externalurl"]).strip(),
            "submission": data.get("submission", existing_task["submission"]).strip(),
            "updated_at": datetime.now(timezone.utc),
        }

        result = collection.database.Podtask.update_one(
            {"_id": task_id}, {"$set": update_fields}
        )

        if result.modified_count == 1:
            return jsonify({"message": "Task updated successfully"}), 200
        else:
            return jsonify({"message": "No changes made to the task"}), 200

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Failed to update task: {str(e)}"}), 500




