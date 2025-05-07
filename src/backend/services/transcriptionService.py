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
    def __init__(self):
        self.speaker_genders = {}

    def detect_speaker_gender(self, file_data: bytes, segments: List[dict]) -> dict:
        # Stub: replace with real gender detection using audio model
        genders = {}
        for idx, seg in enumerate(segments):
            label = seg['speaker']
            if label not in genders:
                genders[label] = 'male' if idx % 2 == 0 else 'female'
        return genders

    def transcribe_audio(self, file_data: bytes, filename: str) -> dict:
        file_id = fs.put(
            file_data,
            filename=filename,
            metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"}
        )
        logger.info(f"📥 File saved to MongoDB with ID: {file_id}")

        result = client.speech_to_text.convert(
            file=BytesIO(file_data),
            model_id="scribe_v1",
            diarize=True,
            num_speakers=2,
            timestamps_granularity="word"
        )
        if not result.text:
            raise Exception("Transcription returned no text.")

        transcript_text = result.text.strip()
        # Build segments
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
            label = speaker_map[sid]
            segments.append({ 'start': start, 'end': end, 'speaker': label, 'text': text })
            buffer = []

        for w in result.words:
            sid = w.speaker_id
            if buffer and sid != buffer_speaker:
                flush_buffer()
            buffer.append(w)
            buffer_speaker = sid
            if re.search(r"[\.\!\?]$", w.text.strip()):
                flush_buffer()
        flush_buffer()

        # Detect speaker genders
        self.speaker_genders = self.detect_speaker_gender(file_data, segments)

        # Build raw_transcription text with timestamps
        raw_lines = [f"[{seg['start']}-{seg['end']}] {seg['speaker']}: {seg['text']}" for seg in segments]
        raw_transcription = "\n".join(raw_lines)

        return {
            "file_id": str(file_id),
            "segments": segments,
            "raw_transcription": raw_transcription,
            "full_transcript": transcript_text
        }

    def translate_segments(self, segments: List[dict], target_language: str) -> List[dict]:
        translated = []
        for seg in segments:
            tr = translate_text(seg['text'], target_language)
            translated.append({**seg, 'text': tr})
        return translated

    def generate_audio_from_segments(self, segments: List[dict], language: str) -> bytes:
        voices_cfg = VOICE_MAP.get(language)
        if not voices_cfg:
            raise ValueError(f"No voices configured for {language}")

        final_audio = AudioSegment.silent(duration=0)
        current_time = 0
        gender_counters = {'male': 0, 'female': 0}

        for seg in segments:
            start_ms = int(seg['start'] * 1000)
            end_ms = int(seg['end'] * 1000)
            target_dur = end_ms - start_ms
            gap = start_ms - current_time
            if gap > 0:
                final_audio += AudioSegment.silent(duration=gap)
                current_time += gap

            speaker = seg['speaker']
            gender = self.speaker_genders.get(speaker, 'female')
            voice_list = voices_cfg.get(gender, [])
            if not voice_list:
                raise ValueError(f"No voice IDs for gender {gender} in {language}")
            idx = gender_counters[gender] % len(voice_list)
            voice_id = voice_list[idx]
            gender_counters[gender] += 1

            # TTS convert stream to bytes
            tts_stream = client.text_to_speech.convert(
                text=seg['text'],
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            tts_bytes = b"".join(tts_stream)
            tts_audio = AudioSegment.from_file(BytesIO(tts_bytes), format="mp3")

            actual_dur = len(tts_audio)
            if actual_dur > target_dur:
                speed = actual_dur / target_dur
                tts_audio = effects.speedup(tts_audio, playback_speed=speed)
            elif actual_dur < target_dur:
                tts_audio += AudioSegment.silent(duration=(target_dur - actual_dur))

            final_audio += tts_audio
            current_time += len(tts_audio)

        buf = BytesIO()
        final_audio.export(buf, format="mp3")
        return buf.getvalue()

    def get_clean_transcript(self, transcript_text: str) -> str:
        return remove_filler_words(transcript_text)

    def get_ai_suggestions(self, transcript_text: str) -> str:
        return generate_ai_suggestions(transcript_text)

    def get_show_notes(self, transcript_text: str) -> str:
        return generate_show_notes(transcript_text)

    def get_quotes(self, transcript_text: str) -> str:
        qt = generate_ai_quotes(transcript_text)
        return qt if isinstance(qt, str) else str(qt)

    def get_quote_images(self, quotes: List[str]) -> List[str]:
        return generate_quote_images(quotes)

    def translate_text(self, text: str, language: str) -> str:
        return translate_text(text, language)

    def get_sentiment_and_sfx(self, transcript_text: str):
        em = analyze_emotions(transcript_text)
        return {"emotions": em, "sound_effects": suggest_sound_effects(em)}

