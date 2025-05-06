import logging
import uuid
from datetime import datetime
from backend.database.mongo_connection import get_db

logger = logging.getLogger(__name__)
db = get_db()

def create_edit_entry(episode_id, user_id, edit_type, clip_url, **kwargs):
    if not episode_id or not user_id or not clip_url:
        logger.warning("Missing required edit entry fields")
        return None

    edit = {
        "_id": str(uuid.uuid4()),
        "episodeId": episode_id,
        "userId": user_id,
        "editType": edit_type,
        "clipUrl": clip_url,
        "clipName": kwargs.get("clipName", "Unnamed"),
        "createdAt": datetime.utcnow(),
        "duration": kwargs.get("duration"),
        "status": kwargs.get("status", "done"),
        "tags": kwargs.get("tags", []),
        "transcript": kwargs.get("transcript"),
        "sentiment": kwargs.get("sentiment"),
        "metadata": kwargs.get("metadata", {}),
    }

    logger.info(f"✅ Inserting edit: {edit}")
    db.Edits.insert_one(edit)
    return edit

def save_transcription_edit(user_id, episode_id, transcript_text, raw_transcript, sentiment, emotion, filename):
    edit = {
        "_id": str(uuid.uuid4()),  # <--- custom string ID
        "episodeId": episode_id,
        "userId": user_id,
        "editType": "transcription",
        "clipUrl": "",
        "status": "done",
        "transcript": transcript_text,
        "metadata": {"filename": filename},
        "sentiment": sentiment,
        "emotion": emotion,
        "createdAt": datetime.utcnow(),
        "tags": ["transcript"]
    }

    db.Edits.insert_one(edit)
