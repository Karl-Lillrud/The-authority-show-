# transcription_service.py
import logging
import os
import openai
from datetime import datetime
from io import BytesIO
from backend.database.mongo_connection import fs
from backend.utils.ai_utils import remove_filler_words, analyze_sentiment
from backend.utils.text_utils import generate_ai_suggestions, generate_show_notes
from bson import ObjectId

logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self, elevenlabs_client):
        """
        :param elevenlabs_client: The ElevenLabs() client you’re using for speech_to_text.
        """
        self.elevenlabs_client = elevenlabs_client

    def transcribe_file(self, file_data: bytes, filename: str, is_video: bool) -> dict:
        """
        Transcribes an audio or video file. If video, you can extract audio first, then transcribe.
        """
        # 1. If video, extract audio via FFmpeg. Otherwise, read direct.
        # 2. Save file to MongoDB if needed. Example:
        file_id = fs.put(
            file_data,
            filename=filename,
            metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"},
        )
        logger.info(f"File saved to MongoDB with ID: {file_id}")

        # 3. Actually transcribe with ElevenLabs
        audio_data = BytesIO(file_data)  # wrap in BytesIO
        transcription_result = self.elevenlabs_client.speech_to_text.convert(
            file=audio_data,
            model_id="scribe_v1",
            num_speakers=2,
            diarize=True,
            timestamps_granularity="word",
        )

        # 4. Build raw transcription text with timestamps
        raw_transcription = []
        speaker_map = {}
        speaker_counter = 1

        for word_info in transcription_result.words:
            word = word_info.text.strip()
            speaker_id = word_info.speaker_id
            if speaker_id not in speaker_map:
                speaker_map[speaker_id] = f"Speaker {speaker_counter}"
                speaker_counter += 1

            if word:
                raw_transcription.append(
                    f"[{word_info.start}-{word_info.end}] {speaker_map[speaker_id]}: {word}"
                )

        # 5. Create AI suggestions & show notes
        transcription_text = transcription_result.text.strip()
        ai_suggestions = generate_ai_suggestions(transcription_text)
        show_notes = generate_show_notes(transcription_text)

        return {
            "raw_transcription": " ".join(raw_transcription),
            "ai_suggestions": ai_suggestions,
            "show_notes": show_notes,
            "file_id": str(file_id)
        }

    def translate_text(self, text: str, target_language: str) -> str:
        """
        Translate text using GPT-4 or any other approach.
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": f"Translate this to {target_language}:\n{text}"}
                ],
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            return f"Error: {str(e)}"
