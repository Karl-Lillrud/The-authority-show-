import logging
import uuid
from typing import Optional
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

def get_edit_by_id(edit_id: str) -> Optional[dict]:
    """
    Hämtar ett edit-dokument baserat på dess ID
    """
    logger.info(f"🔍 Looking for edit with ID: {edit_id}")
    edit = db.Edits.find_one({"_id": edit_id})
    
    if edit:
        word_timings_count = len(edit.get("metadata", {}).get("word_timings", []))
        logger.info(f"✅ Found edit {edit_id} with {word_timings_count} word_timings")
    else:
        logger.warning(f"❌ Edit not found: {edit_id}")
    
    return edit

def add_voice_map_to_edit(edit_id: str, voice_map: dict):
    """
    Spara eller uppdatera en voiceMap i ett befintligt edit-dokument.
    """
    if not edit_id or not voice_map:
        logger.warning("Missing edit_id or voice_map for update")
        return None

    logger.info(f"💾 Adding voice_map to edit {edit_id}: {voice_map}")

    result = db.Edits.update_one(
        {"_id": edit_id},
        {
            "$set": {
                "voiceMap": voice_map,
                "updatedAt": datetime.utcnow()
            }
        }
    )

    if result.modified_count == 1:
        logger.info(f"✅ VoiceMap updated in edit {edit_id}")
    else:
        logger.warning(f"⚠️ Edit not found or unchanged for ID: {edit_id}")
    return result

