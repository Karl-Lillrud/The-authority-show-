import logging
from backend.database.mongo_connection import collection
from flask import current_app
from werkzeug.datastructures import FileStorage
import os

try:
    from mutagen import File as MutagenFile
    from mutagen.mp3 import MP3
    from mutagen.wave import WAVE
    from mutagen.flac import FLAC
    from mutagen.oggvorbis import OggVorbis
    from mutagen.mp4 import MP4 # for m4a
except ImportError:
    MutagenFile = None
    MP3 = None
    WAVE = None
    FLAC = None
    OggVorbis = None
    MP4 = None
    current_app_logger = current_app.logger if current_app else None
    if current_app_logger:
        current_app_logger.warning(
            "Mutagen library not found. Audio duration and type detection will be limited. "
            "Please install it using 'pip install mutagen'.")
    else:
        print(
            "Warning: Mutagen library not found. Audio duration and type detection will be limited. "
            "Please install it using 'pip install mutagen'.")


logger = logging.getLogger(__name__)

def calculate_audio_duration(file_storage: FileStorage) -> int | None:
    """
    Calculates the duration of an audio file in seconds.
    Args:
        file_storage: A FileStorage object representing the audio file.
    Returns:
        Duration in seconds as an integer, or None if duration cannot be determined.
    """
    logger = current_app.logger
    if not MutagenFile:
        logger.warning("Mutagen library is not available. Cannot calculate audio duration.")
        return None

    try:
        # Mutagen needs a filename or a file-like object.
        # To avoid saving to disk, pass the stream.
        # Ensure the stream is at the beginning.
        file_storage.seek(0)
        audio = MutagenFile(file_storage.stream)
        if audio and audio.info:
            duration = int(audio.info.length)
            logger.info(f"Calculated audio duration for '{file_storage.filename}': {duration}s")
            return duration
        else:
            logger.warning(f"Could not get audio info for '{file_storage.filename}' using MutagenFile generic.")
            # Try specific types if generic fails or info is not detailed enough
            file_storage.seek(0) # Reset stream for next read
            if file_storage.filename.lower().endswith('.mp3'):
                audio = MP3(file_storage.stream)
            elif file_storage.filename.lower().endswith('.wav'):
                audio = WAVE(file_storage.stream)
            elif file_storage.filename.lower().endswith('.flac'):
                audio = FLAC(file_storage.stream)
            elif file_storage.filename.lower().endswith('.ogg'):
                audio = OggVorbis(file_storage.stream)
            elif file_storage.filename.lower().endswith(('.m4a', '.mp4')): # MP4 can contain audio
                audio = MP4(file_storage.stream)
            else:
                audio = None # Unknown type for specific mutagen loaders
            
            if audio and audio.info:
                duration = int(audio.info.length)
                logger.info(f"Calculated audio duration (specific type) for '{file_storage.filename}': {duration}s")
                return duration
            else:
                logger.warning(f"Could not determine duration for '{file_storage.filename}' even with specific mutagen types.")
                return None

    except Exception as e:
        logger.error(f"Error calculating audio duration for '{file_storage.filename}': {e}", exc_info=True)
        return None
    finally:
        # It's good practice to reset the stream pointer if the FileStorage object will be used again
        file_storage.seek(0)


def get_audio_file_size(file_storage: FileStorage) -> int | None:
    """
    Gets the size of an audio file in bytes.
    Args:
        file_storage: A FileStorage object representing the audio file.
    Returns:
        File size in bytes as an integer, or None if size cannot be determined.
    """
    logger = current_app.logger
    try:
        file_storage.seek(0, os.SEEK_END)  # Go to the end of the file
        size = file_storage.tell()        # Get the current position, which is the size
        file_storage.seek(0)              # Reset the stream pointer to the beginning
        logger.info(f"Calculated audio file size for '{file_storage.filename}': {size} bytes")
        return size
    except Exception as e:
        logger.error(f"Error getting file size for '{file_storage.filename}': {e}", exc_info=True)
        return None


def get_audio_file_type(file_storage: FileStorage) -> str | None:
    """
    Gets the MIME type of an audio file.
    Args:
        file_storage: A FileStorage object representing the audio file.
    Returns:
        MIME type as a string (e.g., 'audio/mpeg'), or None.
    """
    logger = current_app.logger
    try:
        # FileStorage object has a content_type attribute
        content_type = file_storage.content_type
        if content_type and content_type != 'application/octet-stream':
            logger.info(f"Determined audio file type for '{file_storage.filename}' from FileStorage: {content_type}")
            return content_type

        # Fallback to extension if content_type is generic or missing
        _, ext = os.path.splitext(file_storage.filename)
        ext = ext.lower()
        mime_map = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac',
            '.m4a': 'audio/mp4', # M4A is often MP4 container
            '.aac': 'audio/aac',
        }
        inferred_type = mime_map.get(ext)
        if inferred_type:
            logger.info(f"Inferred audio file type for '{file_storage.filename}' from extension '{ext}': {inferred_type}")
            return inferred_type
            
        logger.warning(f"Could not determine specific audio file type for '{file_storage.filename}'. Defaulting to application/octet-stream or None.")
        return 'application/octet-stream' # A generic fallback if truly unknown

    except Exception as e:
        logger.error(f"Error getting file type for '{file_storage.filename}': {e}", exc_info=True)
        return None


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
