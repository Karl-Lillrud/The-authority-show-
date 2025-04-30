#src/backend/services/transcriptionService.py
import os
import openai
import logging
from datetime import datetime, timezone
from typing import List
from io import BytesIO
from elevenlabs.client import ElevenLabs
from backend.database.mongo_connection import fs
from backend.utils.ai_utils import remove_filler_words,analyze_emotions
from backend.utils.text_utils import generate_ai_suggestions, generate_show_notes, generate_ai_quotes, generate_ai_quotes, generate_quote_images,translate_text,suggest_sound_effects

logger = logging.getLogger(__name__)
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

class TranscriptionService:
    def transcribe_audio(self, file_data: bytes, filename: str) -> dict:
        
        logger.info(f"Starting transcription")

        # 2. Transcribe with ElevenLabs
        audio_data = BytesIO(file_data)
        transcription_result = client.speech_to_text.convert(
            file=audio_data,
            model_id="scribe_v1",
            num_speakers=2,
            diarize=True,
            timestamps_granularity="word"
        )

        if not transcription_result.text:
            raise Exception("Transcription returned no text.")

        transcription_text = transcription_result.text.strip()
        logger.info(f"🧠 Final transcription text:\n{transcription_text[:300]}")

        file_id = fs.put(
            file_data,
            filename=filename,
            metadata={"upload_timestamp": datetime.now(timezone.utc)}
        )
        logger.info(f"✅ File saved to MongoDB with ID: {file_id}")
        
        raw_transcription = []
        speaker_map = {}
        speaker_counter = 1

        # 3. Build word-level transcription
        logger.debug(f"Word-level entries found: {len(transcription_result.words)}")
        for word_info in transcription_result.words:
            word = word_info.text.strip()
            start = round(word_info.start, 2)
            end = round(word_info.end, 2)
            speaker_id = word_info.speaker_id

            if speaker_id not in speaker_map:
                speaker_map[speaker_id] = f"Speaker {speaker_counter}"
                speaker_counter += 1

            speaker_label = speaker_map[speaker_id]
            if word:
                raw_transcription.append(f"[{start}-{end}] {speaker_label}: {word}")

        # 4. Fallback if no word-level transcription is available
        if not raw_transcription:
            logger.warning("⚠️ No word-level transcription found. Using fallback.")
            fallback_sentences = transcription_text.split(".")
            raw_transcription = [
                f"Speaker 1: {sentence.strip()}" for sentence in fallback_sentences if sentence.strip()
            ]

        return {
            "file_id": str(file_id),
            "raw_transcription": " ".join(raw_transcription),
            "full_transcript": transcription_text
        }

    def get_clean_transcript(self, transcript_text: str) -> str:
        logger.info("🧽 Running filler-word removal...")
        return remove_filler_words(transcript_text)

    def get_ai_suggestions(self, transcript_text: str) -> str:
        logger.info("💡 Generating AI suggestions...")
        return generate_ai_suggestions(transcript_text)

    def get_show_notes(self, transcript_text: str) -> str:
        logger.info("📝 Generating show notes...")
        return generate_show_notes(transcript_text)

    def get_quotes(self, transcript_text: str) -> str:
        logger.info("💬 Generating quotes...")
        quotes_text = generate_ai_quotes(transcript_text)
        # Ensure it's a string. If it's not, convert it.
        if not isinstance(quotes_text, str):
            quotes_text = str(quotes_text)
        return quotes_text
    
    def get_quote_images(self, quotes: List[str]) -> List[str]:
        logger.info("🖼 Generating quote images...")
        return generate_quote_images(quotes)

    def translate_text(self, text: str, language: str) -> str:
        logger.info(f"🌍 Translating transcript to {language}...")
        return translate_text(text, language)

    def get_sentiment_and_sfx(self, transcript_text: str):
        logger.info("🔍 Running sentiment & sound suggestion analysis...")
        emotion_data = analyze_emotions(transcript_text)
        sfx_suggestions = suggest_sound_effects(emotion_data)
        return {"emotions": emotion_data, "sound_effects": sfx_suggestions}
