# backend/services/activity_service.py
import uuid
import logging
from datetime import datetime, timezone
from backend.database.mongo_connection import collection

logger = logging.getLogger(__name__)


class ActivityService:
    def __init__(self):
        self.activities_collection = collection.database.Activities

    def log_activity(self, user_id, activity_type, description, details=None, ip_address=None):
        """
        Logs an activity to the database.
        """
        try:
            activity = {
                "_id": str(uuid.uuid4()),
                "userId": str(user_id),
                "type": activity_type,
                "description": description,
                "details": details or {},
                "ipAddress": ip_address,
                "createdAt": datetime.now(timezone.utc),
            }
            self.activities_collection.insert_one(activity)
            logger.info(f"Logged activity: {activity_type} for user {user_id}")
        except Exception as e:
            logger.error(f"Error logging activity: {e}", exc_info=True)

    def get_user_activity(self, user_id, limit=20):
        """
        Retrieves recent activity for a given user.
        """
        try:
            activities = list(
                self.activities_collection.find({"userId": user_id})
                .sort("createdAt", -1)
                .limit(limit)
            )
            return activities, 200
        except Exception as e:
            logger.error(f"Error retrieving activity for user {user_id}: {e}", exc_info=True)
            return {"error": "Failed to retrieve user activity"}, 500
