from datetime import datetime
from backend.database.mongo_connection import get_db

db = get_db()

def create_edit_entry(episode_id, user_id, edit_type, clip_url, **kwargs):
    edit = {
        "episodeId": episode_id,
        "userId": user_id,
        "editType": edit_type,
        "clipUrl": clip_url,
        "createdAt": datetime.utcnow(),
        "clipName": kwargs.get("clipName"),
        "duration": kwargs.get("duration"),
        "status": kwargs.get("status", "done"),
        "tags": kwargs.get("tags", []),
        "transcript": kwargs.get("transcript"),
        "sentiment": kwargs.get("sentiment"),
        "metadata": kwargs.get("metadata", {}),
    }
    db.edits.insert_one(edit)
    return edit