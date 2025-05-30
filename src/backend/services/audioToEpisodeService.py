import os
import logging
from io import BytesIO
from mutagen import File as MutagenFile  # For extracting audio duration
from backend.utils.blob_storage import upload_file_to_blob, download_blob_to_tempfile

logger = logging.getLogger(__name__)

class AudioToEpisodeService:
    """
    Service to handle audio file operations for podcast episodes.
    """
    def __init__(self):
        self.audio_container_name = os.getenv("AZURE_BLOB_AUDIO_CONTAINER", "podmanagerfiles")
    
    def upload_episode_audio(self, account_id, episode_id, audio_file, podcast_id):
            try:
                if not audio_file:
                    logger.warning("No audio file provided for upload")
                    return None

                valid_mimes = [
                    "audio/mpeg", "audio/mp3", "audio/wav",
                    "audio/webm", "audio/webm;codecs=opus",
                    "audio/ogg", "audio/ogg;codecs=opus",
                    "audio/mp4"
                ]

                mime_type = getattr(audio_file, "mimetype", None)
                if mime_type not in valid_mimes:
                    logger.warning(f"Invalid file type: {mime_type}")
                    return None

                logger.debug(f"Audio file: filename={getattr(audio_file, 'filename', 'unknown')}, "
                            f"content_type={mime_type}, readable={audio_file.readable()}")

                buffer = BytesIO()
                audio_file.seek(0)
                buffer.write(audio_file.read())
                buffer.seek(0)

                # Calculate file size
                buffer.seek(0, os.SEEK_END)
                file_size_bytes = buffer.tell()
                buffer.seek(0)

                if file_size_bytes == 0:
                    logger.error("File size is 0 bytes, invalid or empty file")
                    return None

                max_size_bytes = 500 * 1024 * 1024  # 500MB
                if file_size_bytes > max_size_bytes:
                    logger.warning(f"File size {file_size_bytes} exceeds max allowed size")
                    return None

                # Try to get audio duration
                buffer.seek(0)
                audio_info = MutagenFile(buffer)
                duration_seconds = None
                if audio_info and hasattr(audio_info.info, "length"):
                    duration_seconds = round(audio_info.info.length)
                    logger.debug(f"Audio duration: {duration_seconds} seconds")
                else:
                    logger.warning("Could not determine audio duration")

                # Determine file extension from MIME
                mime_to_ext = {
                    "audio/mpeg": "mp3",
                    "audio/mp3": "mp3",
                    "audio/wav": "wav",
                    "audio/webm": "webm",
                    "audio/webm;codecs=opus": "webm",
                    "audio/ogg": "ogg",
                    "audio/ogg;codecs=opus": "ogg",
                    "audio/mp4": "mp4"
                }
                file_extension = mime_to_ext.get(mime_type, "webm")

                safe_file_name = f"{episode_id}_audio.{file_extension}"
                blob_path = f"users/{account_id}/podcasts/{podcast_id}/episodes/{episode_id}/{safe_file_name}"

                # Upload to Azure
                buffer.seek(0)
                blob_url = upload_file_to_blob(
                    container_name=self.audio_container_name,
                    blob_path=blob_path,
                    file=buffer,
                    content_type=mime_type
                )

                if not blob_url or not blob_url.startswith("https://"):
                    logger.error(f"Blob upload failed or URL invalid: {blob_url}")
                    return None

                logger.info(f"Audio uploaded to Azure: {blob_url}")

                return {
                    "blob_url": blob_url,
                    "file_size_bytes": file_size_bytes,
                    "file_type": mime_type,
                    "duration_seconds": duration_seconds
                }

            except Exception as e:
                logger.error(f"Error uploading audio: {e}", exc_info=True)
                return None