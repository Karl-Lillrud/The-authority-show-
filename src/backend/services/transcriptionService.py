#src/backend/services/transcriptionService.py
import os
import openai
import logging
from datetime import datetime
from io import BytesIO
from elevenlabs.client import ElevenLabs
from backend.database.mongo_connection import fs
from backend.utils.ai_utils import remove_filler_words
from backend.utils.text_utils import generate_ai_suggestions, generate_show_notes, generate_ai_quotes, generate_quote_image

logger = logging.getLogger(__name__)
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

class TranscriptionService:
    def transcribe_audio(self, file_data: bytes, filename: str) -> dict:
        # 1. Save file to MongoDB
        file_id = fs.put(
            file_data,
            filename=filename,
            metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"},
        )
        logger.info(f"📥 File saved to MongoDB with ID: {file_id}")

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

        raw_transcription = []
        speaker_map = {}
        speaker_counter = 1

        # 3. Attempt to build word-level transcription
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

        # 4. Fallback if word-level fails
        if not raw_transcription:
            logger.warning("⚠️ No word-level transcription found. Using fallback.")
            fallback_sentences = transcription_text.split(".")
            raw_transcription = [
                f"Speaker 1: {sentence.strip()}" for sentence in fallback_sentences if sentence.strip()
            ]

        # 5. AI enhancements
        logger.info(f"🧽 Running filler-word removal...")
        transcription_no_fillers = remove_filler_words(transcription_text)

        logger.info(f"💡 Generating AI suggestions...")
        ai_suggestions = generate_ai_suggestions(transcription_text)

        logger.info(f"📝 Generating show notes...")
        show_notes = generate_show_notes(transcription_text)

        logger.info(f"📝 Generating quotes notes...")
        quotes_text = generate_ai_quotes(transcription_text)

        if isinstance(quotes_text, str):
            quotes_list = quotes_text.split("\n\n")
        else:
            quotes_list = quotes_text

        quote_images = [generate_quote_image(quote) for quote in quotes_list if quote.strip()]

        return {
            "file_id": str(file_id),
            "raw_transcription": " ".join(raw_transcription),
            "transcription_no_fillers": transcription_no_fillers,
            "ai_suggestions": ai_suggestions,
            "show_notes": show_notes,
            "quotes": quotes_text,
            "quote_images": quote_images,
        }

    def translate_text(self, text: str, language: str) -> str:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": f"Translate this to {language}:\n{text}"}],
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            return f"Error: {str(e)}"

