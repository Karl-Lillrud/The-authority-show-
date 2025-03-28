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
from elevenlabs.client import ElevenLabs

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

        # Save video to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
            tmp_video.write(video_bytes)
            video_path = tmp_video.name

        # Extract audio from video to WAV
        audio_path = video_path.replace(".mp4", ".wav")
        extract_audio(video_path, audio_path)

        # Transcribe audio (using Whisper in this case)
        with open(audio_path, "rb") as audio_file:
            client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
            result = client.speech_to_text.convert(
                file=audio_file,
                model_id="scribe_v1",
                num_speakers=2,
                diarize=True,
                timestamps_granularity="word",
            )
        transcript = result.text.strip()
        
        # Perform background noise detection and sentiment analysis
        noise_result = detect_background_noise(audio_path)
        sentiment = analyze_sentiment(transcript)

        # --- New Part: Visual Quality Analysis ---
        # Here we include dummy values for visual quality metrics.
        # In a real implementation, you might run FFmpeg filters (e.g., signalstats) and parse the output.
        visual_quality = {
            "sharpness": 0.75,  # Dummy value; replace with actual analysis if available.
            "contrast": 1.05    # Dummy value; replace with actual analysis if available.
        }

        # --- New Part: Speech Rate Calculation ---
        # Calculate audio duration using the wave module and count words.
        import wave
        with wave.open(audio_path, "rb") as wf:
            duration = wf.getnframes() / wf.getframerate()  # Duration in seconds
        word_count = len(transcript.split())
        # Calculate words per minute (WPM)
        speech_rate = word_count / (duration / 60) if duration > 0 else 0

        # Cleanup temporary files
        os.remove(video_path)
        os.remove(audio_path)

        return {
            "background_noise": noise_result,
            "transcript": transcript,
            "sentiment": sentiment,
            "visual_quality": visual_quality,
            "speech_rate": f"{speech_rate:.2f} WPM"
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