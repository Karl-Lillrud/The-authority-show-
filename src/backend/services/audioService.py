# audio_service.py
import logging
import os
import subprocess
import tempfile
from datetime import datetime
from io import BytesIO
from bson import ObjectId

from backend.database.mongo_connection import fs
from backend.utils.file_utils import enhance_audio_with_ffmpeg, detect_background_noise
from backend.utils.ai_utils import remove_filler_words, calculate_clarity_score
from backend.utils.ai_utils import analyze_sentiment
from backend.utils.text_utils import transcribe_with_whisper

logger = logging.getLogger(__name__)

class AudioService:
    def enhance_audio(self, audio_bytes: bytes, filename: str) -> str:
        """
        Enhance audio by saving to GridFS, running FFmpeg, and returning new file ID.
        """
        # 1. Save original file
        file_id = fs.put(
            audio_bytes,
            filename=filename,
            metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"},
        )
        logger.info(f"Original audio saved to GridFS with ID: {file_id}")

        # 2. Write to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            temp_in_path = tmp.name

        # 3. Run FFmpeg enhancement
        temp_out_path = temp_in_path.replace(".wav", "_enhanced.wav")
        enhanced_ok = enhance_audio_with_ffmpeg(temp_in_path, temp_out_path)
        if not enhanced_ok:
            raise RuntimeError("FFmpeg enhancement failed.")

        # 4. Read back enhanced audio & save to GridFS
        with open(temp_out_path, "rb") as f:
            enhanced_data = f.read()
        enhanced_file_id = fs.put(
            enhanced_data,
            filename=f"enhanced_{filename}",
            metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"},
        )

        # Cleanup
        os.remove(temp_in_path)
        os.remove(temp_out_path)

        return str(enhanced_file_id)

    def analyze_audio(self, audio_bytes: bytes):
        """
        Analyze emotion, sentiment, clarity, background noise, speech rate, etc.
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            temp_path = tmp.name

        # 1. Transcribe with Whisper
        transcript = transcribe_with_whisper(temp_path)
        # 2. Remove filler words for clarity
        cleaned = remove_filler_words(transcript)
        # 3. Clarity Score
        clarity_score_text = calculate_clarity_score(cleaned)
        # 4. Background Noise
        noise_result = detect_background_noise(temp_path)
        # 5. Sentiment
        sentiment_result = analyze_sentiment(transcript)
        # 6. Speech Rate
        # (Implement your speech_rate function or reuse from your code)

        # Cleanup
        os.remove(temp_path)

        return {
            "transcript": transcript,
            "cleaned_transcript": cleaned,
            "clarity_score": clarity_score_text,
            "background_noise": noise_result,
            "sentiment": sentiment_result,
            # "speech_rate": ...
        }

    def cut_audio(self, file_id: str, start_time: float, end_time: float) -> str:
        """
        Cut audio using FFmpeg from GridFS. Return clipped file ID.
        """
        # 1. Retrieve from GridFS
        original_file = fs.get(ObjectId(file_id))
        audio_data = original_file.read()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_data)
            temp_in = tmp.name

        temp_out = temp_in.replace(".wav", "_clipped.wav")

        # 2. Run FFmpeg
        ffmpeg_cmd = f'ffmpeg -y -i "{temp_in}" -ss {start_time} -to {end_time} -c copy "{temp_out}"'
        subprocess.run(ffmpeg_cmd, shell=True, check=True)

        # 3. Save clipped to GridFS
        with open(temp_out, "rb") as f:
            clipped_data = f.read()
        clipped_id = fs.put(
            clipped_data,
            filename=f"clipped_{file_id}.wav",
            metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"},
        )

        os.remove(temp_in)
        os.remove(temp_out)
        return str(clipped_id)
