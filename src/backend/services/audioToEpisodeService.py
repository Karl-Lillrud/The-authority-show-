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

            valid_mimes = ["audio/mpeg", "audio/mp3", "audio/wav"]
            mime_type = getattr(audio_file, "mimetype", None)
            if mime_type not in valid_mimes:
                logger.warning(f"Invalid file type: {mime_type}")
                return None

            logger.debug(f"Audio file: filename={getattr(audio_file, 'filename', 'unknown')}, "
                         f"content_type={mime_type}, readable={audio_file.stream.readable()}")

            buffer = BytesIO()
            audio_file.seek(0)
            buffer.write(audio_file.read())
            buffer.seek(0)

            # Calculate file size
            buffer.seek(0, os.SEEK_END)
            file_size_bytes = buffer.tell()
            buffer.seek(0)

            file_size_mb = file_size_bytes / (1024 * 1024)
            if file_size_mb < 1:
                file_size = file_size_bytes / 1024
                size_unit = "KB"
            else:
                file_size = file_size_mb
                size_unit = "MB"

            logger.debug(f"Calculated file size: {file_size_bytes} bytes ({file_size:.2f} {size_unit})")

            if file_size_bytes == 0:
                logger.error("File size is 0 bytes, invalid or empty file")
                return None

            max_size_mb = 500
            if file_size_mb > max_size_mb:
                logger.warning(f"File size exceeds limit: {file_size_mb:.2f} MB")
                return None

            # Extract duration using mutagen
            buffer.seek(0)  # Make sure we start from the beginning
            audio_info = MutagenFile(buffer)
            duration_seconds = None
            if audio_info is not None and hasattr(audio_info.info, 'length'):
                duration_seconds = round(audio_info.info.length, 2)
                logger.debug(f"Audio duration: {duration_seconds} seconds")
            else:
                logger.warning("Could not determine audio duration")

            # Prepare blob path
            file_name = os.path.basename(audio_file.filename) if hasattr(audio_file, 'filename') else f"{episode_id}.{mime_type.split('/')[-1]}"
            blob_path = f"users/{account_id}/podcasts/{podcast_id}/episodes/{episode_id}/{file_name}"

            # Upload to Azure Blob Storage
            buffer.seek(0)  # Reset again before upload
            blob_url = upload_file_to_blob(
                container_name=self.audio_container_name,
                blob_path=blob_path,
                file=buffer
            )

            if not blob_url or not blob_url.startswith("https://"):
                logger.error(f"Invalid or missing blob URL: {blob_url}")
                return None

            logger.info(f"Audio file uploaded to blob storage: {blob_url}, size: {file_size:.2f} {size_unit}")

            return {
                "blob_url": blob_url,
                "file_size": round(file_size, 2),
                "size_unit": size_unit,
                "duration_seconds": duration_seconds
            }

        except Exception as e:
            logger.error(f"Error uploading episode audio to blob: {e}", exc_info=True)
            return None
