#src/backend/services/transcriptionService.py
import os
import re
import openai
import logging
from datetime import datetime
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
        # 1. Spara fil till MongoDB
        file_id = fs.put(
            file_data,
            filename=filename,
            metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"},
        )
        logger.info(f"📥 File saved to MongoDB with ID: {file_id}")

        # 2. Transkribera med ord-granularitet och exakt 2 talare
        audio_data = BytesIO(file_data)
        transcription_result = client.speech_to_text.convert(
            file=audio_data,
            model_id="scribe_v1",
            diarize=True,
            num_speakers=2,
            timestamps_granularity="word"
        )

        if not transcription_result.text:
            raise Exception("Transcription returned no text.")

        transcription_text = transcription_result.text.strip()
        logger.info(f"🧠 Full transcript (first 300 chars):\n{transcription_text[:300]}")

        # 3. Manuellt gruppera ord till meningar med tidsstämplar per mening
        raw_transcription = []
        speaker_map = {}
        speaker_counter = 1
        buffer = []
        buffer_speaker = None

        for w in transcription_result.words:
            sid = w.speaker_id
            # Mappa nya talare
            if sid not in speaker_map:
                speaker_map[sid] = f"Speaker {speaker_counter}"
                speaker_counter += 1

            # Om talare byts, flusha befintlig buffer
            if buffer and sid != buffer_speaker:
                start = round(buffer[0].start, 2)
                end   = round(buffer[-1].end,   2)
                text  = " ".join(word.text.strip() for word in buffer).strip()
                label = speaker_map[buffer_speaker]
                raw_transcription.append(f"[{start}-{end}] {label}: {text}")
                buffer = []

            buffer_speaker = sid
            buffer.append(w)

            # Om ordet avslutar en mening, flusha
            if re.search(r"[\.!\?]$", w.text.strip()):
                start = round(buffer[0].start, 2)
                end   = round(buffer[-1].end,   2)
                text  = " ".join(word.text.strip() for word in buffer).strip()
                label = speaker_map[buffer_speaker]
                raw_transcription.append(f"[{start}-{end}] {label}: {text}")
                buffer = []

        # Flusha eventuell kvarvarande buffer
        if buffer:
            start = round(buffer[0].start, 2)
            end   = round(buffer[-1].end,   2)
            text  = " ".join(word.text.strip() for word in buffer).strip()
            label = speaker_map[buffer_speaker]
            raw_transcription.append(f"[{start}-{end}] {label}: {text}")

        # 4. Fallback om inga meningar bildades
        if not raw_transcription:
            logger.warning("⚠️ Ingen mening kunde grupperas – fallback till heltext utan tidsstämplar.")
            for sent in transcription_text.split("."):
                sent = sent.strip()
                if sent:
                    raw_transcription.append(f"Speaker 1: {sent}")

        return {
            "file_id": str(file_id),
            "raw_transcription": "\n".join(raw_transcription),
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
