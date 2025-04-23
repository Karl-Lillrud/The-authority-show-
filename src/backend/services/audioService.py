import os
import logging
import tempfile
import requests
import subprocess
from pydub import AudioSegment, silence
from backend.database.mongo_connection import get_fs
from backend.utils.file_utils import enhance_audio_with_ffmpeg, detect_background_noise, convert_audio_to_wav
from backend.utils.ai_utils import (
    remove_filler_words, calculate_clarity_score, analyze_sentiment,analyze_emotions
)
from backend.utils.text_utils import (
    transcribe_with_whisper, detect_filler_words, classify_sentence_relevance,
    analyze_certainty_levels, get_sentence_timestamps, detect_long_pauses,
    generate_ai_show_notes, suggest_sound_effects,translate_text
)
from backend.repository.ai_models import save_file, get_file_data, get_file_by_id, add_audio_edit_to_episode
from elevenlabs.client import ElevenLabs

logger = logging.getLogger(__name__)
fs = get_fs()

class AudioService:
    def enhance_audio(self, audio_bytes: bytes, filename: str, episode_id: str) -> str:
        # 1. Save input to temp WAV file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            temp_in_path = tmp.name

        # 2. Prepare output path
        temp_out_path = temp_in_path.replace(".wav", "_enhanced.wav")
        success = enhance_audio_with_ffmpeg(temp_in_path, temp_out_path)

        if not success:
            raise RuntimeError("FFmpeg enhancement failed")

        # 3. Read enhanced data
        with open(temp_out_path, "rb") as f:
            enhanced_data = f.read()

        # 4. Save to GridFS
        enhanced_file_id = save_file(
            enhanced_data,
            filename=f"enhanced_{filename}",
            metadata={"type": "audio", "enhanced": True}
        )

        # 5. Add reference to episode
        add_audio_edit_to_episode(
            episode_id=episode_id,
            file_id=enhanced_file_id,
            edit_type="enhanced",
            filename=f"enhanced_{filename}",
            metadata={"source": filename, "enhanced": True}
        )

        # 6. Cleanup temp files
        os.remove(temp_in_path)
        os.remove(temp_out_path)

        return enhanced_file_id

    def analyze_audio(self, audio_bytes: bytes):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            temp_path = tmp.name

        transcript = transcribe_with_whisper(temp_path)
        cleaned = remove_filler_words(transcript)
        clarity_score = calculate_clarity_score(cleaned)
        noise_result = detect_background_noise(temp_path)
        sentiment_result = analyze_sentiment(transcript)

        # NEW: Sentence-level emotion + sound suggestion
        translated_text = translate_text(transcript, "English")
        emotion_data = analyze_emotions(translated_text)
        sound_effects = suggest_sound_effects(emotion_data)

        os.remove(temp_path)

        return {
            "transcript": transcript,
            "cleaned_transcript": cleaned,
            "clarity_score": clarity_score,
            "background_noise": noise_result,
            "sentiment": sentiment_result,
            "emotions": emotion_data,            # NEW
            "sound_effect_suggestions": sound_effects  # NEW
        }

    def cut_audio(self, file_id: str, start_time: float, end_time: float) -> str:
        logger.info(f"📥 Request to clip audio file with ID: {file_id}")
        logger.info(f"🕒 Timestamps to clip: start={start_time}, end={end_time}")

        if start_time is None or end_time is None or start_time >= end_time:
            raise ValueError("Invalid timestamps.")

        clipped_filename = f"clipped_{file_id}.wav"
        existing = fs.find_one({"filename": clipped_filename})
        if existing:
            logger.info(f"✅ Clipped version exists: {existing._id}")
            return str(existing._id)

        audio_data = get_file_data(file_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_in:
            tmp_in.write(audio_data)
            input_path = tmp_in.name

        output_path = input_path.replace(".wav", "_clipped.wav")

        try:
            ffmpeg_cmd = f'ffmpeg -y -i "{input_path}" -ss {start_time} -to {end_time} -c copy "{output_path}"'
            subprocess.run(ffmpeg_cmd, shell=True, check=True)

            with open(output_path, "rb") as f:
                clipped_data = f.read()

            clipped_file_id = save_file(
                clipped_data,
                filename=clipped_filename,
                metadata={"type": "transcription", "clipped": True}
            )

            logger.info(f"✅ Clipped audio saved with ID: {clipped_file_id}")
            return clipped_file_id

        finally:
            for path in [input_path, output_path]:
                if os.path.exists(path):
                    os.remove(path)

    def ai_cut_audio(self, file_bytes: bytes, filename: str) -> dict:
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".mp3", ".wav"]:
            raise ValueError("Unsupported audio format")

        temp_path = (
            convert_audio_to_wav(file_bytes, original_ext=ext)
            if ext == ".mp3"
            else tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
        )

        if ext == ".wav":
            with open(temp_path, "wb") as f:
                f.write(file_bytes)

        logger.info(f"📥 AI Cut: Temp file at {temp_path}")

        try:
            client = ElevenLabs()
            with open(temp_path, "rb") as f:
                audio_bytes = f.read()

            result = client.speech_to_text.convert(
                file=audio_bytes,
                model_id="scribe_v1",
                num_speakers=2,
                diarize=True,
                timestamps_granularity="word"
            )

            transcript = result.text.strip()
            word_timings = [
                {"word": w.text, "start": w.start, "end": w.end}
                for w in result.words
                if hasattr(w, "start") and hasattr(w, "end")
            ]

            cleaned_transcript = remove_filler_words(transcript)
            noise_result = detect_background_noise(temp_path)
            filler_sentences = detect_filler_words(transcript)
            sentence_certainty = analyze_certainty_levels(transcript)

            logger.info(f"📊 Certainty results: {sentence_certainty}")

            sentence_timestamps = []
            audio = AudioSegment.from_wav(temp_path)
            cut_file_ids = []

            for idx, entry in enumerate(sentence_certainty):
                logger.info(f"🔍 Sentence {idx}: {entry['sentence']} | Certainty: {entry.get('certainty')}")
                if entry["certainty"] <= 0:
                    continue

                timestamps = get_sentence_timestamps(entry["sentence"], word_timings)
                start_ms = int(timestamps["start"] * 1000)
                end_ms = int(timestamps["end"] * 1000)

                entry.update({
                    "start": timestamps["start"],
                    "end": timestamps["end"],
                    "id": idx
                })

                sentence_timestamps.append({
                    "id": idx,
                    "sentence": entry["sentence"],
                    "start": timestamps["start"],
                    "end": timestamps["end"]
                })

                cut = audio[start_ms:end_ms]
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    cut.export(tmp.name, format="wav")
                    tmp_path = tmp.name

                with open(tmp_path, "rb") as f:
                    file_id = save_file(
                        f.read(),
                        filename=f"cut_{idx}.wav",
                        metadata={"type": "ai_cut", "source": filename}
                    )
                    cut_file_ids.append(file_id)

                os.remove(tmp_path)

            sentiment = analyze_sentiment(transcript)
            show_notes = generate_ai_show_notes(transcript)

            return {
                "message": "✅ AI Audio processing completed with clips",
                "cleaned_transcript": cleaned_transcript,
                "background_noise": noise_result,
                "filler_sentences": filler_sentences,
                "sentence_certainty_scores": sentence_certainty,
                "sentence_timestamps": sentence_timestamps,
                "suggested_cuts": [
                    {
                        "sentence": e["sentence"],
                        "certainty_level": e["certainty_level"],
                        "certainty_score": e["certainty"],
                        "start": e["start"],
                        "end": e["end"]
                    } for e in sentence_certainty if e["certainty"] >= 0.1
                ],
                "sentiment": sentiment,
                "long_pauses": detect_long_pauses(temp_path),
                "ai_show_notes": show_notes,
                "cut_file_ids": cut_file_ids
            }

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            logger.info(f"🗑️ Temp file cleaned up: {temp_path}")

    def ai_cut_audio_from_id(self, file_id: str) -> dict:
        audio_bytes, filename = get_file_by_id(file_id)
        return self.ai_cut_audio(audio_bytes, filename)
    
    def isolate_voice(self, audio_bytes: bytes, filename: str, episode_id: str) -> str:
        """
        Use ElevenLabs Audio Isolation API to extract vocals and save result to MongoDB.
        """
        logger.info(f"🎙️ Starting voice isolation for file: {filename}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            temp_path = tmp.name

        try:
            logger.info("🔄 Sending audio to ElevenLabs voice isolation endpoint...")

            with open(temp_path, "rb") as f:
                response = requests.post(
                    "https://api.elevenlabs.io/v1/audio-isolation",
                    headers={"xi-api-key": os.getenv("ELEVENLABS_API_KEY")},
                    files={"audio": f}
                )

            if response.status_code != 200:
                logger.error(f"❌ Voice isolation failed: {response.status_code} {response.text}")
                raise RuntimeError(f"Voice isolation failed: {response.status_code} {response.text}")

            isolated_audio = response.content
            isolated_filename = f"isolated_{filename}"

            file_id = save_file(
                isolated_audio,
                filename=isolated_filename,
                metadata={"type": "voice_isolated", "source": filename}
            )

            # 🧠 Save to episode's audioEdits
            add_audio_edit_to_episode(
                episode_id=episode_id,
                file_id=file_id,
                edit_type="voice_isolated",
                filename=isolated_filename,
                metadata={"source": filename}
            )

            logger.info(f"✅ Isolated voice saved to MongoDB with ID: {file_id}")
            return file_id

        finally:
            os.remove(temp_path)


    def split_audio_on_silence(wav_path, min_len=500, silence_thresh_db=-35):
        audio = AudioSegment.from_wav(wav_path)
        chunks = silence.split_on_silence(
            audio,
            min_silence_len=min_len,
            silence_thresh=audio.dBFS + silence_thresh_db,
            keep_silence=200  # pad before and after
        )
        return chunks

    def apply_cuts_and_return_new_file(self, file_id: str, cuts: list[dict]) -> str:
        """
        Keeps only the specified segments and returns a new file.
        cuts = [{ "start": float, "end": float }, ...]
        """
        logger.info(f"✂️ Applying cuts to file ID: {file_id}")
        audio_data = get_file_data(file_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            audio = AudioSegment.from_wav(tmp_path)
            duration_ms = len(audio)
            logger.info(f"📏 Original audio duration: {duration_ms / 1000:.2f}s")

            # Sort cuts and convert to milliseconds
            cuts_ms = sorted([(int(c['start'] * 1000), int(c['end'] * 1000)) for c in cuts])
            logger.info(f"✅ Cuts to keep (ms): {cuts_ms}")

            # Keep only those segments
            kept_segments = [audio[start:end] for start, end in cuts_ms]
            cleaned_audio = sum(kept_segments)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as out_tmp:
                cleaned_path = out_tmp.name
                cleaned_audio.export(cleaned_path, format="wav")

            with open(cleaned_path, "rb") as f:
                cleaned_bytes = f.read()

            cleaned_file_id = save_file(
                cleaned_bytes,
                filename=f"cleaned_{file_id}.wav",
                metadata={"type": "ai_cut_cleaned", "source": file_id, "segments_kept": len(cuts)}
            )

            logger.info(f"✅ Cleaned file saved with ID: {cleaned_file_id}")
            return cleaned_file_id

        finally:
            for path in [tmp_path, cleaned_path]:
                if os.path.exists(path):
                    os.remove(path)

