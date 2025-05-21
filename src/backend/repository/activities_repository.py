import logging
from backend.database.mongo_connection import collection

logger = logging.getLogger(__name__)


class ActivitiesRepository:
    def __init__(self):
        self.collection = collection.database.Activities

    def delete_by_user(self, user_id: str) -> int:
        """
        Delete all activities associated with a user.
        Args:
            user_id (str): The ID of the user whose activities should be deleted
        Returns:
            int: Number of activities deleted
        """
        try:
            # Ensure user_id is string
            user_id_str = str(user_id)
            result = self.collection.delete_many({"userId": user_id_str})
            deleted_count = result.deleted_count
            logger.info(f"Deleted {deleted_count} activities for user {user_id_str}")
            return deleted_count
        except Exception as e:
            logger.error(f"Error deleting activities for user {user_id}: {e}", exc_info=True)
            return 0