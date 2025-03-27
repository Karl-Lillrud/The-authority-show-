import os
import logging
import tempfile
from datetime import datetime
import subprocess
from bson import ObjectId

from backend.utils.file_utils import extract_audio, detect_background_noise
from backend.utils.text_utils import transcribe_with_whisper
from backend.utils.ai_utils import analyze_sentiment
from backend.repository.Ai_models import save_file, get_file_data
from backend.database.mongo_connection import get_fs

logger = logging.getLogger(__name__)
fs = get_fs()

class VideoService:
    def upload_video(self, video_bytes: bytes, filename: str) -> str:
        logger.info(f"📤 Uploading video: {filename}")
        return save_file(
            video_bytes,
            filename=filename,
            metadata={"type": "video", "upload_timestamp": datetime.utcnow()}
        )

    def enhance_video(self, file_id: str) -> str:
        logger.info(f"🎬 Enhancing video with ID: {file_id}")
        video_bytes = get_file_data(file_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_in:
            tmp_in.write(video_bytes)
            input_path = tmp_in.name

        output_path = input_path.replace(".mp4", "_enhanced.mp4")
        ffmpeg_cmd = f'ffmpeg -y -i "{input_path}" -vf "eq=contrast=1.05:brightness=0.05" -af "loudnorm" "{output_path}"'

        logger.info(f"🔧 Running FFmpeg command: {ffmpeg_cmd}")
        result = subprocess.run(ffmpeg_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        logger.debug(result.stdout.decode())
        logger.warning(result.stderr.decode())

        if result.returncode != 0 or not os.path.exists(output_path):
            raise RuntimeError("FFmpeg video enhancement failed")

        with open(output_path, "rb") as f:
            enhanced_data = f.read()

        enhanced_id = save_file(
            enhanced_data,
            filename=f"enhanced_{file_id}.mp4",
            metadata={"type": "video", "enhanced": True}
        )

        os.remove(input_path)
        os.remove(output_path)

        return enhanced_id

    def analyze_video(self, file_id: str) -> dict:
        logger.info(f"📊 Analyzing video with ID: {file_id}")
        video_bytes = get_file_data(file_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_in:
            tmp_in.write(video_bytes)
            video_path = tmp_in.name

        audio_path = video_path.replace(".mp4", ".wav")
        extract_audio(video_path, audio_path)

        transcript = transcribe_with_whisper(audio_path)
        noise_result = detect_background_noise(audio_path)
        sentiment = analyze_sentiment(transcript)

        os.remove(video_path)
        os.remove(audio_path)

        return {
            "background_noise": noise_result,
            "transcript": transcript,
            "sentiment": sentiment,
        }

    def cut_video(self, file_id: str, start_time: float, end_time: float) -> str:
        logger.info(f"✂ Cutting video {file_id} from {start_time}s to {end_time}s")
        if start_time >= end_time:
            raise ValueError("Start time must be less than end time")

        video_bytes = get_file_data(file_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_in:
            tmp_in.write(video_bytes)
            input_path = tmp_in.name

        output_path = input_path.replace(".mp4", "_clipped.mp4")

        ffmpeg_cmd = f'ffmpeg -y -i "{input_path}" -ss {start_time} -to {end_time} -c copy "{output_path}"'
        logger.info(f"🔧 Running FFmpeg command: {ffmpeg_cmd}")
        result = subprocess.run(ffmpeg_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        logger.debug(result.stdout.decode())
        logger.warning(result.stderr.decode())

        if result.returncode != 0 or not os.path.exists(output_path):
            raise RuntimeError("FFmpeg video cutting failed")

        with open(output_path, "rb") as f:
            clipped_data = f.read()

        clipped_id = save_file(
            clipped_data,
            filename=f"clipped_{file_id}.mp4",
            metadata={"type": "video", "clipped": True}
        )

        os.remove(input_path)
        os.remove(output_path)

        return clipped_id