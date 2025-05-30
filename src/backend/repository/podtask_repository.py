import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional, Union

from marshmallow import ValidationError

from backend.database.mongo_connection import collection
from backend.models.podtasks import PodtaskSchema  
from backend.services.taskService import extract_highlights, process_default_tasks

logger = logging.getLogger(__name__)


class PodtaskRepository:
    
    def __init__(self):
        """Initialize collections from database."""
        self.podtasks_collection = collection.database.Podtasks
        self.accounts_collection = collection.database.Accounts
        self.podcasts_collection = collection.database.Podcasts
        self.users_collection = collection.database.Users
        self.episodes_collection = collection.database.Episodes
    
    def register_podtask(self, user_id: str, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        try:
            # Validate data through schema
            schema = PodtaskSchema()
            validated_data = schema.load(data)
            
            # Assign podcast ID if missing
            if not validated_data.get("podcastId"):
                podcast_result = self._get_default_podcast_id(user_id)
                if isinstance(podcast_result, tuple):  # Error occurred
                    return podcast_result
                validated_data["podcastId"] = podcast_result

            # Add required fields
            validated_data["userid"] = str(user_id)
            validated_data["created_at"] = datetime.now(timezone.utc)
            
            # Process optional data
            validated_data = process_default_tasks(validated_data)
            
            # Extract highlights if description exists
            if description := validated_data.get("description"):
                validated_data["highlights"] = extract_highlights(description)
            
            # Generate unique ID for the podtask
            podtask_id = str(uuid.uuid4())
            
            # Create podtask document
            podtask_document = self._create_podtask_document(podtask_id, validated_data)
            
            # Insert into database
            result = self.podtasks_collection.insert_one(podtask_document)
            
            if result.inserted_id:
                logger.info(f"Successfully registered podtask with ID: {podtask_id}")
                return {"message": "Podtask registered successfully", "podtask_id": podtask_id}, 201
            else:
                logger.error("Database insert returned without error but no ID was created")
                return {"error": "Failed to register podtask"}, 500
                
        except ValidationError as err:
            logger.warning(f"Validation error during podtask registration: {err.messages}")
            return {"error": "Invalid data", "details": err.messages}, 400
        except Exception as e:
            logger.error(f"Error registering podtask: {e}", exc_info=True)
            return {"error": f"Failed to register podtask: {str(e)}"}, 500
    
    def _get_default_podcast_id(self, user_id: str) -> Union[str, Tuple[Dict[str, Any], int]]:
        user_accounts = list(self.accounts_collection.find({"ownerId": str(user_id)}, {"_id": 1}))
        if not user_accounts:
            logger.warning(f"No accounts found for user {user_id}")
            return {"error": "No accounts found for user"}, 403

        user_account_ids = [str(account["_id"]) for account in user_accounts]
        podcasts = list(self.podcasts_collection.find({"accountId": {"$in": user_account_ids}}))
        if not podcasts:
            logger.warning(f"No podcasts found for user accounts: {user_account_ids}")
            return {"error": "No podcasts found for user"}, 404

        return str(podcasts[0]["_id"])
    
    def _create_podtask_document(self, podtask_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "_id": podtask_id,
            "podcastId": data.get("podcastId"),
            "episodeId": data.get("episodeId"),
            "teamId": data.get("teamId"),
            "members": data.get("members", []),
            "guestId": data.get("guestId"),
            "name": data.get("name", ""),
            "action": data.get("action", []),
            "dayCount": data.get("dayCount"),
            "description": data.get("description", ""),
            "actionUrl": data.get("actionUrl", ""),
            "urlDescribe": data.get("urlDescribe", ""),
            "submissionReq": data.get("submissionReq", False),
            "status": data.get("status", "pending"),
            "assignedAt": data.get("assignedAt"),
            "dueDate": data.get("dueDate"),
            "priority": data.get("priority", "medium"),
            "userid": data["userid"],
            "created_at": data["created_at"],
            "highlights": data.get("highlights", []),
            "dependencies": data.get("dependencies", []),
            "aiTool": data.get("aiTool", ""),
        }

    def get_podtasks(self, user_id: str, filters: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], int]:
        try:
            # Create base query
            query = {"userid": str(user_id)}
            
            # Add any additional filters
            if filters:
                for key, value in filters.items():
                    if key in ["status", "priority", "teamId", "episodeId", "podcastId"]:
                        query[key] = value
            
            # Execute query
            podtasks = list(self.podtasks_collection.find(query))

            logger.info(f"Retrieved {len(podtasks)} podtasks for user {user_id}")
            return {"podtasks": podtasks}, 200

        except Exception as e:
            logger.error(f"Error fetching podtasks: {e}", exc_info=True)
            return {"error": f"Failed to fetch tasks: {str(e)}"}, 500

    def get_podtask_by_id(self, user_id: str, task_id: str) -> Tuple[Dict[str, Any], int]:
        try:
            # Find task
            task = self.podtasks_collection.find_one({"_id": task_id})
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return {"error": "Task not found"}, 404

            # Verify ownership
            if task["userid"] != str(user_id):
                logger.warning(f"Permission denied for user {user_id} to access task {task_id}")
                return {"error": "Permission denied"}, 403

            return {"podtask": task}, 200

        except Exception as e:
            logger.error(f"Error fetching podtask {task_id}: {e}", exc_info=True)
            return {"error": f"Failed to fetch task: {str(e)}"}, 500


    def delete_podtask(self, user_id: str, task_id: str) -> Tuple[Dict[str, Any], int]:
        try:
            # Find and verify ownership
            task = self.podtasks_collection.find_one({"_id": task_id})
            if not task:
                logger.warning(f"Task not found for deletion: {task_id}")
                return {"error": "Task not found"}, 404

            if task["userid"] != str(user_id):
                logger.warning(f"Permission denied for user {user_id} to delete task {task_id}")
                return {"error": "Permission denied"}, 403

            # Delete the task
            result = self.podtasks_collection.delete_one({"_id": task_id})
            if result.deleted_count == 1:
                logger.info(f"Successfully deleted task {task_id}")
                return {"message": "Task deleted successfully"}, 200
            else:
                logger.error(f"Failed to delete task {task_id}, delete_count: {result.deleted_count}")
                return {"error": "Failed to delete task"}, 500

        except Exception as e:
            logger.error(f"Error deleting podtask {task_id}: {e}", exc_info=True)
            return {"error": f"Failed to delete task: {str(e)}"}, 500

    def update_podtask(self, user_id: str, task_id: str, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        try:
            logger.info(f"Request to update task {task_id} by user {user_id}")
            logger.debug(f"Incoming data: {data}")

            task = self.podtasks_collection.find_one({"_id": task_id})
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return {"error": "Task not found"}, 404

            if task["userid"] != str(user_id):
                logger.warning(f"Permission denied for user {user_id} on task {task_id}")
                return {"error": "Permission denied"}, 403

            update_fields = self._prepare_update_fields(task, data)
            logger.debug(f"Update fields: {update_fields}")

            result = self.podtasks_collection.update_one({"_id": task_id}, {"$set": update_fields})
            logger.debug(f"Matched: {result.matched_count}, Modified: {result.modified_count}")

            message = "Task updated successfully" if result.modified_count else "No changes made to the task"
            return {"message": message}, 200

        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}", exc_info=True)
            return {"error": f"Failed to update task: {str(e)}"}, 500

    def _prepare_update_fields(self, existing_task: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        description = data.get("description", existing_task.get("description", "")).strip()
        highlights = extract_highlights(description) if description and description != existing_task.get("description") else None

        fields = [
            "podcastId", "episodeId", "teamId", "members", "guestId", "name", "action",
            "dayCount", "description", "actionUrl", "urlDescribe", "submissionReq",
            "status", "assignedAt", "dueDate", "priority", "highlights", "dependencies", "aiTool"
        ]

        update_fields = {
            field: data[field] if field in data else existing_task.get(field)
            for field in fields
        }

        if highlights is not None:
            update_fields["highlights"] = highlights

        if data.get("status") == "completed" and existing_task.get("status") != "completed":
            update_fields["completed_at"] = datetime.now(timezone.utc)

        update_fields["updated_at"] = datetime.now(timezone.utc)
        return update_fields

    def bulk_update_status(self, user_id: str, task_ids: List[str], new_status: str) -> Tuple[Dict[str, Any], int]:
        try:
            # Verify all tasks exist and belong to the user
            tasks = list(self.podtasks_collection.find({"_id": {"$in": task_ids}}))
            if len(tasks) != len(task_ids):
                return {"error": "One or more tasks not found"}, 404
                    
            for task in tasks:
                if task["userid"] != str(user_id):
                    return {"error": "Permission denied for one or more tasks"}, 403
                
            # Prepare update data
            update_data = {
                "status": new_status,
                "updated_at": datetime.now(timezone.utc)
            }
                
            # Add completion timestamp if status is "completed"
            if new_status == "completed":
                update_data["completed_at"] = datetime.now(timezone.utc)
                
            # Perform bulk update
            result = self.podtasks_collection.update_many(
                {"_id": {"$in": task_ids}},
                {"$set": update_data}
            )
                
            return {
                "message": f"Updated {result.modified_count} tasks",
                "modified_count": result.modified_count
            }, 200
                
        except Exception as e:
            logger.error(f"Error in bulk status update: {e}", exc_info=True)
            return {"error": f"Failed to update tasks: {str(e)}"}, 500

    def add_tasks_to_episode(self, user_id: str, episode_id: str, guest_id: str, tasks: list) -> Tuple[Dict[str, Any], int]:
        try:
            # Lookup the episode to retrieve its podcastId
            episode = self.episodes_collection.find_one({"_id": episode_id})
            if not episode:
                return {"error": "Episode not found"}, 404
            podcastId = episode.get("podcastId")
            if not podcastId:
                return {"error": "Episode missing podcastId"}, 400

            inserted_count = 0
            inserted_ids = []
            for task in tasks:
                # Set keys to ensure correct associations
                task["podcastId"] = podcastId
                task["episodeId"] = episode_id
                task["guestId"] = guest_id
                task["userid"] = str(user_id)
                task["created_at"] = datetime.now(timezone.utc)
                # Convert 'title' to 'name' if provided
                if "title" in task:
                    task["name"] = task.pop("title")
                # Optionally process defaults if needed
                task = process_default_tasks(task)
                # Generate a unique id for each task
                podtask_id = str(uuid.uuid4())
                task_document = self._create_podtask_document(podtask_id, task)
                result = self.podtasks_collection.insert_one(task_document)
                if result.inserted_id:
                    inserted_count += 1
                    inserted_ids.append(podtask_id)
            if inserted_count > 0:
                return {"message": f"Added {inserted_count} tasks", "task_ids": inserted_ids}, 201
            else:
                return {"error": "No tasks were added"}, 500
        except Exception as e:
            return {"error": str(e)}, 500
            
            
    def add_default_tasks_to_episode(self, user_id: str, episode_id: str, default_tasks: list) -> Tuple[Dict[str, Any], int]:
        try:
            episode = self.episodes_collection.find_one({"_id": episode_id})
            if not episode:
                return {"error": "Episode not found"}, 404

            # Try both keys: podcastId and podcast_id
            podcastId = episode.get("podcastId") or episode.get("podcast_id")
            if not podcastId:
                return {"error": "Episode missing podcastId"}, 400

            inserted_count = 0
            inserted_ids = []

            for task_name in default_tasks:
                task = {
                    "name": task_name,
                    "podcastId": podcastId,
                    "episodeId": episode_id,
                    "userid": str(user_id),
                    "created_at": datetime.now(timezone.utc),
                    "status": "pending",
                }
                task = process_default_tasks(task)
                podtask_id = str(uuid.uuid4())
                task_document = self._create_podtask_document(podtask_id, task)
                result = self.podtasks_collection.insert_one(task_document)
                if result.inserted_id:
                    inserted_count += 1
                    inserted_ids.append(podtask_id)

            if inserted_count > 0:
                return {"message": f"Added {inserted_count} default tasks", "task_ids": inserted_ids}, 201
            else:
                return {"error": "No default tasks were added"}, 500
        except Exception as e:
            return {"error": str(e)}, 500

    def delete_by_user(self, user_id: str) -> int:
        """
        Delete all podtasks associated with a user.
        Args:
            user_id (str): The ID of the user whose podtasks should be deleted
        Returns:
            int: Number of podtasks deleted
        """
        try:
            result = self.podtasks_collection.delete_many({"userid": str(user_id)})
            deleted_count = result.deleted_count
            logger.info(f"Deleted {deleted_count} podtasks for user {user_id}")
            return deleted_count
        except Exception as e:
            logger.error(f"Error deleting podtasks for user {user_id}: {e}", exc_info=True)
            return 0
