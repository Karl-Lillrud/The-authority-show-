# backend/services/activity_service.py
import uuid
import logging
from datetime import datetime, timezone
from backend.database.mongo_connection import collection

logger = logging.getLogger(__name__)

MAX_ACTIVITIES_PER_USER = (
    30  # Define the maximum number of activities to store per user
)


class ActivityService:
    def __init__(self):
        self.activities_collection = collection.database.Activities

    def log_activity(
        self, user_id, activity_type, description, details=None, ip_address=None
    ):
        """
        Logs an activity to the database and ensures the user does not exceed MAX_ACTIVITIES_PER_USER.
        """
        try:
            user_id_str = str(user_id)  # Ensure user_id is a string for consistency
            activity = {
                "_id": str(uuid.uuid4()),
                "userId": user_id_str,  # Use the string version of user_id
                "type": activity_type,
                "description": description,
                "details": details or {},
                "createdAt": datetime.now(timezone.utc),
            }
            self.activities_collection.insert_one(activity)
            logger.info(f"Logged activity: {activity_type} for user {user_id_str}")

            # Enforce MAX_ACTIVITIES_PER_USER limit
            current_activities_count = self.activities_collection.count_documents(
                {"userId": user_id_str}
            )

            if current_activities_count > MAX_ACTIVITIES_PER_USER:
                num_to_delete = current_activities_count - MAX_ACTIVITIES_PER_USER
                # Find the oldest activities to delete
                oldest_activities = (
                    self.activities_collection.find({"userId": user_id_str})
                    .sort("createdAt", 1)
                    .limit(num_to_delete)
                )  # 1 for ascending (oldest first)

                ids_to_delete = [act["_id"] for act in oldest_activities]

                if ids_to_delete:
                    self.activities_collection.delete_many(
                        {"_id": {"$in": ids_to_delete}}
                    )
                    logger.info(
                        f"Deleted {len(ids_to_delete)} oldest activities for user {user_id_str} to maintain limit of {MAX_ACTIVITIES_PER_USER}."
                    )

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
            logger.error(
                f"Error retrieving activity for user {user_id}: {e}", exc_info=True
            )
            return {"error": "Failed to retrieve user activity"}, 500
