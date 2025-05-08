#src/backend/services/transcriptionService.py
import os
import openai
import logging
import re
from datetime import datetime, timezone
from typing import List
from io import BytesIO
from elevenlabs.client import ElevenLabs
from backend.database.mongo_connection import fs
from backend.utils.ai_utils import remove_filler_words, analyze_emotions
from backend.utils.text_utils import (
    generate_ai_suggestions,
    generate_show_notes,
    generate_ai_quotes,
    generate_quote_images,
    translate_text,
    suggest_sound_effects,
    get_sentence_timestamps
)

logger = logging.getLogger(__name__)
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

class TranscriptionService:
    def transcribe_audio(self, file_data: bytes, filename: str) -> dict:
        logger.info(f"Starting transcription")

        # Step 1: Attempt transcription with ElevenLabs
        audio_data = BytesIO(file_data)
        try:
            transcription_result = client.speech_to_text.convert(
                file=audio_data,
                model_id="scribe_v1",
                num_speakers=2,
                diarize=True,
                timestamps_granularity="word"
            )
        except Exception as e:
            logger.error(f"ElevenLabs transcription failed: {str(e)}")
            raise Exception("Transcription service failed. Please try again later.")

        if not transcription_result.text:
            logger.warning("Transcription returned no text.")
            raise Exception("Transcription returned no text.")

        transcription_text = transcription_result.text.strip()
        logger.info(f"Transcription successful. Preview:\n{transcription_text[:300]}")

        # Step 2: Save only if transcription succeeded
        file_id = fs.put(
            file_data,
            filename=filename,
            metadata={"upload_timestamp": datetime.now(timezone.utc), "type": "transcription"},
        )
        logger.info(f"File saved to MongoDB with ID: {file_id}")

        # Prepare speaker mapping
        speaker_map = {}
        speaker_counter = 1

        # Build word timings list
        word_timings = []
        for w in transcription_result.words:
            text = w.text.strip()
            if not text:
                continue
            word_timings.append({
                "word": text,
                "start": round(w.start, 2),
                "end": round(w.end, 2),
                "speaker_id": w.speaker_id
            })
            if w.speaker_id not in speaker_map:
                speaker_map[w.speaker_id] = f"Speaker {speaker_counter}"
                speaker_counter += 1

        # Step 3: Build sentence-level transcription
        sentences = re.split(r'(?<=[\.\?\!])\s+', transcription_text)
        raw_transcription_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            # Compute timestamps
            ts = get_sentence_timestamps(sentence, word_timings)
            # Find speaker for the first word in this sentence
            first_word_start = ts["start"]
            first_entry = next((wt for wt in word_timings if wt["start"] == first_word_start), None)
            speaker_label = speaker_map.get(first_entry["speaker_id"], "Speaker 1") if first_entry else "Speaker 1"
            raw_transcription_sentences.append(f"[{ts['start']}-{ts['end']}] {speaker_label}: {sentence}")

        # Fallback to word-level if sentence-level is empty
        if not raw_transcription_sentences:
            logger.warning("No sentence-level transcription produced; falling back to word-level.")
            for wt in word_timings:
                speaker_label = speaker_map[wt['speaker_id']]
                raw_transcription_sentences.append(f"[{wt['start']}-{wt['end']}] {speaker_label}: {wt['word']}")

        return {
            "file_id": str(file_id),
            "raw_transcription": "\n".join(raw_transcription_sentences),
            "full_transcript": transcription_text
        }

    def get_clean_transcript(self, transcript_text: str) -> str:
        logger.info("Running filler-word removal...")
        return remove_filler_words(transcript_text)

    def get_ai_suggestions(self, transcript_text: str) -> str:
        logger.info("Generating AI suggestions...")
        return generate_ai_suggestions(transcript_text)

    def get_show_notes(self, transcript_text: str) -> str:
        logger.info("Generating show notes...")
        return generate_show_notes(transcript_text)

    def get_quotes(self, transcript_text: str) -> str:
        logger.info("Generating quotes...")
        quotes_text = generate_ai_quotes(transcript_text)
        if not isinstance(quotes_text, str):
            quotes_text = str(quotes_text)
        return quotes_text
    
    def get_quote_images(self, quotes: List[str]) -> List[str]:
        logger.info("Generating quote images...")
        return generate_quote_images(quotes)

    def translate_text(self, text: str, language: str) -> str:
        logger.info(f"Translating transcript to {language}...")
        return translate_text(text, language)

    def get_sentiment_and_sfx(self, transcript_text: str):
        logger.info("Running sentiment & sound suggestion analysis...")
        emotion_data = analyze_emotions(transcript_text)
        sfx_suggestions = suggest_sound_effects(emotion_data)
        return {"emotions": emotion_data, "sound_effects": sfx_suggestions}
