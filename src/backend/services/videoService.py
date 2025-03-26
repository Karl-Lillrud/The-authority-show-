# video_service.py
import os
import logging
import tempfile
from datetime import datetime
from bson import ObjectId
import subprocess

from backend.utils.file_utils import extract_audio, detect_background_noise
from backend.utils.text_utils import transcribe_with_whisper
from backend.utils.ai_utils import analyze_sentiment
from backend.repository.Ai_models import save_file, get_file_data

logger = logging.getLogger(__name__)

class VideoService:
    def upload_video(self, video_bytes: bytes, filename: str) -> str:
        return save_file(
            video_bytes,
            filename=filename,
            metadata={"type": "transcription", "upload_timestamp": datetime.utcnow()}
        )

    def enhance_video(self, file_id: str) -> str:
        video_bytes = get_file_data(file_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(video_bytes)
            temp_in = tmp.name

        temp_out = temp_in.replace(".mp4", "_processed.mp4")
        cmd = f'ffmpeg -i "{temp_in}" -vf "eq=contrast=1.05:brightness=0.05" -af "loudnorm" "{temp_out}"'
        subprocess.run(cmd, shell=True, check=True)

        with open(temp_out, "rb") as f:
            processed_data = f.read()

        processed_id = save_file(
            processed_data,
            filename=f"processed_{file_id}.mp4",
            metadata={"type": "transcription", "enhanced": True}
        )

        os.remove(temp_in)
        os.remove(temp_out)
        return processed_id

    def analyze_video(self, file_id: str):
        video_bytes = get_file_data(file_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(video_bytes)
            video_path = tmp.name

        audio_path = video_path.replace(".mp4", ".wav")
        extract_audio(video_path, audio_path)

        noise_result = detect_background_noise(audio_path)
        transcript = transcribe_with_whisper(audio_path)
        sentiment = analyze_sentiment(transcript)

        os.remove(video_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return {
            "background_noise": noise_result,
            "transcript": transcript,
            "sentiment": sentiment,
        }

    def cut_video(self, file_id: str, start_time: float, end_time: float) -> str:
        video_bytes = get_file_data(file_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(video_bytes)
            temp_in = tmp.name

        temp_out = temp_in.replace(".mp4", "_clipped.mp4")
        cmd = f'ffmpeg -y -i "{temp_in}" -ss {start_time} -to {end_time} -c copy "{temp_out}"'
        subprocess.run(cmd, shell=True, check=True)

        with open(temp_out, "rb") as f:
            clipped_data = f.read()

        clipped_id = save_file(
            clipped_data,
            filename=f"clipped_{file_id}.mp4",
            metadata={"type": "transcription", "clipped": True}
        )

        os.remove(temp_in)
        os.remove(temp_out)
        return clipped_id