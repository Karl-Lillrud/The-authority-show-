#src/backend/services/transcriptionService.py
import os
import logging
import re
import time
import tempfile
import httpx
from typing import Optional, Dict
from elevenlabs import ElevenLabs
from pydub import AudioSegment, effects
from datetime import datetime, timezone
from typing import List
from io import BytesIO
from elevenlabs.client import ElevenLabs
from pydub.exceptions import CouldntDecodeError
from backend.repository.edit_repository import get_edit_by_id, save_transcription_edit
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
    def transcribe_audio(self, file_data: bytes, filename: str, user_id: str, episode_id: str) -> dict:
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

        edit_id = save_transcription_edit(
            user_id=user_id,
            episode_id=episode_id,
            transcript_text=full_text,
            raw_transcript=raw_transcription,
            sentiment={"overall": "neutral"},
            emotion={"overall": "neutral"},
            filename=filename
        )

        return {
            "file_id": str(file_id),
            "raw_transcription": raw_transcription,
            "full_transcript": full_text,
            "word_timestamps": word_timings,
            "edit_id": str(edit_id)
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
            if idx < len(placeholder_map):
                placeholder, prefix = placeholder_map[idx]
            else:
                placeholder, prefix = "", ""
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
    

    def generate_audio_from_translated(
        self,
        raw_transcription: str,
        language: str,
        voice_id: str
    ) -> bytes:
        """
        Generate audio from translated transcription using a cloned voice.
        """
        try:
            logger.info(f"Starting audio generation from translation. Language: {language}, Voice ID: {voice_id}")
            if not raw_transcription:
                raise ValueError("No raw transcription provided")
            if not language:
                raise ValueError("No language specified")
            if not voice_id:
                raise ValueError("No voice ID provided")

            segments = self.build_segments_from_raw(raw_transcription)
            segments.sort(key=lambda s: s["start"])
            if not segments:
                raise ValueError("No valid segments in raw_transcription.")
            logger.info(f"Built {len(segments)} segments from transcription")

            total_ms = int(max(s["end"] for s in segments) * 1000)
            final = AudioSegment.silent(duration=total_ms)

            for i, seg in enumerate(segments):
                try:
                    start_ms = int(seg["start"] * 1000)
                    end_ms = int(seg["end"] * 1000)
                    text = seg["text"]
                    logger.info(f"Processing segment {i+1}/{len(segments)}: {start_ms}-{end_ms} ms, text='{text[:40]}...'")
                    target_dur = end_ms - start_ms
                    if target_dur <= 0:
                        logger.warning(f"Segment at {seg['start']}s has duration {target_dur} ms – skipping")
                        continue

                    tts_bytes = None
                    try:
                        logger.info(f"Calling ElevenLabs TTS API for segment {i+1}")
                        tts_stream = client.text_to_speech.convert(
                            text=text,
                            voice_id=voice_id,
                            model_id="eleven_multilingual_v2",
                            output_format="mp3_44100_128"
                        )
                        if tts_stream is None:
                            raise Exception("TTS stream was None (SDK bug or API fail)")
                        tts_bytes = b"".join(tts_stream) if hasattr(tts_stream, '__iter__') else tts_stream
                        logger.info(f"TTS bytes length for segment {i+1}: {len(tts_bytes) if tts_bytes else 'None'}")
                        # Save TTS output for debugging
                        debug_path = f"tts_debug_segment_{i+1}.mp3"
                        with open(debug_path, "wb") as f:
                            f.write(tts_bytes)
                        logger.info(f"Saved TTS debug file: {debug_path}")
                        # Delete the debug file after logging
                        try:
                            os.remove(debug_path)
                            logger.info(f"Deleted TTS debug file: {debug_path}")
                        except Exception as e:
                            logger.warning(f"Could not delete debug file {debug_path}: {e}")
                        if not tts_bytes or len(tts_bytes) < 1000:
                            raise Exception("Stream returned too little data – fallback triggered")
                    except Exception as e:
                        logger.error(f"TTS error for segment {i+1}: {e}", exc_info=True)
                        continue

                    try:
                        logger.info(f"Loading audio segment {i+1} with pydub")
                        tts_audio = AudioSegment.from_file(BytesIO(tts_bytes), format="mp3")
                        actual = len(tts_audio)
                        logger.info(f"Loaded audio segment {i+1} with duration {actual} ms (target: {target_dur} ms)")
                        if actual > target_dur:
                            speed = actual / target_dur
                            tts_audio = effects.speedup(tts_audio, playback_speed=speed)
                        else:
                            tts_audio += AudioSegment.silent(duration=(target_dur - actual))
                        final = final.overlay(tts_audio, position=start_ms)
                        logger.info(f"Overlayed segment {i+1} at {start_ms} ms")
                    except Exception as e:
                        logger.error(f"Error processing audio segment {i+1}: {e}", exc_info=True)
                        continue

                    logger.info(f"Finished processing segment {i+1}")
                except Exception as e:
                    logger.error(f"Error in segment {i+1}: {e}", exc_info=True)
                    continue
            logger.info("All segments processed, exporting final audio")
            buf = BytesIO()
            try:
                final.export(buf, format="mp3")
                logger.info("Exported final audio successfully")
            except Exception as e:
                logger.error(f"Error exporting final audio: {e}", exc_info=True)
                raise
            return buf.getvalue()
        except Exception as e:
            logger.error(f"Fatal error in generate_audio_from_translated: {e}", exc_info=True)
            raise

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
    
    def clone_user_voice(self, file_data: bytes, user_id: str, voice_name: str = None) -> str:
        voice_name = voice_name or f"{user_id}_voice"
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(file_data)
                tmp.flush()
                tmp_path = tmp.name

            # Call SDK, which will open/close the file internally
            voice = client.clone(
                name=voice_name,
                description="Cloned via PodManager AI",
                files=[tmp_path]
            )
            return voice.voice_id

        finally:
            if tmp_path and os.path.exists(tmp_path):
                # Windows kan låsa filen kort efter SDK-anrop, så vi väntar och försöker igen om det krävs
                for _ in range(5):
                    try:
                        os.remove(tmp_path)
                        break
                    except PermissionError:
                        time.sleep(0.2)

