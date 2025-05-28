import logging
from backend.database.mongo_connection import collection

logger = logging.getLogger(__name__)

def force_episode_published_status(episode_id, user_id=None):
    """
    Force an episode's status to 'published' in the database.
    Used as a fallback when normal update mechanisms aren't working.
    
    Args:
        episode_id: The ID of the episode to update
        user_id: Optional user ID to verify ownership
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        episodes_collection = collection.database.Episodes
        query = {"_id": episode_id}
        if user_id:
            query["userid"] = str(user_id)
            
        update_result = episodes_collection.update_one(
            query,
            {"$set": {"status": "published"}}
        )
        
        success = update_result.matched_count > 0
        logger.info(
            f"Force published status for episode {episode_id}: "
            f"matched={update_result.matched_count}, "
            f"modified={update_result.modified_count}, "
            f"success={success}"
        )
        return success
    except Exception as e:
        logger.error(f"Failed to force episode {episode_id} published status: {str(e)}", exc_info=True)
        return False
