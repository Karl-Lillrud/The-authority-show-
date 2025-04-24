import os, logging, tempfile, requests, subprocess, base64
from typing import Optional
from pydub import AudioSegment, silence
from backend.database.mongo_connection import get_fs
from backend.utils.file_utils import enhance_audio_with_ffmpeg, detect_background_noise, convert_audio_to_wav
from backend.utils.ai_utils import (
    remove_filler_words, calculate_clarity_score, analyze_sentiment, analyze_emotions
)
from backend.utils.text_utils import (
    transcribe_with_whisper, detect_filler_words, classify_sentence_relevance,
    analyze_certainty_levels, get_sentence_timestamps, detect_long_pauses,
    generate_ai_show_notes, suggest_sound_effects, translate_text, mix_background,
    pick_dominant_emotion, fetch_sfx_for_emotion
)
from backend.repository.ai_models import save_file, get_file_data, get_file_by_id, add_audio_edit_to_episode
from elevenlabs.client import ElevenLabs
from backend.utils.blob_storage import upload_file_to_blob
from backend.repository.episode_repository import EpisodeRepository
from flask import g

logger = logging.getLogger(__name__)
fs = get_fs()
episode_repo = EpisodeRepository()

class AudioService:
    def enhance_audio(self, audio_bytes: bytes, filename: str, episode_id: str) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            temp_in_path = tmp.name

        temp_out_path = temp_in_path.replace(".wav", "_enhanced.wav")
        success = enhance_audio_with_ffmpeg(temp_in_path, temp_out_path)

        if not success:
            raise RuntimeError("FFmpeg enhancement failed")

        with open(temp_out_path, "rb") as f:
            enhanced_data = f.read()

        podcast_id = episode_repo.get_podcast_id_by_episode(episode_id)
        blob_path = f"users/{g.user_id}/podcasts/{podcast_id}/episodes/{episode_id}/audio/enhanced_{filename}"
        blob_url = upload_file_to_blob("podmanagerfiles", blob_path, enhanced_data)

        add_audio_edit_to_episode(
            episode_id=episode_id,
            file_id="external",
            edit_type="enhanced",
            filename=f"enhanced_{filename}",
            metadata={"source": filename, "enhanced": True, "blob_url": blob_url}
        )

        os.remove(temp_in_path)
        os.remove(temp_out_path)

        return blob_url

    def analyze_audio(self, audio_bytes: bytes):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            temp_path = tmp.name

        try:
            # 1) Grunddata ---------------------------------------------------
            transcript    = transcribe_with_whisper(temp_path)
            cleaned       = remove_filler_words(transcript)
            clarity_score = calculate_clarity_score(cleaned)
            noise_result  = detect_background_noise(temp_path)
            sentiment     = analyze_sentiment(transcript)

            # 2) Emotion-analys ---------------------------------------------
            translated    = translate_text(transcript, "English")
            emotion_data  = analyze_emotions(translated)

            dominant      = pick_dominant_emotion(emotion_data)
            bg_b64        = fetch_sfx_for_emotion(dominant, "general")[0]   # 30 s-klipp

            # 3) Mixa bakgrunden under originalet ---------------------------
            merged_wav    = mix_background(audio_bytes, bg_b64, bg_gain_db=-50)

            #    👉 lägg till data-prefixet här!
            merged_b64    = "data:audio/wav;base64," + base64.b64encode(merged_wav).decode("utf-8")

            # 4) Returnera ---------------------------------------------------
            return {
                "transcript":         transcript,
                "cleaned_transcript": cleaned,
                "clarity_score":      clarity_score,
                "background_noise":   noise_result,
                "sentiment":          sentiment,
                "emotions":           emotion_data,
                "background_clip":    bg_b64,     # ett enda 30-sek-klipp
                "merged_audio":       merged_b64  # nu med korrekt prefix
            }

        finally:
            os.remove(temp_path)

    def cut_audio(self, file_id: str, start_time: float, end_time: float, episode_id: str) -> str:
        logger.info(f"📥 Request to clip audio file with ID: {file_id}")
        logger.info(f"🕒 Timestamps to clip: start={start_time}, end={end_time}")

        if start_time is None or end_time is None or start_time >= end_time:
            raise ValueError("Invalid timestamps.")

        audio_data = get_file_data(file_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_in:
            tmp_in.write(audio_data)
            input_path = tmp_in.name

        output_path = input_path.replace(".wav", "_clipped.wav")

        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", input_path,
                "-ss", str(start_time), "-to", str(end_time),
                "-c", "copy", output_path
            ], check=True)

            with open(output_path, "rb") as f:
                clipped_data = f.read()

            episode, status = episode_repo.get_episode(episode_id, user_id=None)
            if not episode or status != 200:
                raise ValueError(f"Episode {episode_id} not found")
            podcast_id = episode.get("podcast_id")
            user_id = episode.get("userid")
            filename = f"clipped_{file_id}.wav"

            blob_path = f"users/{user_id}/podcasts/{podcast_id}/episodes/{episode_id}/audio/{filename}"
            blob_url = upload_file_to_blob("podmanagerfiles", blob_path, clipped_data)

            add_audio_edit_to_episode(
                episode_id=episode_id,
                file_id="external",
                edit_type="manual_clip",
                filename=filename,
                metadata={"blob_url": blob_url, "start": start_time, "end": end_time}
            )

            return blob_url
        finally:
            for path in [input_path, output_path]:
                if os.path.exists(path):
                    os.remove(path)


    def ai_cut_audio(self, file_bytes: bytes, filename: str, episode_id: Optional[str] = None) -> dict:
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

    def ai_cut_audio_from_id(self, file_id: str, episode_id: Optional[str] = None) -> dict:
        audio_bytes, filename = get_file_by_id(file_id)
        return self.ai_cut_audio(audio_bytes, filename, episode_id=episode_id)
    
    def isolate_voice(self, audio_bytes: bytes, filename: str, episode_id: str) -> str:
        logger.info(f"🎙️ Starting voice isolation for file: {filename}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            temp_input_path = tmp.name

        try:
            logger.info("🔄 Sending audio to ElevenLabs voice isolation endpoint...")

            with open(temp_input_path, "rb") as f:
                response = requests.post(
                    "https://api.elevenlabs.io/v1/audio-isolation",
                    headers={"xi-api-key": os.getenv("ELEVENLABS_API_KEY")},
                    files={"audio": f}
                )

            if response.status_code != 200:
                logger.error(f"❌ Voice isolation failed: {response.status_code} {response.text}")
                raise RuntimeError(f"Voice isolation failed: {response.status_code} {response.text}")

            # Spara det isolerade ljudet till temporär fil
            temp_output_path = temp_input_path.replace(".wav", "_isolated.wav")
            with open(temp_output_path, "wb") as out_file:
                out_file.write(response.content)

            with open(temp_output_path, "rb") as f:
                isolated_data = f.read()

            isolated_filename = f"isolated_{filename}"
            repo = EpisodeRepository()
            podcast_id = repo.get_podcast_id_by_episode(episode_id)

            blob_path = f"users/{g.user_id}/podcasts/{podcast_id}/episodes/{episode_id}/audio/{isolated_filename}"
            blob_url = upload_file_to_blob("podmanagerfiles", blob_path, isolated_data)

            add_audio_edit_to_episode(
                episode_id=episode_id,
                file_id="external",
                edit_type="voice_isolated",
                filename=isolated_filename,
                metadata={"source": filename, "blob_url": blob_url}
            )

            logger.info(f"✅ Isolated voice uploaded to Azure: {blob_url}")
            return blob_url

        finally:
            os.remove(temp_input_path)
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)


    def split_audio_on_silence(wav_path, min_len=500, silence_thresh_db=-35):
        audio = AudioSegment.from_wav(wav_path)
        chunks = silence.split_on_silence(
            audio,
            min_silence_len=min_len,
            silence_thresh=audio.dBFS + silence_thresh_db,
            keep_silence=200  # pad before and after
        )
        return chunks

    def apply_cuts_and_return_new_file(self, file_id: str, cuts: list[dict], episode_id: str) -> str:
        logger.info(f"✂️ Applying cuts to file ID: {file_id}")
        audio_data = get_file_data(file_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            audio = AudioSegment.from_wav(tmp_path)
            duration_ms = len(audio)
            cuts_ms = sorted([
                (int(c["start"] * 1000), int(c["end"] * 1000))
                for c in cuts
                if 0 <= c["start"] < c["end"] <= duration_ms / 1000
            ])

            merged = []
            for start, end in cuts_ms:
                if merged and start <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], end))
                else:
                    merged.append((start, end))

            segments = [audio[start:end] for start, end in merged]
            final_audio = sum(segments)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as out_tmp:
                cleaned_path = out_tmp.name
                final_audio.export(cleaned_path, format="wav")

            with open(cleaned_path, "rb") as f:
                cleaned_bytes = f.read()

            episode = episode_repo.get_episode(episode_id, user_id=None)[0]
            podcast_id = episode.get("podcast_id")
            user_id = episode.get("userid")
            filename = f"cleaned_{file_id}.wav"

            blob_path = f"users/{user_id}/podcasts/{podcast_id}/episodes/{episode_id}/audio/{filename}"
            base64_audio = base64.b64encode(cleaned_bytes).decode("utf-8")
            blob_url = upload_file_to_blob("podmanagerfiles", blob_path, base64_audio)

            add_audio_edit_to_episode(
                episode_id=episode_id,
                file_id="external",
                edit_type="ai_cut_cleaned",
                filename=filename,
                metadata={"blob_url": blob_url, "segments_kept": len(merged)}
            )

            return blob_url
        finally:
            for path in [tmp_path, cleaned_path]:
                if os.path.exists(path):
                    os.remove(path)