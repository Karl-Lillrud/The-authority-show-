# backend/services/activity_service.py
import uuid
import logging
from datetime import datetime, timezone
from backend.database.mongo_connection import collection

logger = logging.getLogger(__name__)


class ActivityService:
    def __init__(self):
        self.activities_collection = collection.database.Activities

    def log_activity(self, user_id, activity_type, description, details=None):
        try:
            activity = {
                "_id": str(uuid.uuid4()),
                "userId": str(user_id),
                "type": activity_type,
                "description": description,
                "details": details or {},
                "createdAt": datetime.now(timezone.utc),
            }
            self.activities_collection.insert_one(activity)
            logger.info(f"Logged activity: {activity_type} for user {user_id}")
        except Exception as e:
            logger.error(f"Error logging activity: {e}", exc_info=True)
