#src/backend/services/transcriptionService.py
import os
import re
import logging
from datetime import datetime
from io import BytesIO
from typing import List
from elevenlabs.client import ElevenLabs
from pydub import AudioSegment, effects
from backend.database.mongo_connection import fs
from backend.utils.ai_utils import remove_filler_words, analyze_emotions
from backend.utils.text_utils import (
    generate_ai_suggestions, generate_show_notes, generate_ai_quotes,
    generate_quote_images, translate_text, suggest_sound_effects
)

logger = logging.getLogger(__name__)
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

VOICE_MAP = {
    'English': {
        'Speaker 1': os.getenv('VOICE_ID_EN_1'),
        'Speaker 2': os.getenv('VOICE_ID_EN_2'),
    },
    'Spanish': {
        'Speaker 1': os.getenv('VOICE_ID_ES_1'),
        'Speaker 2': os.getenv('VOICE_ID_ES_2'),
    },
    # Add more languages and voices as needed
}

class TranscriptionService:
    def transcribe_audio(self, file_data: bytes, filename: str) -> dict:
        file_id = fs.put(
            file_data,
            filename=filename,
            metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"}
        )
        logger.info(f"📥 File saved to MongoDB with ID: {file_id}")

        transcription_result = client.speech_to_text.convert(
            file=BytesIO(file_data),
            model_id="scribe_v1",
            diarize=True,
            num_speakers=2,
            timestamps_granularity="word"
        )
        if not transcription_result.text:
            raise Exception("Transcription returned no text.")

        segments = []
        speaker_map = {}
        speaker_counter = 1
        buffer = []
        buffer_speaker = None

        def flush_buffer():
            nonlocal buffer, buffer_speaker, speaker_counter
            if not buffer:
                return
            start = round(buffer[0].start, 2)
            end = round(buffer[-1].end, 2)
            text = ' '.join(w.text.strip() for w in buffer).strip()
            sid = buffer_speaker
            if sid not in speaker_map:
                speaker_map[sid] = f"Speaker {speaker_counter}"
                speaker_counter += 1
            speaker_label = speaker_map[sid]
            segments.append({
                'start': start,
                'end': end,
                'speaker': speaker_label,
                'text': text
            })
            buffer = []

        for w in transcription_result.words:
            sid = w.speaker_id
            if buffer and sid != buffer_speaker:
                flush_buffer()
            buffer.append(w)
            buffer_speaker = sid
            if re.search(r"[\.\!\?]$", w.text.strip()):
                flush_buffer()
        flush_buffer()

        return {"file_id": str(file_id), "segments": segments}

    def translate_segments(self, segments: list, target_language: str) -> list:
        translated = []
        for seg in segments:
            tr_text = translate_text(seg['text'], target_language)
            translated.append({**seg, 'text': tr_text})
        return translated

    def generate_audio_from_segments(self, segments: list, language: str) -> bytes:
        voices = VOICE_MAP.get(language)
        if not voices:
            raise ValueError(f"No voices configured for {language}")

        final_audio = AudioSegment.silent(duration=0)
        current_time = 0

        for seg in segments:
            seg_start_ms = int(seg['start'] * 1000)
            seg_end_ms = int(seg['end'] * 1000)
            target_duration = seg_end_ms - seg_start_ms

            gap = seg_start_ms - current_time
            if gap > 0:
                final_audio += AudioSegment.silent(duration=gap)
                current_time += gap

            speaker = seg['speaker']
            voice_id = voices.get(speaker) or list(voices.values())[0]
            if not voice_id:
                raise ValueError(f"No voice_id configured for speaker {speaker} in language {language}")

            tts_stream = client.text_to_speech.convert(
                text=seg['text'],
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            # If convert() returns generator, join into bytes
            tts_bytes = b"".join(tts_stream)
            tts_audio = AudioSegment.from_file(BytesIO(tts_bytes), format="mp3")

            actual_dur = len(tts_audio)
            if actual_dur > target_duration:
                speed = actual_dur / target_duration
                tts_audio = effects.speedup(tts_audio, playback_speed=speed)
            elif actual_dur < target_duration:
                pad = target_duration - actual_dur
                tts_audio += AudioSegment.silent(duration=pad)

            final_audio += tts_audio
            current_time += len(tts_audio)

        buf = BytesIO()
        final_audio.export(buf, format="mp3")
        return buf.getvalue()

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
