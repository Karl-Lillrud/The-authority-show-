import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional
from pydantic import BaseModel, Field, ValidationError

from backend.database.mongo_connection import collection

logger = logging.getLogger(__name__)

# Define Pydantic model for Comment
class Comment(BaseModel):
    id: Optional[str] = Field(default=None) # Removed alias="id"
    userId: str
    podtaskId: str # Assuming this is the correct linking field based on add_comment
    content: str # Assuming 'text' field from original is 'content' here, or vice-versa
    userName: Optional[str] = None # Added from add_comment logic
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: Optional[datetime] = None
    text: Optional[str] = None # From original add_comment, if different from content


class CommentRepository:
    
    def __init__(self):
        """Initialize collections from database."""
        self.comments_collection = collection.database.Comments
        self.podtasks_collection = collection.database.Podtasks # Assuming this is used for podtaskId validation
        self.users_collection = collection.database.Users
    
    def add_comment(self, user_id: str, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        try:
            data["userId"] = str(user_id) # Ensure userId is part of data for Pydantic model
            if "text" in data and "content" not in data: # Map text to content if that's the model field
                data["content"] = data["text"]
            
            # Validate data using Pydantic model
            validated_comment = Comment(**data)
            
            # Verify the podtask exists
            podtask_id_val = validated_comment.podtaskId # Renamed podtask_id to podtask_id_val
            podtask = self.podtasks_collection.find_one({"id": podtask_id_val}) # Query by id
            if not podtask:
                logger.warning(f"Podtask not found: {podtask_id_val}")
                return {"error": "Podtask not found"}, 404
            
            # Try to get user name from users collection
            user = self.users_collection.find_one({"id": str(user_id)}) # Query by id
            if user:
                validated_comment.userName = user.get("fullName") or user.get("full_name") or user.get("name") or "Unknown User"
            
            comment_document = validated_comment.dict(exclude_none=True) # Use exclude_none=True
            
            # Ensure 'id' is set if not provided by model default (e.g. if it's not optional or no factory)
            if "id" not in comment_document or not comment_document["id"]:
                 comment_document["id"] = str(uuid.uuid4())
            
            # Insert into database
            result = self.comments_collection.insert_one(comment_document)
            
            if result.inserted_id: # inserted_id will be the value of the 'id' field
                comment_id_inserted = comment_document["id"]
                logger.info(f"Successfully added comment with ID: {comment_id_inserted}")
                
                self.podtasks_collection.update_one(
                    {"id": podtask_id_val}, # Query by id
                    {"$push": {"comments": comment_id_inserted}}
                )
                
                # Prepare comment_document for response, ensuring 'id' is string
                comment_document_response = {**comment_document}
                comment_document_response["id"] = str(comment_document_response["id"])
                if isinstance(comment_document_response.get("createdAt"), datetime):
                    comment_document_response["createdAt"] = comment_document_response["createdAt"].isoformat()
                if isinstance(comment_document_response.get("updatedAt"), datetime):
                    comment_document_response["updatedAt"] = comment_document_response["updatedAt"].isoformat()


                return {
                    "message": "Comment added successfully", 
                    "comment_id": comment_id_inserted,
                    "comment": comment_document_response
                }, 201
            else:
                logger.error("Database insert returned without error but no ID was created")
                return {"error": "Failed to add comment"}, 500
                
        except ValidationError as err: # Pydantic's ValidationError
            logger.warning(f"Validation error during comment creation: {err.errors()}")
            return {"error": "Invalid data", "details": err.errors()}, 400
        except Exception as e:
            logger.error(f"Error adding comment: {e}", exc_info=True)
            return {"error": f"Failed to add comment: {str(e)}"}, 500
    
    def get_comments_by_podtask(self, user_id: str, podtask_id: str) -> Tuple[Dict[str, Any], int]:
        try:
            podtask = self.podtasks_collection.find_one({"id": podtask_id}) # Query by id
            if not podtask:
                logger.warning(f"Podtask not found: {podtask_id}")
                return {"error": "Podtask not found"}, 404
            
            # Add user access check if podtask is user-specific
            # if podtask.get("userid") != str(user_id):
            #     logger.warning(f"User {user_id} does not have access to podtask {podtask_id}")
            #     return {"error": "Permission denied"}, 403

            comments_cursor = list(self.comments_collection.find({"podtaskId": podtask_id}).sort("createdAt", 1))
            
            for comment_item in comments_cursor: # Renamed comment to comment_item
                if "id" in comment_item and "id" not in comment_item: # Handle if DB still has _id
                    comment_item["id"] = str(comment_item.pop("id"))
                elif "id" in comment_item:
                    comment_item["id"] = str(comment_item["id"])
                
                if "createdAt" in comment_item and isinstance(comment_item["createdAt"], datetime):
                    comment_item["createdAt"] = comment_item["createdAt"].isoformat()
                if "updatedAt" in comment_item and isinstance(comment_item["updatedAt"], datetime):
                    comment_item["updatedAt"] = comment_item["updatedAt"].isoformat()
            
            logger.info(f"Retrieved {len(comments_cursor)} comments for podtask {podtask_id}")
            return {"comments": comments_cursor}, 200
            
        except Exception as e:
            logger.error(f"Error fetching comments: {e}", exc_info=True)
            return {"error": f"Failed to fetch comments: {str(e)}"}, 500
    
    def delete_comment(self, user_id: str, comment_id: str) -> Tuple[Dict[str, Any], int]:
        try:
            comment_doc = self.comments_collection.find_one({"id": comment_id}) # Query by id, Renamed comment to comment_doc
            if not comment_doc:
                logger.warning(f"Comment not found: {comment_id}")
                return {"error": "Comment not found"}, 404
            
            if comment_doc.get("userId") != str(user_id): # Use .get for safety
                logger.warning(f"Permission denied for user {user_id} to delete comment {comment_id}")
                return {"error": "Permission denied"}, 403
            
            podtask_id_val = comment_doc.get("podtaskId") # Renamed podtask_id to podtask_id_val
            
            result = self.comments_collection.delete_one({"id": comment_id}) # Delete by id
            
            if result.deleted_count == 1:
                logger.info(f"Successfully deleted comment {comment_id}")
                
                if podtask_id_val:
                    self.podtasks_collection.update_one(
                        {"id": podtask_id_val}, # Query by id
                        {"$pull": {"comments": comment_id}}
                    )
                
                return {"message": "Comment deleted successfully"}, 200
            else:
                logger.error(f"Failed to delete comment {comment_id}")
                return {"error": "Failed to delete comment"}, 500
                
        except Exception as e:
            logger.error(f"Error deleting comment: {e}", exc_info=True)
            return {"error": f"Failed to delete comment: {str(e)}"}, 500
    
    def update_comment(self, user_id: str, comment_id: str, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        try:
            comment_doc = self.comments_collection.find_one({"id": comment_id}) # Query by id, Renamed comment to comment_doc
            if not comment_doc:
                logger.warning(f"Comment not found: {comment_id}")
                return {"error": "Comment not found"}, 404
            
            if comment_doc.get("userId") != str(user_id): # Use .get for safety
                logger.warning(f"Permission denied for user {user_id} to update comment {comment_id}")
                return {"error": "Permission denied"}, 403
            
            # Assuming 'text' or 'content' is the field to update
            update_payload = {}
            if "text" in data:
                update_payload["text"] = data["text"]
            elif "content" in data: # If model uses 'content'
                update_payload["content"] = data["content"]
            else:
                return {"error": "No text/content provided for update"}, 400
            
            update_payload["updatedAt"] = datetime.now(timezone.utc)
            
            result = self.comments_collection.update_one(
                {"id": comment_id}, # Query by id
                {"$set": update_payload}
            )
            
            if result.modified_count == 1:
                logger.info(f"Successfully updated comment {comment_id}")
                return {"message": "Comment updated successfully"}, 200
            else:
                logger.warning(f"No changes made to comment {comment_id}")
                return {"message": "No changes made to the comment"}, 200
                
        except Exception as e:
            logger.error(f"Error updating comment: {e}", exc_info=True)
            return {"error": f"Failed to update comment: {str(e)}"}, 500
