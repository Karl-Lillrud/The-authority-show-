# video_service.py
import logging
import os
import subprocess
import tempfile
from datetime import datetime
from bson import ObjectId

from backend.database.mongo_connection import fs
from backend.utils.file_utils import extract_audio, detect_background_noise
from backend.utils.text_utils import transcribe_with_whisper
from backend.utils.ai_utils import analyze_sentiment

logger = logging.getLogger(__name__)

class VideoService:
    def upload_video(self, video_bytes: bytes, filename: str) -> str:
        """
        Just store the video in GridFS, returning file_id.
        """
        file_id = fs.put(
            video_bytes,
            filename=filename,
            metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"},
        )
        logger.info(f"Video uploaded to GridFS with ID: {file_id}")
        return str(file_id)

    def enhance_video(self, file_id: str) -> str:
        """
        Download from GridFS, run FFmpeg enhancement, re-upload, return new ID.
        """
        video_file = fs.get(ObjectId(file_id))
        if not video_file:
            raise ValueError("Video not found in GridFS")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(video_file.read())
            tmp.flush()
            temp_in = tmp.name

        temp_out = temp_in.replace(".mp4", "_processed.mp4")
        ffmpeg_cmd = f'ffmpeg -i "{temp_in}" -vf "eq=contrast=1.05:brightness=0.05" -af "loudnorm" "{temp_out}"'
        subprocess.run(ffmpeg_cmd, shell=True, check=True)

        # Save processed
        with open(temp_out, "rb") as f:
            processed_data = f.read()

        processed_id = fs.put(
            processed_data,
            filename=f"processed_{file_id}.mp4",
            metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"},
        )

        os.remove(temp_in)
        os.remove(temp_out)
        return str(processed_id)

    def analyze_video(self, file_id: str):
        """
        Extract audio, check background noise, do transcription, sentiment, etc.
        """
        video_file = fs.get(ObjectId(file_id))
        if not video_file:
            raise ValueError("Video not found")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(video_file.read())
            tmp.flush()
            video_path = tmp.name

        # 1. Extract audio
        audio_path = video_path.replace(".mp4", ".wav")
        extract_audio(video_path, audio_path)

        # 2. Detect noise
        noise_result = detect_background_noise(audio_path)

        # 3. Transcribe with Whisper
        transcript = transcribe_with_whisper(audio_path)

        # 4. Sentiment
        sentiment = analyze_sentiment(transcript)

        # 5. Visual quality (sharpness, contrast) if needed
        #   e.g. self.calculate_visual_quality(...)

        # Cleanup
        os.remove(video_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return {
            "background_noise": noise_result,
            "transcript": transcript,
            "sentiment": sentiment,
            # "visual_quality": ...
        }

    def cut_video(self, file_id: str, start_time: float, end_time: float) -> str:
        """
        Use FFmpeg to cut a portion of the video from start_time to end_time.
        """
        video_file = fs.get(ObjectId(file_id))
        video_data = video_file.read()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(video_data)
            tmp.flush()
            temp_in = tmp.name

        temp_out = temp_in.replace(".mp4", "_clipped.mp4")
        ffmpeg_cmd = f'ffmpeg -y -i "{temp_in}" -ss {start_time} -to {end_time} -c copy "{temp_out}"'
        subprocess.run(ffmpeg_cmd, shell=True, check=True)

        with open(temp_out, "rb") as f:
            clipped_data = f.read()

        clipped_id = fs.put(
            clipped_data,
            filename=f"clipped_{file_id}.mp4",
            metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"},
        )

        os.remove(temp_in)
        os.remove(temp_out)
        return str(clipped_id)
