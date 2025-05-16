#src/backend/services/transcriptionService.py
import os
import openai
import logging
import re
from pydub import AudioSegment, effects
from datetime import datetime, timezone
from typing import List, Tuple
from io import BytesIO
from elevenlabs.client import ElevenLabs
from backend.database.mongo_connection import fs
from backend.utils.ai_utils import remove_filler_words, analyze_emotions
from backend.utils.text_utils import (
    generate_ai_suggestions,
    generate_show_notes,
    generate_ai_quotes,
    generate_quote_images_dalle,
    render_quote_images_local,
    translate_text,
    suggest_sound_effects,
    get_sentence_timestamps
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
        from io import BytesIO
        from datetime import datetime, timezone
        import re
        
        logger.info("Starting transcription")

        # === steg 1: ElevenLabs-transkription ===
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

        # === steg 2: spara fil i GridFS ===
        file_id = fs.put(
            file_data,
            filename=filename,
            metadata={"upload_timestamp": datetime.now(timezone.utc), "type": "transcription"}
        )

        # === steg 3: bygg word_timings + speaker_map ===
        speaker_map = {}
        speaker_counter = 1
        word_timings = []
        for w in transcription_result.words:
            txt = w.text.strip()
            if not txt:
                continue
            start = round(w.start, 2)
            end   = round(w.end,   2)
            word_timings.append({
                "word": txt,
                "start": start,
                "end": end,
                "speaker_id": w.speaker_id
            })
            if w.speaker_id not in speaker_map:
                speaker_map[w.speaker_id] = f"Speaker {speaker_counter}"
                speaker_counter += 1

        # === steg 4: dela upp i meningar och behåll kronologisk ordning ===
        sentences = re.split(r'(?<=[\.!?])\s+', transcription_text)
        raw_entries = []  # list of (start_time, line)
        prev_end_time = 0.0
        for sentence in sentences:
            sent = sentence.strip()
            if not sent:
                continue
            # hämta tidsintervall för meningen från ord-timings, baserat på föregående slut-tid
            ts = get_sentence_timestamps(sent, word_timings, prev_end_time)
            start, end = ts["start"], ts["end"]
            prev_end_time = end
            # hitta talare för första ordet i segmentet
            first = next((wt for wt in word_timings if wt["start"] == start), None)
            speaker = speaker_map.get(first["speaker_id"], "Speaker 1") if first else "Speaker 1"
            line = f"[{start:.2f}-{end:.2f}] {speaker}: {sent}"
            raw_entries.append((start, line))

        # === steg 5: fallback om ingen mening fångades ===
        if not raw_entries:
            for wt in word_timings:
                line = (
                    f"[{wt['start']:.2f}-{wt['end']:.2f}] "
                    f"{speaker_map[wt['speaker_id']]}: {wt['word']}"
                )
                raw_entries.append((wt["start"], line))

        # === steg 6: sortera per start-tid och slå ihop ===
        raw_entries.sort(key=lambda x: x[0])
        raw_lines = [line for _, line in raw_entries]
        raw_transcription = "\n".join(raw_lines)

        return {
            "file_id": str(file_id),
            "raw_transcription": raw_transcription,
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

        # 1) Extrahera prefix (timestamp+speaker) och ersätt textdelen med placeholder
        placeholder_map = []
        bulk_text_parts = []
        for idx, line in enumerate(lines):
            m = re.match(r"^(\[[0-9]+\.[0-9]{2}-[0-9]+\.[0-9]{2}\]\s*Speaker\s*\d+:)\s*(.*)$", line)
            if m:
                prefix, body = m.groups()
            else:
                # om formatet avviker, behandla hela raden som "body" (utan prefix)
                prefix, body = "", line

            placeholder = f"__LINE{idx}__"
            placeholder_map.append((placeholder, prefix))
            bulk_text_parts.append(body or placeholder)
            # vi lägger in placeholder även för tomma body så att antalet delar matchar
        bulk_text = "\n".join(bulk_text_parts)

        # 2) Kör en bulk-översättning på hela texten
        try:
            translated_bulk = translate_text(bulk_text, target_language)
        except Exception as e:
            logger.warning(f"Bulk translation failed: {e}")
            # fallback: gör rad-för-rad (originalmetoden)
            return "\n".join(self._translate_line_by_line(lines, target_language))

        # 3) Återsätt varje rad med prefix + översatt text
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
        # 1) Bygg och sortera segment
        segments = self.build_segments_from_raw(raw_transcription)
        segments.sort(key=lambda s: s["start"])

        # 2) Beräkna total längd (i ms)
        total_ms = int(max(s["end"] for s in segments) * 1000)

        # 3) Starta en “tyst” AudioSegment av total längd
        final = AudioSegment.silent(duration=total_ms)

        voice_map = VOICE_MAPS.get(language)
        if not voice_map:
            raise ValueError(f"Inget voice_map för språk '{language}'")

        # 4) Generera varje TTS och lägg ovanpå på rätt tidpunkt
        for seg in segments:
            start_ms = int(seg["start"] * 1000)
            end_ms   = int(seg["end"]   * 1000)
            text     = seg["text"]
            speaker  = seg["speaker"]
            voice_id = voice_map.get(speaker)
            if not voice_id:
                raise ValueError(f"Ingen voice_id för {speaker} i {language}")

            # TTS
            tts_stream = client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            tts_bytes = b"".join(tts_stream)
            tts_audio = AudioSegment.from_file(BytesIO(tts_bytes), format="mp3")

            # Anpassa längd
            target_dur = end_ms - start_ms
            actual     = len(tts_audio)
            if actual > target_dur:
                speed = actual / target_dur
                tts_audio = effects.speedup(tts_audio, playback_speed=speed)
            else:
                tts_audio += AudioSegment.silent(duration=(target_dur - actual))

            # Overlay på exakt start_ms
            final = final.overlay(tts_audio, position=start_ms)

        # 5) Exportera som MP3
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
    