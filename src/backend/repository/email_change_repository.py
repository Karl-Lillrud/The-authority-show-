import logging
import uuid
from datetime import datetime, timedelta
from backend.database.mongo_connection import collection

logger = logging.getLogger(__name__)

class EmailChangeRepository:
    def __init__(self):
        self.collection = collection.database.EmailChangeRequests
        self.user_collection = collection.database.Users
        
    def create_request(self, user_id, current_email, new_email):
        """Create a new email change request."""
        try:
            request_id = str(uuid.uuid4())
            request_data = {
                "_id": request_id,
                "userId": user_id,
                "currentEmail": current_email,
                "newEmail": new_email,
                "status": "pending",
                "createdAt": datetime.utcnow().isoformat(),
                "expiresAt": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
            
            # Cancel any existing pending requests for this user
            self.collection.update_many(
                {"userId": user_id, "status": "pending"},
                {"$set": {"status": "cancelled", "cancelledAt": datetime.utcnow().isoformat()}}
            )
            
            result = self.collection.insert_one(request_data)
            if result.inserted_id:
                logger.info(f"Created email change request: {request_id}")
                return {"requestId": request_id}, 201
            return {"error": "Failed to create email change request"}, 500
            
        except Exception as e:
            logger.error(f"Error creating email change request: {e}", exc_info=True)
            return {"error": f"Internal server error: {str(e)}"}, 500
            
    def get_pending_request(self, request_id):
        """Get a pending email change request."""
        try:
            request = self.collection.find_one({
                "_id": request_id,
                "status": "pending",
                "expiresAt": {"$gt": datetime.utcnow().isoformat()}
            })
            if not request:
                logger.warning(f"No valid pending request found for ID: {request_id}")
                return {"error": "No valid pending request found"}, 404
                
            logger.info(f"Found pending request: {request_id}")
            return {"request": request}, 200
            
        except Exception as e:
            logger.error(f"Error retrieving email change request: {e}", exc_info=True)
            return {"error": f"Internal server error: {str(e)}"}, 500
            
    def complete_request(self, request_id):
        """Mark an email change request as completed and update user email."""
        try:
            # First get the request to ensure it exists and is pending
            request = self.collection.find_one({"_id": request_id, "status": "pending"})
            if not request:
                logger.warning(f"No pending request found for completion: {request_id}")
                return {"error": "No pending request found to complete"}, 404

            # Update the request status
            result = self.collection.update_one(
                {"_id": request_id, "status": "pending"},
                {
                    "$set": {
                        "status": "completed",
                        "completedAt": datetime.utcnow().isoformat()
                    }
                }
            )

            if result.modified_count == 0:
                logger.error(f"Failed to update request status: {request_id}")
                return {"error": "Failed to update request status"}, 500

            # Update user's email
            user_result = self.user_collection.update_one(
                {"_id": request["userId"]},
                {
                    "$set": {
                        "email": request["newEmail"],
                        "updatedAt": datetime.utcnow().isoformat()
                    }
                }
            )

            if user_result.modified_count == 0:
                logger.error(f"Failed to update user email for request: {request_id}")
                # Revert request status
                self.collection.update_one(
                    {"_id": request_id},
                    {"$set": {"status": "pending"}}
                )
                return {"error": "Failed to update user email"}, 500

            logger.info(f"Successfully completed email change request: {request_id}")
            return {"message": "Request completed successfully"}, 200
            
        except Exception as e:
            logger.error(f"Error completing email change request: {e}", exc_info=True)
            return {"error": f"Internal server error: {str(e)}"}, 500
            
    def cancel_request(self, request_id):
        """Cancel an email change request."""
        try:
            result = self.collection.update_one(
                {"_id": request_id, "status": "pending"},
                {
                    "$set": {
                        "status": "cancelled",
                        "cancelledAt": datetime.utcnow().isoformat()
                    }
                }
            )
            
            if result.modified_count == 0:
                logger.warning(f"No pending request found to cancel: {request_id}")
                return {"error": "No pending request found to cancel"}, 404
                
            logger.info(f"Successfully cancelled email change request: {request_id}")
            return {"message": "Request cancelled successfully"}, 200
            
        except Exception as e:
            logger.error(f"Error cancelling email change request: {e}", exc_info=True)
            return {"error": f"Internal server error: {str(e)}"}, 500 