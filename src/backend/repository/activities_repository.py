from backend.database.mongo_connection import collection


class ActivitiesRepository:
    def __init__(self):
        self.collection = collection.database.Activities

    def delete_by_user(self, user_id):
        try:
            result = self.collection.delete_many({"userId": user_id})
            logger.info(f"Deleted {result.deleted_count} activities for user {user_id}")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error deleting activities for user {user_id}: {e}", exc_info=True)
            return 0