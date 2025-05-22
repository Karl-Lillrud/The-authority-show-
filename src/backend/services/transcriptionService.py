#src/backend/services/transcriptionService.py
import os
import logging
import re
from pydub import AudioSegment, effects
from datetime import datetime, timezone
from typing import List
from io import BytesIO
from elevenlabs.client import ElevenLabs
from backend.database.mongo_connection import fs
from backend.utils.ai_utils import (
    generate_ai_suggestions,
    generate_show_notes,
    generate_ai_quotes,
    generate_quote_images_dalle,
    render_quote_images_local,
    translate_text,
    suggest_sound_effects,
    remove_filler_words, 
    analyze_emotions
)

logger = logging.getLogger(__name__)
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

VOICE_MAPS = {
    "English": {
        "Speaker 1": os.getenv("VOICE_ID_EN_1"),
        "Speaker 2": os.getenv("VOICE_ID_EN_2"),
        "Speaker 3": os.getenv("VOICE_ID_EN_3"),
        "Speaker 4": os.getenv("VOICE_ID_EN_4"),
    },
    "Spanish": {
        "Speaker 1": os.getenv("VOICE_ID_ES_1"),
        "Speaker 2": os.getenv("VOICE_ID_ES_2"),
        "Speaker 3": os.getenv("VOICE_ID_ES_3"),
        "Speaker 4": os.getenv("VOICE_ID_ES_4"),
    },
}


