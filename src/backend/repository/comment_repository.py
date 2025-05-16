import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional

from marshmallow import ValidationError

from backend.database.mongo_connection import collection
from backend.models.comments import Comment  # Changed from CommentSchema to Comment

logger = logging.getLogger(__name__)

class CommentRepository:
    
    def __init__(self):
        """Initialize collections from database."""
        self.comments_collection = collection.database.Comments
        self.podtasks_collection = collection.database.Podtasks
        self.users_collection = collection.database.Users
    
    def add_comment(self, user_id: str, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        try:
            # Validate data using Pydantic model
            validated_comment = Comment(**data)
            validated_data = validated_comment.dict()
            
            # Verify the podtask exists
            podtask_id = validated_data.get("podtaskId")
            podtask = self.podtasks_collection.find_one({"_id": podtask_id})
            if not podtask:
                logger.warning(f"Podtask not found: {podtask_id}")
                return {"error": "Podtask not found"}, 404
            
            # Add required fields
            validated_data["userId"] = str(user_id)
            validated_data["createdAt"] = datetime.now(timezone.utc)
            
            # Try to get user name from users collection
            user = self.users_collection.find_one({"_id": str(user_id)})
            if user:
                # Handle different user name field formats
                validated_data["userName"] = user.get("fullName") or user.get("full_name") or user.get("name") or "Unknown User"
            
            # Generate unique ID for the comment
            comment_id = str(uuid.uuid4())
            
            # Create comment document
            comment_document = {
                "_id": comment_id,
                "podtaskId": validated_data.get("podtaskId"),
                "userId": validated_data.get("userId"),
                "userName": validated_data.get("userName", "Unknown User"),
                "text": validated_data.get("text", ""),
                "createdAt": validated_data.get("createdAt"),
            }
            
            # Insert into database
            result = self.comments_collection.insert_one(comment_document)
            
            if result.inserted_id:
                logger.info(f"Successfully added comment with ID: {comment_id}")
                
                # Update the podtask to include this comment reference
                self.podtasks_collection.update_one(
                    {"_id": podtask_id},
                    {"$push": {"comments": comment_id}}
                )
                
                return {
                    "message": "Comment added successfully", 
                    "comment_id": comment_id,
                    "comment": comment_document
                }, 201
            else:
                logger.error("Database insert returned without error but no ID was created")
                return {"error": "Failed to add comment"}, 500
                
        except ValidationError as err:
            logger.warning(f"Validation error during comment creation: {err.messages}")
            return {"error": "Invalid data", "details": err.messages}, 400
        except Exception as e:
            logger.error(f"Error adding comment: {e}", exc_info=True)
            return {"error": f"Failed to add comment: {str(e)}"}, 500
    
    def get_comments_by_podtask(self, user_id: str, podtask_id: str) -> Tuple[Dict[str, Any], int]:
        try:
            # Verify the podtask exists and user has access
            podtask = self.podtasks_collection.find_one({"_id": podtask_id})
            if not podtask:
                logger.warning(f"Podtask not found: {podtask_id}")
                return {"error": "Podtask not found"}, 404
            
            # Find all comments for this podtask
            comments = list(self.comments_collection.find({"podtaskId": podtask_id}).sort("createdAt", 1))
            
            for comment in comments:
                comment["_id"] = str(comment["_id"])
                # Format dates for frontend
                if "createdAt" in comment:
                    comment["createdAt"] = comment["createdAt"].isoformat()
                if "updatedAt" in comment and comment["updatedAt"]:
                    comment["updatedAt"] = comment["updatedAt"].isoformat()
            
            logger.info(f"Retrieved {len(comments)} comments for podtask {podtask_id}")
            return {"comments": comments}, 200
            
        except Exception as e:
            logger.error(f"Error fetching comments: {e}", exc_info=True)
            return {"error": f"Failed to fetch comments: {str(e)}"}, 500
    
    def delete_comment(self, user_id: str, comment_id: str) -> Tuple[Dict[str, Any], int]:
        try:
            # Find comment
            comment = self.comments_collection.find_one({"_id": comment_id})
            if not comment:
                logger.warning(f"Comment not found: {comment_id}")
                return {"error": "Comment not found"}, 404
            
            # Verify ownership
            if comment["userId"] != str(user_id):
                logger.warning(f"Permission denied for user {user_id} to delete comment {comment_id}")
                return {"error": "Permission denied"}, 403
            
            # Get the podtask ID before deleting the comment
            podtask_id = comment.get("podtaskId")
            
            # Delete the comment
            result = self.comments_collection.delete_one({"_id": comment_id})
            
            if result.deleted_count == 1:
                logger.info(f"Successfully deleted comment {comment_id}")
                
                # Remove the comment reference from the podtask
                if podtask_id:
                    self.podtasks_collection.update_one(
                        {"_id": podtask_id},
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
            # Find comment
            comment = self.comments_collection.find_one({"_id": comment_id})
            if not comment:
                logger.warning(f"Comment not found: {comment_id}")
                return {"error": "Comment not found"}, 404
            
            # Verify ownership
            if comment["userId"] != str(user_id):
                logger.warning(f"Permission denied for user {user_id} to update comment {comment_id}")
                return {"error": "Permission denied"}, 403
            
            # Only allow updating the text field
            if "text" not in data:
                return {"error": "No text provided for update"}, 400
            
            # Update the comment
            update_data = {
                "text": data["text"],
                "updatedAt": datetime.now(timezone.utc)
            }
            
            result = self.comments_collection.update_one(
                {"_id": comment_id},
                {"$set": update_data}
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
