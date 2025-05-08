# src/backend/utils/transcription_utils.py

import os
import tempfile
import soundfile as sf
import logging

logger = logging.getLogger(__name__)

def check_audio_duration(audio_bytes: bytes, max_duration_seconds: int = 36) -> float:
    # Check audio duration in seconds.
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_bytes)
        temp_audio_path = temp_audio.name

    try:
        data, samplerate = sf.read(temp_audio_path)
        duration = len(data) / samplerate
        logger.info(f"Audio duration: {round(duration, 2)} seconds")
    except Exception as e:
        logger.error(f"Failed to read audio file: {e}")
        raise ValueError("Invalid audio file format.")
    finally:
        os.remove(temp_audio_path)

    if duration > max_duration_seconds:
        raise ValueError(
            f"Audio too long ({round(duration / 60, 2)} minutes). Max allowed is {max_duration_seconds / 60} minutes."
        )

    return duration