class TranscriptionService:
    def transcribe_audio(self, file_data: bytes, filename: str) -> dict:
        """
        Transcribes audio and groups words into sentences with accurate timestamps.
        """

        logger.info("Starting transcription (group by sentence)")

        # === steg 1: ElevenLabs-transkription (word granularity) ===
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
        full_text = transcription_result.text.strip()

        # === steg 2: spara fil i GridFS ===
        file_id = fs.put(
            file_data,
            filename=filename,
            metadata={"upload_timestamp": datetime.now(timezone.utc), "type": "transcription"}
        )

        # === steg 3: bygg per-ord-lista och speaker_map ===
        word_timings = []
        speaker_map = {}
        speaker_counter = 1
        for w in transcription_result.words:
            txt = w.text.strip()
            if not txt:
                continue
            start = round(w.start, 2)
            end = round(w.end, 2)
            word_timings.append({
                "word": txt,
                "start": start,
                "end": end,
                "speaker_id": w.speaker_id
            })
            if w.speaker_id not in speaker_map:
                speaker_map[w.speaker_id] = f"Speaker {speaker_counter}"
                speaker_counter += 1

        # === steg 4: dela full_text i meningar ===
        sentences = re.split(r'(?<=[\.\?\!])\s+', full_text)

        # === steg 5: gruppera ord till meningar ===
        raw_entries = []  # (start_time, end_time, speaker, sentence_text)
        idx = 0
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            words = sent.split()
            # hitta start/end för mening baserat på ord_timings sekventiellt
            # start = first matching word start, end = last matching word end
            start_time, end_time = None, None
            speaker = None
            for w in word_timings[idx:]:
                if w["word"] == words[0] and start_time is None:
                    start_time = w["start"]
                if start_time is not None:
                    # mappa speaker från första ord
                    if speaker is None:
                        speaker = speaker_map[w["speaker_id"]]
                    if w["word"] == words[-1]:
                        end_time = w["end"]
                        # flytta idx framåt för nästa sentence
                        idx = word_timings.index(w) + 1
                        break
            # fallback om ej hittat
            if start_time is None or end_time is None:
                continue
            raw_entries.append((start_time, end_time, speaker or "Speaker 1", sent))

        # === steg 6: format och sortera ===
        raw_entries.sort(key=lambda x: x[0])
        raw_lines = [f"[{s:.2f}-{e:.2f}] {sp}: {txt}" for s, e, sp, txt in raw_entries]
        raw_transcription = "\n".join(raw_lines)

        return {
            "file_id": str(file_id),
            "raw_transcription": raw_transcription,
            "full_transcript": full_text
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
        q = generate_ai_quotes(transcript_text)
        return str(q)

    def get_quote_images(self, quotes: List[str], method: str = "dalle") -> List[str]:
        if method == "local":
            return render_quote_images_local(quotes)
        else:
            return generate_quote_images_dalle(quotes)

    def translate_transcript(self, raw_transcription: str, target_language: str) -> str:
        """
        Translate the entire raw_transcription in one go (for speed), preserving
        timestamps and speaker labels by using placeholders.
        """
        logger.info(f"Translating transcript to {target_language} (bulk) with timestamps and speakers…")
        lines = raw_transcription.split("\n")

        placeholder_map = []
        bulk_text_parts = []
        for idx, line in enumerate(lines):
            m = re.match(r"^(\[[0-9]+\.[0-9]{2}-[0-9]+\.[0-9]{2}\]\s*Speaker\s*\d+:)\s*(.*)$", line)
            if m:
                prefix, body = m.groups()
            else:
                prefix, body = "", line

            placeholder = f"__LINE{idx}__"
            placeholder_map.append((placeholder, prefix))
            bulk_text_parts.append(body or placeholder)
        bulk_text = "\n".join(bulk_text_parts)

        try:
            translated_bulk = translate_text(bulk_text, target_language)
        except Exception as e:
            logger.warning(f"Bulk translation failed: {e}")
            return "\n".join(self._translate_line_by_line(lines, target_language))

        translated_lines = translated_bulk.split("\n")
        final_lines = []
        for idx, translated_body in enumerate(translated_lines):
            placeholder, prefix = placeholder_map[idx]
            if prefix:
                final_lines.append(f"{prefix} {translated_body}")
            else:
                final_lines.append(translated_body)

        return "\n".join(final_lines)

    def get_sentiment_and_sfx(self, transcript_text: str):
        logger.info("Running sentiment & sound suggestion analysis...")
        emotion_data = analyze_emotions(transcript_text)
        sfx_suggestions = suggest_sound_effects(emotion_data)
        return {"emotions": emotion_data, "sound_effects": sfx_suggestions}
    
    def generate_audio_from_translated(self, raw_transcription: str, language: str) -> bytes:
     
        segments = self.build_segments_from_raw(raw_transcription)
        segments.sort(key=lambda s: s["start"])

        if not segments:
            raise ValueError("No valid segments in raw_transcription.")

        total_ms = int(max(s["end"] for s in segments) * 1000)

        final = AudioSegment.silent(duration=total_ms)

        voice_map = VOICE_MAPS.get(language)
        if not voice_map:
            raise ValueError(f"Inget voice_map för språk '{language}'")
    
        default_voice = next(iter(voice_map.values()), None)

        for seg in segments:
            start_ms = int(seg["start"] * 1000)
            end_ms   = int(seg["end"]   * 1000)
            text     = seg["text"]
            speaker  = seg["speaker"]

            voice_id = voice_map.get(speaker) or default_voice
            if not voice_id:
                raise ValueError(f"Ingen voice_id för {speaker} i {language}")

            target_dur = end_ms - start_ms
            if target_dur <= 0:
                logger.warning(f"Segment vid {seg['start']}s har längd {target_dur} ms – skippar")
                continue

            tts_stream = client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            tts_bytes = b"".join(tts_stream)
            tts_audio = AudioSegment.from_file(BytesIO(tts_bytes), format="mp3")

            actual = len(tts_audio)
            if actual > target_dur:
                speed = actual / target_dur
                tts_audio = effects.speedup(tts_audio, playback_speed=speed)
            else:
                tts_audio += AudioSegment.silent(duration=(target_dur - actual))

            final = final.overlay(tts_audio, position=start_ms)

        buf = BytesIO()
        final.export(buf, format="mp3")
        return buf.getvalue()
    
    def build_segments_from_raw(self, raw_transcription: str) -> List[dict]:
        segments = []
        pattern = re.compile(
            r"\[(?P<start>\d+(\.\d+)?)\-(?P<end>\d+(\.\d+)?)\]\s*"
            r"(?P<speaker>Speaker \d+):\s*(?P<text>.+)"
        )
        for line in raw_transcription.splitlines():
            m = pattern.match(line)
            if not m:
                continue
            segments.append({
                "start":   float(m.group("start")),
                "end":     float(m.group("end")),
                "speaker": m.group("speaker"),
                "text":    m.group("text").strip()
            })
        if not segments:
            raise ValueError("Ingen giltig segmentrad hittades i transcriptet.")
        return segments

    def _translate_line_by_line(self, lines: List[str], target_language: str) -> List[str]:
        """
        Tidigare beteende: översätt varje enskild rad separat.
        """
        translated = []
        for line in lines:
            m = re.match(r"^(\[.*?\]\s*Speaker\s*\d+:)\s*(.*)$", line)
            if m:
                prefix, body = m.groups()
            else:
                prefix, body = "", line

            try:
                trans = translate_text(body, target_language)
            except Exception as e:
                logger.warning(f"Translation failed for line '{body}': {e}")
                trans = body
            translated.append(f"{prefix} {trans}" if prefix else trans)
        return translated
    