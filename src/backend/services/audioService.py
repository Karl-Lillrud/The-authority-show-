# audio_service.py
import os
import logging
import tempfile
from datetime import datetime
from bson import ObjectId
import subprocess

from backend.utils.file_utils import enhance_audio_with_ffmpeg, detect_background_noise
from backend.utils.ai_utils import remove_filler_words, calculate_clarity_score, analyze_sentiment
from backend.utils.text_utils import transcribe_with_whisper
from backend.repository.Ai_models import save_file

logger = logging.getLogger(__name__)

class AudioService:
    def enhance_audio(self, audio_bytes: bytes, filename: str) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            temp_in_path = tmp.name

        temp_out_path = temp_in_path.replace(".wav", "_enhanced.wav")
        success = enhance_audio_with_ffmpeg(temp_in_path, temp_out_path)

        if not success:
            raise RuntimeError("FFmpeg enhancement failed")

        with open(temp_out_path, "rb") as f:
            enhanced_data = f.read()

        enhanced_file_id = save_file(
            enhanced_data,
            filename=f"enhanced_{filename}",
            metadata={"type": "transcription", "enhanced": True}
        )

        os.remove(temp_in_path)
        os.remove(temp_out_path)

        return enhanced_file_id

    def analyze_audio(self, audio_bytes: bytes):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            temp_path = tmp.name

        transcript = transcribe_with_whisper(temp_path)
        cleaned = remove_filler_words(transcript)
        clarity_score = calculate_clarity_score(cleaned)
        noise_result = detect_background_noise(temp_path)
        sentiment_result = analyze_sentiment(transcript)

        os.remove(temp_path)

        return {
            "transcript": transcript,
            "cleaned_transcript": cleaned,
            "clarity_score": clarity_score,
            "background_noise": noise_result,
            "sentiment": sentiment_result,
        }

    def cut_audio(self, file_id: str, start_time: float, end_time: float) -> str:
        from backend.repository.Ai_models import get_file_data
        audio_data = get_file_data(file_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_data)
            temp_in = tmp.name

        temp_out = temp_in.replace(".wav", "_clipped.wav")
        cmd = f'ffmpeg -y -i "{temp_in}" -ss {start_time} -to {end_time} -c copy "{temp_out}"'
        subprocess.run(cmd, shell=True, check=True)

        with open(temp_out, "rb") as f:
            clipped_data = f.read()

        clipped_id = save_file(
            clipped_data,
            filename=f"clipped_{file_id}.wav",
            metadata={"type": "transcription", "clipped": True}
        )

        os.remove(temp_in)
        os.remove(temp_out)
        return clipped_id