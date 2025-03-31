import os
import logging
import tempfile
import requests
import subprocess
from backend.database.mongo_connection import get_fs
from backend.utils.file_utils import enhance_audio_with_ffmpeg, detect_background_noise, convert_audio_to_wav
from backend.utils.ai_utils import (
    remove_filler_words, calculate_clarity_score, analyze_sentiment
)
from backend.utils.text_utils import (
    transcribe_with_whisper, detect_filler_words, classify_sentence_relevance,
    analyze_certainty_levels, get_sentence_timestamps, detect_long_pauses,
    generate_ai_show_notes
)
from backend.repository.ai_models import save_file, get_file_data, get_file_by_id
from elevenlabs.client import ElevenLabs

logger = logging.getLogger(__name__)
fs = get_fs()

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
        logger.info(f"📥 Request to clip audio file with ID: {file_id}")
        logger.info(f"🕒 Timestamps to clip: start={start_time}, end={end_time}")

        if start_time is None or end_time is None or start_time >= end_time:
            raise ValueError("Invalid timestamps.")

        clipped_filename = f"clipped_{file_id}.wav"
        existing = fs.find_one({"filename": clipped_filename})
        if existing:
            logger.info(f"✅ Clipped version exists: {existing._id}")
            return str(existing._id)

        audio_data = get_file_data(file_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_in:
            tmp_in.write(audio_data)
            input_path = tmp_in.name

        output_path = input_path.replace(".wav", "_clipped.wav")

        try:
            ffmpeg_cmd = f'ffmpeg -y -i "{input_path}" -ss {start_time} -to {end_time} -c copy "{output_path}"'
            subprocess.run(ffmpeg_cmd, shell=True, check=True)

            with open(output_path, "rb") as f:
                clipped_data = f.read()

            clipped_file_id = save_file(
                clipped_data,
                filename=clipped_filename,
                metadata={"type": "transcription", "clipped": True}
            )

            logger.info(f"✅ Clipped audio saved with ID: {clipped_file_id}")
            return clipped_file_id

        finally:
            for path in [input_path, output_path]:
                if os.path.exists(path):
                    os.remove(path)

    def ai_cut_audio(self, file_bytes: bytes, filename: str) -> dict:
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".mp3", ".wav"]:
            raise ValueError("Unsupported audio format")

        temp_path = (
            convert_audio_to_wav(file_bytes, original_ext=ext)
            if ext == ".mp3"
            else tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
        )

        if ext == ".wav":
            with open(temp_path, "wb") as f:
                f.write(file_bytes)

        logger.info(f"📥 AI Cut: Temp file at {temp_path}")

        try:
            client = ElevenLabs()
            result = client.speech_to_text.convert(
                file=open(temp_path, "rb"),
                model_id="scribe_v1",
                num_speakers=2,
                diarize=True,
                timestamps_granularity="word"
            )

            transcript = result.text.strip()
            word_timings = [
                {"word": w.text, "start": w.start, "end": w.end}
                for w in result.words
                if hasattr(w, "start") and hasattr(w, "end")
            ]

            cleaned_transcript = remove_filler_words(transcript)
            noise_result = detect_background_noise(temp_path)
            filler_sentences = detect_filler_words(transcript)
            sentence_certainty = analyze_certainty_levels(transcript)

            sentence_timestamps = []
            for idx, entry in enumerate(sentence_certainty):
                timestamps = get_sentence_timestamps(entry["sentence"], word_timings)
                entry.update({"start": timestamps["start"], "end": timestamps["end"], "id": idx})
                sentence_timestamps.append({
                    "id": idx,
                    "sentence": entry["sentence"],
                    "start": timestamps["start"],
                    "end": timestamps["end"]
                })

            suggested_cuts = [
                {
                    "sentence": e["sentence"],
                    "certainty_level": e["certainty_level"],
                    "certainty_score": e["certainty"],
                    "start": e["start"],
                    "end": e["end"]
                } for e in sentence_certainty if e["certainty"] >= 0.6
            ]

            sentiment = analyze_sentiment(transcript)
            show_notes = generate_ai_show_notes(transcript)

            return {
                "message": "✅ AI Audio processing completed",
                "cleaned_transcript": cleaned_transcript,
                "background_noise": noise_result,
                "filler_sentences": filler_sentences,
                "sentence_certainty_scores": sentence_certainty,
                "sentence_timestamps": sentence_timestamps,
                "suggested_cuts": suggested_cuts,
                "sentiment": sentiment,
                "long_pauses": detect_long_pauses(temp_path),
                "ai_show_notes": show_notes,
            }

        finally:
            os.remove(temp_path)
            logger.info(f"🗑️ Temp file cleaned up: {temp_path}")

    def ai_cut_audio_from_id(self, file_id: str) -> dict:
        audio_bytes, filename = get_file_by_id(file_id)
        return self.ai_cut_audio(audio_bytes, filename)
    
    def isolate_voice(self, audio_bytes: bytes, filename: str) -> str:
        """
        Use ElevenLabs Audio Isolation API to extract vocals and save result to MongoDB.
        """
        logger.info(f"🎙️ Starting voice isolation for file: {filename}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            temp_path = tmp.name

        try:
            logger.info("🔄 Sending audio to ElevenLabs voice isolation endpoint...")

            with open(temp_path, "rb") as f:
                response = requests.post(
                    "https://api.elevenlabs.io/v1/audio-isolation",
                    headers={
                        "xi-api-key": os.getenv("ELEVENLABS_API_KEY")
                    },
                    files={"audio": f}
                )

            if response.status_code != 200:
                logger.error(f"❌ Voice isolation failed: {response.status_code} {response.text}")
                raise RuntimeError(f"Voice isolation failed: {response.status_code} {response.text}")

            isolated_audio = response.content

            isolated_filename = f"isolated_{filename}"
            file_id = save_file(
                isolated_audio,
                filename=isolated_filename,
                metadata={"type": "voice_isolated", "source": filename}
            )

            logger.info(f"✅ Isolated voice saved to MongoDB with ID: {file_id}")
            return file_id

        except Exception as e:
            logger.error(f"❌ Voice isolation failed: {str(e)}")
            raise RuntimeError(f"Voice isolation failed: {str(e)}")

        finally:
            os.remove(temp_path)
            logger.info(f"🗑️ Temp file cleaned up: {temp_path}")
