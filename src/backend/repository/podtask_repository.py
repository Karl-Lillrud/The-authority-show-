import logging
import uuid
from datetime import datetime, timezone
from backend.database.mongo_connection import collection
from backend.models.podtasks import PodtaskSchema
from marshmallow import ValidationError

logger = logging.getLogger(__name__)

class PodtaskRepository:
    def __init__(self):
        self.podtasks_collection = collection.database.Podtasks
        self.accounts_collection = collection.database.Accounts
        self.podcasts_collection = collection.database.Podcasts

    def register_podtask(self, user_id, data):
        try:
            schema = PodtaskSchema()
            validated_data = schema.load(data)

            user_accounts = list(self.accounts_collection.find({"userId": str(user_id)}, {"_id": 1}))
            if not user_accounts:
                return {"error": "No accounts found for user"}, 403

            user_account_ids = [str(account["_id"]) for account in user_accounts]

            podcasts = list(self.podcasts_collection.find({"accountId": {"$in": user_account_ids}}))
            if not podcasts:
                return {"error": "No podcasts found for user"}, 404

            selected_podcast = podcasts[0]
            podcast_id = str(selected_podcast["_id"])

            validated_data["podcastId"] = podcast_id
            validated_data["userid"] = str(user_id)
            validated_data["created_at"] = datetime.now(timezone.utc)

            podtask_id = str(uuid.uuid4())

            podtask_document = {
                "_id": podtask_id,
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
                "userid": validated_data["userid"],
                "created_at": validated_data["created_at"],
            }

            result = self.podtasks_collection.insert_one(podtask_document)
            if result.inserted_id:
                return {"message": "Podtask registered successfully", "podtask_id": podtask_id}, 201
            else:
                return {"error": "Failed to register podtask"}, 500

        except ValidationError as err:
            return {"error": "Invalid data", "details": err.messages}, 400
        except Exception as e:
            logger.error(f"Error registering podtask: {e}", exc_info=True)
            return {"error": f"Failed to register podtask: {str(e)}"}, 500

    def get_podtasks(self, user_id):
        try:
            podtasks = list(self.podtasks_collection.find({"userid": str(user_id)}))

            for task in podtasks:
                task["_id"] = str(task["_id"])

            return {"podtasks": podtasks}, 200

        except Exception as e:
            logger.error(f"Error fetching podtasks: {e}", exc_info=True)
            return {"error": f"Failed to fetch tasks: {str(e)}"}, 500

    def delete_podtask(self, user_id, task_id):
        try:
            task = self.podtasks_collection.find_one({"_id": task_id})
            if not task:
                return {"error": "Task not found"}, 404

            if task["userid"] != str(user_id):
                return {"error": "Permission denied"}, 403

            result = self.podtasks_collection.delete_one({"_id": task_id})
            if result.deleted_count == 1:
                return {"message": "Task deleted successfully"}, 200
            else:
                return {"error": "Failed to delete task"}, 500

        except Exception as e:
            logger.error(f"Error deleting podtask: {e}", exc_info=True)
            return {"error": f"Failed to delete task: {str(e)}"}, 500

    def update_podtask(self, user_id, task_id, data):
        try:
            existing_task = self.podtasks_collection.find_one({"_id": task_id})
            if not existing_task:
                return {"error": "Task not found"}, 404

            if existing_task["userid"] != str(user_id):
                return {"error": "Permission denied"}, 403

            update_fields = {
                "name": data.get("taskname", existing_task.get("name", "")).strip(),
                "description": data.get("Description", existing_task.get("description", "")).strip(),
                "dayCount": data.get("DayCount", existing_task.get("dayCount")),
                "action": data.get("action", existing_task.get("action", [])),
                "actionUrl": data.get("actionurl", existing_task.get("actionUrl", "")).strip(),
                "urlDescribe": data.get("externalurl", existing_task.get("urlDescribe", "")).strip(),
                "submissionReq": True if data.get("submission", "Optional") == "Required" else False,
                "updated_at": datetime.now(timezone.utc),
            }

            result = self.podtasks_collection.update_one({"_id": task_id}, {"$set": update_fields})

            if result.modified_count == 1:
                return {"message": "Task updated successfully"}, 200
            else:
                return {"message": "No changes made to the task"}, 200

        except Exception as e:
            logger.error(f"Error updating podtask: {e}", exc_info=True)
            return {"error": f"Failed to update task: {str(e)}"}, 500

    
    def delete_by_user(self, user_id):
        try:
            result = self.podtasks_collection.delete_many({"userid": str(user_id)})
            logger.info(f"🧹 Deleted {result.deleted_count} podtasks for user {user_id}")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to delete podtasks: {e}", exc_info=True)
            return 0
