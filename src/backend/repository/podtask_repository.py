import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional, Union

from pydantic import BaseModel, Field, ValidationError

from backend.database.mongo_connection import collection
from backend.services.taskService import extract_highlights, process_default_tasks

logger = logging.getLogger(__name__)

# Define Pydantic model for PodTask
class PodTask(BaseModel): # Renamed from Podtask to PodTask for convention
    id: Optional[str] = Field(default=None) # Removed alias="id"
    title: str # Assuming title was 'name' or similar, adjust if Podtask model is different
    description: Optional[str] = None
    status: str # Assuming status was part of the model
    assignedTo: Optional[List[str]] = None # Assuming assignedTo was 'members'
    dueDate: Optional[datetime] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow) # Was 'created_at'
    updatedAt: Optional[datetime] = None
    tags: Optional[List[str]] = None # Assuming tags was 'highlights' or similar
    metadata: Optional[Dict] = None # For other fields like podcastId, episodeId etc.

    # Add other fields from the original _create_podtask_document method
    podcastId: Optional[str] = None
    episodeId: Optional[str] = None
    teamId: Optional[str] = None
    members: Optional[List[str]] = Field(default_factory=list) # from assignedTo or members
    guestId: Optional[str] = None
    action: Optional[List[str]] = Field(default_factory=list)
    dayCount: Optional[int] = None
    actionUrl: Optional[str] = None
    urlDescribe: Optional[str] = None
    submissionReq: Optional[bool] = False
    priority: Optional[str] = "medium"
    userid: Optional[str] = None # from validated_data["userid"]
    highlights: Optional[List[str]] = Field(default_factory=list) # from validated_data["highlights"]
    dependencies: Optional[List[str]] = Field(default_factory=list)
    aiTool: Optional[str] = None
    completed_at: Optional[datetime] = None


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
            # Assign podcast ID if missing
            if not data.get("podcastId"):
                podcast_result = self._get_default_podcast_id(user_id)
                if isinstance(podcast_result, tuple):  # Error occurred
                    return podcast_result
                data["podcastId"] = podcast_result

            data["userid"] = str(user_id) # Ensure userid is set before Pydantic validation
            data["title"] = data.get("name", data.get("title", "Untitled Task")) # Map name to title

            # Validate data through Pydantic model
            validated_task = PodTask(**data)
            
            # Process optional data
            task_data_dict = validated_task.dict(exclude_none=True) # Use exclude_none=True
            
            # Ensure 'name' is not in the final dict if 'title' is used by the model
            if "name" in task_data_dict and "title" in task_data_dict and task_data_dict["name"] == task_data_dict["title"]:
                del task_data_dict["name"]

            task_data_dict = process_default_tasks(task_data_dict) # process_default_tasks might need adjustment
            
            # Extract highlights if description exists
            if description := task_data_dict.get("description"):
                task_data_dict["highlights"] = extract_highlights(description)
            
            # Generate unique ID for the podtask if not provided
            if "id" not in task_data_dict or not task_data_dict["id"]:
                task_data_dict["id"] = str(uuid.uuid4())
            
            # Insert into database
            result = self.podtasks_collection.insert_one(task_data_dict)
            
            if result.inserted_id:
                # Use the id from task_data_dict as it's the one inserted
                podtask_id_inserted = task_data_dict["id"]
                logger.info(f"Successfully registered podtask with ID: {podtask_id_inserted}")
                return {"message": "Podtask registered successfully", "podtask_id": podtask_id_inserted}, 201
            else:
                logger.error("Database insert returned without error but no ID was created")
                return {"error": "Failed to register podtask"}, 500
                
        except ValidationError as err:
            logger.warning(f"Validation error during podtask registration: {err.errors()}")
            return {"error": "Invalid data", "details": err.errors()}, 400
        except Exception as e:
            logger.error(f"Error registering podtask: {e}", exc_info=True)
            return {"error": f"Failed to register podtask: {str(e)}"}, 500
    
    def _get_default_podcast_id(self, user_id: str) -> Union[str, Tuple[Dict[str, Any], int]]:
        user_accounts = list(self.accounts_collection.find({"ownerId": str(user_id)}, {"id": 1}))
        if not user_accounts:
            logger.warning(f"No accounts found for user {user_id}")
            return {"error": "No accounts found for user"}, 403

        user_account_ids = [str(account["id"]) for account in user_accounts]
        podcasts = list(self.podcasts_collection.find({"accountId": {"$in": user_account_ids}}))
        if not podcasts:
            logger.warning(f"No podcasts found for user accounts: {user_account_ids}")
            return {"error": "No podcasts found for user"}, 404

        return str(podcasts[0]["id"])
    
    def _create_podtask_document(self, podtask_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        # This method might become obsolete if Pydantic model is comprehensive
        # For now, ensure it uses "id"
        doc = {
            "id": podtask_id,
            "podcastId": data.get("podcastId"),
            "episodeId": data.get("episodeId"),
            "teamId": data.get("teamId"),
            "members": data.get("members", data.get("assignedTo", [])), # map members or assignedTo
            "guestId": data.get("guestId"),
            "title": data.get("name", data.get("title", "")), # map name to title
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
            "userid": data.get("userid"), # Ensure userid is present
            "createdAt": data.get("createdAt", data.get("created_at")), # map created_at
            "highlights": data.get("highlights", []),
            "dependencies": data.get("dependencies", []),
            "aiTool": data.get("aiTool", ""),
        }
        if "name" in doc and "title" in doc and doc["name"] == doc["title"]:
             del doc["name"] # Avoid duplicate field if name was mapped to title
        return doc


    def get_podtasks(self, user_id: str, filters: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], int]:
        try:
            query = {"userid": str(user_id)}
            
            if filters:
                for key, value in filters.items():
                    if key in ["status", "priority", "teamId", "episodeId", "podcastId"]:
                        query[key] = value
            
            podtasks_cursor = list(self.podtasks_collection.find(query))
            # Convert MongoDB _id to id for Pydantic compatibility if needed, or ensure DB stores as id
            for task in podtasks_cursor:
                if "id" in task and "id" not in task: # If DB still has _id
                    task["id"] = str(task.pop("id"))
                elif "id" in task:
                    task["id"] = str(task["id"])


            logger.info(f"Retrieved {len(podtasks_cursor)} podtasks for user {user_id}")
            return {"podtasks": podtasks_cursor}, 200

        except Exception as e:
            logger.error(f"Error fetching podtasks: {e}", exc_info=True)
            return {"error": f"Failed to fetch tasks: {str(e)}"}, 500

    def get_podtask_by_id(self, user_id: str, task_id: str) -> Tuple[Dict[str, Any], int]:
        try:
            task = self.podtasks_collection.find_one({"id": task_id}) # Query by id
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return {"error": "Task not found"}, 404

            if task.get("userid") != str(user_id): # Use .get for safety
                logger.warning(f"Permission denied for user {user_id} to access task {task_id}")
                return {"error": "Permission denied"}, 403
            
            if "id" in task and "id" not in task: # If DB still has _id
                task["id"] = str(task.pop("id"))
            elif "id" in task:
                task["id"] = str(task["id"])


            return {"podtask": task}, 200

        except Exception as e:
            logger.error(f"Error fetching podtask {task_id}: {e}", exc_info=True)
            return {"error": f"Failed to fetch task: {str(e)}"}, 500


    def delete_podtask(self, user_id: str, task_id: str) -> Tuple[Dict[str, Any], int]:
        try:
            task = self.podtasks_collection.find_one({"id": task_id}) # Query by id
            if not task:
                logger.warning(f"Task not found for deletion: {task_id}")
                return {"error": "Task not found"}, 404

            if task.get("userid") != str(user_id): # Use .get for safety
                logger.warning(f"Permission denied for user {user_id} to delete task {task_id}")
                return {"error": "Permission denied"}, 403

            result = self.podtasks_collection.delete_one({"id": task_id}) # Delete by id
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

            task = self.podtasks_collection.find_one({"id": task_id}) # Query by id
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return {"error": "Task not found"}, 404

            if task.get("userid") != str(user_id): # Use .get for safety
                logger.warning(f"Permission denied for user {user_id} on task {task_id}")
                return {"error": "Permission denied"}, 403

            # Map 'name' to 'title' if present in incoming data for Pydantic model
            if "name" in data and "title" not in data:
                data["title"] = data.pop("name")

            # Create a Pydantic model instance with existing task data, then update with new data
            # This ensures validation and proper field handling
            updated_values = {**task, **data}
            # Pydantic needs string id, ensure it is if coming from DB as ObjectId initially
            if "id" in updated_values: # if task from DB had _id
                 updated_values["id"] = str(updated_values.pop("id"))
            elif "id" in updated_values and not isinstance(updated_values["id"], str):
                 updated_values["id"] = str(updated_values["id"])


            validated_update = PodTask(**updated_values)
            update_fields = validated_update.dict(exclude_unset=True, exclude_none=True)
            
            # Specific logic from _prepare_update_fields
            description = update_fields.get("description", task.get("description", ""))
            if description and description != task.get("description"):
                 update_fields["highlights"] = extract_highlights(description)

            if update_fields.get("status") == "completed" and task.get("status") != "completed":
                update_fields["completed_at"] = datetime.now(timezone.utc)
            
            update_fields["updatedAt"] = datetime.now(timezone.utc) # Was updated_at

            # Remove id from update_fields as it's used in query, not for $set
            if "id" in update_fields:
                del update_fields["id"]
            if "userid" in update_fields and update_fields["userid"] == task.get("userid"): # Don't update userid if same
                del update_fields["userid"]


            logger.debug(f"Update fields: {update_fields}")

            if not update_fields:
                 return {"message": "No changes made to the task"}, 200

            result = self.podtasks_collection.update_one({"id": task_id}, {"$set": update_fields}) # Update by id
            logger.debug(f"Matched: {result.matched_count}, Modified: {result.modified_count}")

            message = "Task updated successfully" if result.modified_count else "No changes made to the task"
            return {"message": message}, 200
        
        except ValidationError as err:
            logger.warning(f"Validation error during podtask update: {err.errors()}")
            return {"error": "Invalid data", "details": err.errors()}, 400
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}", exc_info=True)
            return {"error": f"Failed to update task: {str(e)}"}, 500

    def _prepare_update_fields(self, existing_task: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        # This method logic is now integrated into update_podtask using Pydantic
        pass


    def bulk_update_status(self, user_id: str, task_ids: List[str], new_status: str) -> Tuple[Dict[str, Any], int]:
        try:
            tasks = list(self.podtasks_collection.find({"id": {"$in": task_ids}})) # Query by id
            if len(tasks) != len(task_ids):
                # Find which tasks were not found
                found_ids = {str(task.get("id", task.get("id"))) for task in tasks}
                missing_ids = [tid for tid in task_ids if tid not in found_ids]
                logger.warning(f"One or more tasks not found: {missing_ids}")
                return {"error": f"One or more tasks not found: {', '.join(missing_ids)}"}, 404
                    
            for task in tasks:
                if task.get("userid") != str(user_id): # Use .get for safety
                    return {"error": "Permission denied for one or more tasks"}, 403
                
            update_data = {
                "status": new_status,
                "updatedAt": datetime.now(timezone.utc) # Was updated_at
            }
                
            if new_status == "completed":
                update_data["completed_at"] = datetime.now(timezone.utc)
                
            result = self.podtasks_collection.update_many(
                {"id": {"$in": task_ids}}, # Update by id
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
            episode = self.episodes_collection.find_one({"id": episode_id}) # Query by id
            if not episode:
                return {"error": "Episode not found"}, 404
            podcastId = episode.get("podcastId")
            if not podcastId:
                return {"error": "Episode missing podcastId"}, 400

            inserted_count = 0
            inserted_ids = []
            for task_data in tasks: # Renamed task to task_data
                task_data["podcastId"] = podcastId
                task_data["episodeId"] = episode_id
                task_data["guestId"] = guest_id
                task_data["userid"] = str(user_id)
                task_data["createdAt"] = datetime.now(timezone.utc) # Was created_at
                
                if "title" not in task_data and "name" in task_data: # Map name to title for Pydantic
                    task_data["title"] = task_data.pop("name")
                elif "title" not in task_data:
                    task_data["title"] = "Untitled Task"


                try:
                    validated_task = PodTask(**task_data)
                    task_document_to_insert = validated_task.dict(exclude_none=True)
                    if "id" not in task_document_to_insert or not task_document_to_insert["id"]:
                        task_document_to_insert["id"] = str(uuid.uuid4())

                    # process_default_tasks might need to be called on task_document_to_insert
                    task_document_to_insert = process_default_tasks(task_document_to_insert)


                    result = self.podtasks_collection.insert_one(task_document_to_insert)
                    if result.inserted_id:
                        inserted_count += 1
                        inserted_ids.append(task_document_to_insert["id"])
                except ValidationError as err:
                    logger.error(f"Validation error for task data {task_data}: {err.errors()}")
                    # Optionally skip this task or return an error for the whole batch
                    return {"error": f"Invalid task data: {err.errors()}"}, 400

            if inserted_count > 0:
                return {"message": f"Added {inserted_count} tasks", "task_ids": inserted_ids}, 201
            else:
                return {"error": "No tasks were added"}, 500
        except Exception as e:
            logger.error(f"Error adding tasks to episode: {e}", exc_info=True)
            return {"error": str(e)}, 500
            
            
    def add_default_tasks_to_episode(self, user_id: str, episode_id: str, default_tasks: list) -> Tuple[Dict[str, Any], int]:
        try:
            episode = self.episodes_collection.find_one({"id": episode_id}) # Query by id
            if not episode:
                return {"error": "Episode not found"}, 404

            podcastId = episode.get("podcastId") or episode.get("podcast_id") # Keep podcast_id for backward compatibility
            if not podcastId:
                return {"error": "Episode missing podcastId"}, 400

            inserted_count = 0
            inserted_ids = []

            for task_name_str in default_tasks: # Renamed task_name to task_name_str
                task_data_item = { # Renamed task to task_data_item
                    "title": task_name_str, # Use title for Pydantic model
                    "podcastId": podcastId,
                    "episodeId": episode_id,
                    "userid": str(user_id),
                    "createdAt": datetime.now(timezone.utc), # Was created_at
                    "status": "pending",
                }
                try:
                    validated_task = PodTask(**task_data_item)
                    task_document_to_insert = validated_task.dict(exclude_none=True)
                    if "id" not in task_document_to_insert or not task_document_to_insert["id"]:
                         task_document_to_insert["id"] = str(uuid.uuid4())
                    
                    # process_default_tasks might need to be called on task_document_to_insert
                    task_document_to_insert = process_default_tasks(task_document_to_insert)

                    result = self.podtasks_collection.insert_one(task_document_to_insert)
                    if result.inserted_id:
                        inserted_count += 1
                        inserted_ids.append(task_document_to_insert["id"])
                except ValidationError as err:
                    logger.error(f"Validation error for default task {task_name_str}: {err.errors()}")
                    # Optionally skip or handle error
                    continue


            if inserted_count > 0:
                return {"message": f"Added {inserted_count} default tasks", "task_ids": inserted_ids}, 201
            else:
                return {"error": "No default tasks were added"}, 500
        except Exception as e:
            logger.error(f"Error adding default tasks to episode: {e}", exc_info=True)
            return {"error": str(e)}, 500
