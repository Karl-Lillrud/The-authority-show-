import os, logging, tempfile, requests, subprocess, base64, json
from typing import Optional
from pydub import AudioSegment, silence
from io import BytesIO 
from backend.database.mongo_connection import get_fs
from backend.utils.file_utils import enhance_audio_with_ffmpeg, detect_background_noise, convert_audio_to_wav,get_sentence_timestamps_fuzzy, convert_to_pcm_wav
from backend.utils.ai_utils import (
    remove_filler_words, calculate_clarity_score, analyze_sentiment, analyze_emotions
)
from backend.utils.text_utils import (
    transcribe_with_whisper, detect_filler_words, classify_sentence_relevance,
    analyze_certainty_levels, get_sentence_timestamps, detect_long_pauses,
    generate_ai_show_notes, suggest_sound_effects, translate_text, mix_background,
    pick_dominant_emotion, fetch_sfx_for_emotion
)
from backend.repository.ai_models import save_file, get_file_data, get_file_by_id
from elevenlabs.client import ElevenLabs
from backend.utils.blob_storage import upload_file_to_blob
from backend.repository.episode_repository import EpisodeRepository
from backend.repository.edit_repository import create_edit_entry
from flask import g

logger = logging.getLogger(__name__)

TEXTSTAT_AVAILABLE = False
try:
    import backend.utils.ai_utils as ai_utils_module
    TEXTSTAT_AVAILABLE = True
except ModuleNotFoundError as e:
    if 'textstat.backend' in str(e) or 'textstat' in str(e):
        logger.warning(
            "Failed to load 'backend.utils.ai_utils' or its dependency 'textstat' due to: %s. "
            "Functionality dependent on textstat will be unavailable.", e
        )
        TEXTSTAT_AVAILABLE = False
    else:
        logger.error(f"An unexpected ModuleNotFoundError occurred while importing ai_utils: {e}", exc_info=True)
        raise
except ImportError as e:
    logger.warning(
        "An ImportError occurred while trying to load 'backend.utils.ai_utils', possibly related to textstat: %s. "
        "Textstat-dependent functionality may be unavailable.", e
    )
    TEXTSTAT_AVAILABLE = False

fs = get_fs()
episode_repo = EpisodeRepository()

class AudioService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        if not TEXTSTAT_AVAILABLE:
            self.logger.warning(
                "AudioService initialized, but textstat-dependent features are UNAVAILABLE "
                "due to import errors concerning 'textstat' or 'ai_utils'."
            )
        else:
            self.logger.info(
                "AudioService initialized. Textstat-dependent features are expected to be available via ai_utils."
            )

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
        enhanced_stream = BytesIO(enhanced_data)
        blob_url = upload_file_to_blob("podmanagerfiles", blob_path, enhanced_stream)

        create_edit_entry(
            episode_id=episode_id,
            user_id=g.user_id,
            edit_type="enhanced",
            clip_url=blob_url,
            clipName=f"enhanced_{filename}",
            metadata={
                "source": filename,
                "enhanced": True,
                "edit_type": "enhanced"
            }
        )


        os.remove(temp_in_path)
        os.remove(temp_out_path)

        return blob_url

    def analyze_audio(self, audio_bytes: bytes) -> dict:
        # Write the incoming bytes to a temp WAV file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            temp_path = tmp.name

        try:
            # 1) Basic transcript analysis
            transcript     = transcribe_with_whisper(temp_path)
            cleaned        = ai_utils_module.remove_filler_words(transcript) if TEXTSTAT_AVAILABLE else transcript
            clarity_score  = ai_utils_module.calculate_clarity_score(cleaned) if TEXTSTAT_AVAILABLE else None
            noise_result   = detect_background_noise(temp_path)
            sentiment      = ai_utils_module.analyze_sentiment(transcript) if TEXTSTAT_AVAILABLE else None

            # 2) Emotion detection
            #    a) Translate to English (for more accurate emotion models)
            translated     = translate_text(transcript, "English")
            #    b) Run your emotion classifier
            emotion_data   = ai_utils_module.analyze_emotions(translated) if TEXTSTAT_AVAILABLE else None
            #    c) Pick the most frequent emotion label
            dominant_emotion = pick_dominant_emotion(emotion_data) if TEXTSTAT_AVAILABLE else None

            # 3) Return only the core analysis results + dominant emotion
            return {
                "transcript":         transcript,
                "cleaned_transcript": cleaned,
                "clarity_score":      clarity_score,
                "background_noise":   noise_result,
                "sentiment":          sentiment,
                "emotions":           emotion_data,
                "dominant_emotion":   dominant_emotion
            }

        finally:
            # Always clean up the temp file
            os.remove(temp_path)
    
    def generate_background_and_mix(self, audio_bytes: bytes, emotion: str) -> dict:
        """
        1) Convert any input format into a real WAV (using pydub).
        2) Fetch a 30s SFX loop for 'emotion'.
        3) Overlay it underneath the newly-created WAV.
        4) Return both the loop and the mixed audio as data-URIs.
        """
        # --- STEP 1: Turn incoming bytes into a valid WAV ---
        # pydub will inspect the bytes and decode MP3, WAV, etc.
        audio_seg = AudioSegment.from_file(BytesIO(audio_bytes))
        wav_io    = BytesIO()
        audio_seg.export(wav_io, format="wav")
        wav_bytes = wav_io.getvalue()

        # --- STEP 2: Fetch the 30s background clip ---
        bg_b64 = fetch_sfx_for_emotion(emotion, "general")[0]

        # --- STEP 3: Mix that clip under the real WAV bytes ---
        merged_wav_bytes = mix_background(wav_bytes, bg_b64, bg_gain_db=-35)

        # --- STEP 4: Prefix as data-URI and return ---
        merged_prefixed = "data:audio/wav;base64," + base64.b64encode(merged_wav_bytes).decode()
        return {
            "background_clip": bg_b64,
            "merged_audio":   merged_prefixed
        }

    def cut_audio(self, file_id: str, start_time: float, end_time: float, episode_id: str) -> str:
        logger.info(f"Request to clip audio file with ID: {file_id}")
        logger.info(f"Timestamps to clip: start={start_time}, end={end_time}")

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
            clipped_stream = BytesIO(clipped_data)
            blob_url = upload_file_to_blob("podmanagerfiles", blob_path, clipped_stream)


            create_edit_entry(
                episode_id=episode_id,
                user_id=g.user_id,
                edit_type="manual_clip",
                clip_url=blob_url,
                clipName=filename,
                metadata={
                    "start": start_time,
                    "end": end_time,
                    "edit_type": "manual_clip"
                }
            )

            return blob_url
        finally:
            for path in [input_path, output_path]:
                if os.path.exists(path):
                    os.remove(path)

    def ai_cut_audio(self, file_bytes: bytes, filename: str, episode_id: Optional[str] = None) -> dict:
        logger.info(f"Starting AI cut for file: {filename}")
        
        # Convert audio to PCM WAV format using FFmpeg
        try:
            converted_bytes = convert_to_pcm_wav(file_bytes)
        except Exception as e:
            logger.error(f"Audio conversion failed: {str(e)}")
            raise RuntimeError("Audio format is unsupported or corrupted")

        # Write to temporary WAV file for downstream processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(converted_bytes)
            tmp.flush()
            temp_path = tmp.name

        logger.info(f"AI Cut working with converted WAV file at: {temp_path}")

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

            cleaned_transcript = ai_utils_module.remove_filler_words(transcript) if TEXTSTAT_AVAILABLE else transcript
            noise_result = detect_background_noise(temp_path)
            filler_sentences = ai_utils_module.detect_filler_words(transcript) if TEXTSTAT_AVAILABLE else []
            sentence_certainty = ai_utils_module.analyze_certainty_levels(transcript) if TEXTSTAT_AVAILABLE else []

            logger.info(f"Certainty results computed")

            sentence_timestamps = []
            audio = AudioSegment.from_wav(temp_path)
            cut_file_ids = []

            for idx, entry in enumerate(sentence_certainty):
                if entry["certainty"] <= 0:
                    continue

                timestamps = get_sentence_timestamps_fuzzy(entry["sentence"], word_timings)
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
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_cut:
                    cut.export(tmp_cut.name, format="wav")
                    tmp_cut.flush()

                    with open(tmp_cut.name, "rb") as f:
                        file_id = save_file(
                            f.read(),
                            filename=f"cut_{idx}.wav",
                            metadata={"type": "ai_cut", "source": filename}
                        )
                        cut_file_ids.append(file_id)

                    os.remove(tmp_cut.name)

            sentiment = ai_utils_module.analyze_sentiment(transcript) if TEXTSTAT_AVAILABLE else None
            show_notes = generate_ai_show_notes(transcript)

            return {
                "message": "AI Audio processing completed with clips",
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
            logger.info(f"Temp file cleaned up: {temp_path}")

    def ai_cut_audio_from_id(self, file_id: str, episode_id: Optional[str] = None) -> dict:
        audio_bytes, filename = get_file_by_id(file_id)
        return self.ai_cut_audio(audio_bytes, filename, episode_id=episode_id)
    
    def isolate_voice(self, audio_bytes: bytes, filename: str, episode_id: str) -> str:
        logger.info(f"Starting voice isolation for file: {filename}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            temp_input_path = tmp.name

        temp_output_path = None  # ✅ Ensure this is always defined

        try:
            elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
            if not elevenlabs_api_key:
                raise RuntimeError("Missing ELEVENLABS_API_KEY environment variable")

            logger.info("Sending audio to ElevenLabs voice isolation endpoint...")

            with open(temp_input_path, "rb") as f:
                response = requests.post(
                    "https://api.elevenlabs.io/v1/audio-isolation",
                    headers={"xi-api-key": elevenlabs_api_key},
                    files={"audio": f}
                )

            logger.info(f"ElevenLabs response status: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"Voice isolation failed: {response.status_code} {response.text}")
                raise RuntimeError(f"Voice isolation failed: {response.status_code} {response.text}")

            # Save the isolated audio to a temporary file
            temp_output_path = temp_input_path.replace(".wav", "_isolated.wav")
            with open(temp_output_path, "wb") as out_file:
                out_file.write(response.content)

            with open(temp_output_path, "rb") as f:
                isolated_data = f.read()

            isolated_filename = f"isolated_{filename}"
            podcast_id = episode_repo.get_podcast_id_by_episode(episode_id)

            blob_path = f"users/{g.user_id}/podcasts/{podcast_id}/episodes/{episode_id}/audio/{isolated_filename}"
            isolated_stream = BytesIO(isolated_data)
            blob_url = upload_file_to_blob("podmanagerfiles", blob_path, isolated_stream)

            create_edit_entry(
                episode_id=episode_id,
                user_id=g.user_id,
                edit_type="voice_isolated",
                clip_url=blob_url,
                clipName=isolated_filename,
                metadata={
                    "source": filename,
                    "edit_type": "voice_isolated"
                }
            )

            logger.info(f"Isolated voice uploaded to Azure: {blob_url}")
            return blob_url

        finally:
            os.remove(temp_input_path)
            if temp_output_path and os.path.exists(temp_output_path):
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
        logger.info(f"Applying cuts to file ID: {file_id}")
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
            cleaned_stream = BytesIO(cleaned_bytes)
            blob_url = upload_file_to_blob("podmanagerfiles", blob_path, cleaned_stream)

            create_edit_entry(
                episode_id=episode_id,
                user_id=g.user_id,
                edit_type="ai_cut_cleaned",
                clip_url=blob_url,
                clipName=filename,
                metadata={
                    "segments_kept": len(merged),
                    "edit_type": "ai_cut_cleaned"
                }
            )


            return blob_url
        finally:
            for path in [tmp_path, cleaned_path]:
                if os.path.exists(path):
                    os.remove(path)

    def apply_cuts_and_return_bytes(self, file_id: str, cuts: list[dict]) -> tuple[bytes, str]:
        audio_data = get_file_data(file_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            audio = AudioSegment.from_wav(tmp_path)
            cuts_ms = sorted([
                (int(c["start"] * 1000), int(c["end"] * 1000))
                for c in cuts if 0 <= c["start"] < c["end"]
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

            filename = f"cleaned_{file_id}.wav"
            return cleaned_bytes, filename
        finally:
            for path in [tmp_path, cleaned_path]:
                if os.path.exists(path):
                    os.remove(path)

    def cut_audio_to_bytes(self, file_id: str, start_time: float, end_time: float) -> tuple[bytes, str]:
        logger.info(f"Cutting audio ID: {file_id} from {start_time}s to {end_time}s")

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

            filename = os.path.basename(output_path)
            return clipped_data, filename
        finally:
            for path in [input_path, output_path]:
                if os.path.exists(path):
                    os.remove(path)

    def cut_audio_from_blob(self, audio_bytes: bytes, filename: str, episode_id: str, start_time: float, end_time: float) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_in:
            tmp_in.write(audio_bytes)
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

            podcast_id = episode_repo.get_podcast_id_by_episode(episode_id)
            blob_path = f"users/{g.user_id}/podcasts/{podcast_id}/episodes/{episode_id}/audio/clipped_{filename}"
            clipped_stream = BytesIO(clipped_data)
            blob_url = upload_file_to_blob("podmanagerfiles", blob_path, clipped_stream)

            create_edit_entry(
                episode_id=episode_id,
                user_id=g.user_id,
                edit_type="manual_clip",
                clip_url=blob_url,
                clipName=f"clipped_{filename}",
                metadata={
                    "start": start_time,
                    "end": end_time,
                    "edit_type": "manual_clip"
                }
            )


            return blob_url
        finally:
            for path in [input_path, output_path]:
                if os.path.exists(path):
                    os.remove(path)

    def apply_cuts_on_blob(self, audio_bytes: bytes, filename: str, cuts: list[dict], episode_id: str) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            audio = AudioSegment.from_wav(tmp_path)
            cuts_ms = sorted([
                (int(c["start"] * 1000), int(c["end"] * 1000))
                for c in cuts if 0 <= c["start"] < c["end"]
            ])

            segments = [audio[start:end] for start, end in cuts_ms]
            final_audio = sum(segments)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as out_tmp:
                cleaned_path = out_tmp.name
                final_audio.export(cleaned_path, format="wav")

            with open(cleaned_path, "rb") as f:
                cleaned_bytes = f.read()

            podcast_id = episode_repo.get_podcast_id_by_episode(episode_id)
            blob_path = f"users/{g.user_id}/podcasts/{podcast_id}/episodes/{episode_id}/audio/cleaned_{filename}"
            cleaned_stream = BytesIO(cleaned_bytes)
            blob_url = upload_file_to_blob("podmanagerfiles", blob_path, cleaned_stream)

            create_edit_entry(
                episode_id=episode_id,
                user_id=g.user_id,
                edit_type="ai_cut_cleaned",
                clip_url=blob_url,
                clipName=f"cleaned_{filename}",
                metadata={
                    "edit_type": "ai_cut_cleaned"
                }
            )


            return blob_url
        finally:
            for path in [tmp_path, cleaned_path]:
                if os.path.exists(path):
                    os.remove(path)
        
    def plan_and_mix_sfx(self, audio_bytes: bytes) -> dict:
        """
        New GPT-based SFX planning and mixing flow:
        1. Transcribe audio with timestamps
        2. Generate SFX plan using GPT
        3. Create SFX clips based on plan
        4. Mix SFX with original audio
        """
        logger.info("Starting plan_and_mix_sfx process")
        
        # Step 1: Transcribe audio with timestamps
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            temp_path = tmp.name
            logger.info(f"Saved input audio to temporary file: {temp_path}")
        
        try:
            # Get transcript with timestamps
            logger.info("Transcribing audio with ElevenLabs API")
            client = ElevenLabs()
            with open(temp_path, "rb") as f:
                audio_bytes_for_api = f.read()
                logger.info(f"Read {len(audio_bytes_for_api)} bytes from temp file")
        
            result = client.speech_to_text.convert(
                file=audio_bytes_for_api,
                model_id="scribe_v1",
                timestamps_granularity="word"
            )
            
            logger.info(f"Transcription complete. Got {len(result.words) if hasattr(result, 'words') else 0} words with timestamps")
        
            # Group words into sentences and calculate sentence timestamps
            transcript_segments = []
            current_sentence = []
            sentence_start = None
            sentence_end = None

            for word in result.words:
                if hasattr(word, "start") and hasattr(word, "end"):
                    if sentence_start is None:
                        sentence_start = word.start
                    sentence_end = word.end
                    current_sentence.append(word.text)
                
                    # Simple sentence boundary detection (period followed by space or end)
                    if word.text.endswith('.') or word.text.endswith('?') or word.text.endswith('!'):
                        if current_sentence:
                            transcript_segments.append({
                                "start": sentence_start,
                                "end": sentence_end,
                                "text": " ".join(current_sentence)
                            })
                            current_sentence = []
                            sentence_start = None
                            sentence_end = None

            # Add any remaining words as a segment
            if current_sentence:
                transcript_segments.append({
                    "start": sentence_start,
                    "end": sentence_end,
                    "text": " ".join(current_sentence)
                })
            
            logger.info(f"Created {len(transcript_segments)} sentence segments from transcript")
            for i, segment in enumerate(transcript_segments[:3]):  # Log first 3 segments
                logger.info(f"Segment {i}: [{segment['start']:.2f}s - {segment['end']:.2f}s] {segment['text'][:50]}...")
            
            # Step 2: Generate SFX plan using GPT
            logger.info("Generating SFX plan using GPT")
            sfx_plan = self.generate_sfx_plan_from_analysis(transcript_segments)
            logger.info(f"Generated SFX plan with {len(sfx_plan)} sound effects")
            
            for i, effect in enumerate(sfx_plan):
                logger.info(f"SFX {i}: {effect['description']} [{effect['start']:.2f}s - {effect['end']:.2f}s]")
            
            if not sfx_plan:
                logger.warning("No sound effects were planned by GPT! Returning original audio.")
        
            # Step 3: Create SFX clips based on plan
            logger.info("Generating SFX clips based on plan")
            sfx_clips = self.generate_sfx_clips_from_plan(sfx_plan)
            logger.info(f"Generated {len(sfx_clips)} SFX clips")
            for i, clip in enumerate(sfx_clips):
                logger.info(f"Clip {i}: {clip['description']} [{clip['start']:.2f}s - {clip['end']:.2f}s] Has audio: {bool(clip.get('audio_bytes'))}")
                if not clip.get('audio_bytes'):
                    logger.warning(f"Clip has no audio bytes - ElevenLabs may have failed to generate audio")
            
            if not sfx_clips:
                logger.warning("No SFX clips were generated! Returning original audio.")
        
            # Step 4: Mix SFX with original audio
            logger.info("Mixing SFX with original audio")
            mixed_audio_bytes = self.mix_sfx_audio_bytes(audio_bytes, sfx_clips)
            logger.info(f"Mixed audio generated: {len(mixed_audio_bytes)} bytes")
        
            # Convert to base64 for frontend
            mixed_audio_b64 = "data:audio/wav;base64," + base64.b64encode(mixed_audio_bytes).decode()
        
            # Prepare the sfx_clips for the response (remove audio_bytes which is not needed in the response)
            sfx_clips_response = []
            for clip in sfx_clips:
                sfx_clips_response.append({
                    "description": clip["description"],
                    "start": clip["start"],
                    "end": clip["end"],
                    "sfxUrl": clip["sfxUrl"]
                })
            
            if mixed_audio_bytes == audio_bytes:
                logger.error("ERROR: Mixed audio is identical to original! No SFX were mixed in.")
            else:
                logger.info("SUCCESS: Mixed audio is different from original.")
            
            logger.info("SFX mixing process complete, returning results")
            return {
                "sfx_plan": sfx_plan,
                "sfx_clips": sfx_clips_response,
                "merged_audio": mixed_audio_b64
            }

        except Exception as e:
            logger.error(f"Error in plan_and_mix_sfx: {e}", exc_info=True)
            raise
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                logger.info(f"Cleaned up temporary file: {temp_path}")

    def generate_sfx_plan_from_analysis(self, transcript_segments: list) -> list:
        """
        Use GPT to generate a creative SFX plan based on transcript segments.
        Fallbacks to gpt-3.5-turbo if gpt-4 fails (rate limit, context length, etc).
        """
        import json, os
        from openai import OpenAI

        logger.info(f"Generating SFX plan from {len(transcript_segments)} transcript segments")
        segments_text = "\n".join([
            f"[{s['start']:.2f}s - {s['end']:.2f}s]: {s['text']}"
            for s in transcript_segments
        ])

        prompt = f"""
    You are a professional podcast sound designer.

    Your task is to plan highly creative and immersive sound effects (SFX) that align with the emotions, actions, or environments described in the transcript below. Use the timestamps to precisely place the sounds.

    For each sound effect, return:
    - A brief but vivid description of the sound
    - The start time in seconds
    - The end time in seconds

    Be cinematic and imaginative, but ensure the effects:
    - Enhance storytelling or emotional tone
    - Reflect the literal or implied context
    - Are suitable for a podcast (not too loud or distracting)

    EXAMPLES:
    If someone says "It was thundering outside", suggest "Distant thunder rumbling".
    If a person whispers nervously, suggest "Tense ambient drone".
    If someone opens a door, suggest "Old wooden door creaking open".

    TRANSCRIPT SEGMENTS:
    {segments_text}

    FORMAT:
    [
    {{
        "description": "sound description",
        "start": start_time,
        "end": end_time
    }},
    ...
    ]

    You can include up to 5 SFX. Skip segments if no effect is needed. Only return the JSON array — no explanation.
    """

        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        def call_gpt(model_name):
            logger.info(f"🔁 Calling model: {model_name}")
            response = openai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a professional sound designer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8
            )
            return response.choices[0].message.content.strip()

        for model in ["gpt-4", "gpt-3.5-turbo"]:
            try:
                content = call_gpt(model)
                logger.info(f"✅ Response from {model}: {content[:200]}...")
                result = json.loads(content)
                if isinstance(result, list):
                    return [
                        {
                            "description": entry["description"],
                            "start": float(entry["start"]),
                            "end": float(entry["end"])
                        }
                        for entry in result
                        if isinstance(entry, dict) and "description" in entry and "start" in entry and "end" in entry
                    ]
                elif isinstance(result, dict) and "sfx_plan" in result:
                    return result["sfx_plan"]
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ GPT ({model}) response is not valid JSON: {e}")
                logger.debug(f"Raw: {content}")
            except Exception as e:
                logger.warning(f"⚠️ GPT call with {model} failed: {e}")
                continue

        logger.error("❌ All GPT model calls failed")
        return []


    def generate_sfx_clips_from_plan(self, sfx_plan: list) -> list:
        """
        Generate actual SFX clips based on the plan.
        Returns a list of: {description, start, end, sfxUrl, audio_bytes}
        """
        logger.info(f"Generating SFX clips from plan with {len(sfx_plan)} entries")
        result = []
        
        for i, entry in enumerate(sfx_plan):
            description = entry["description"]
            logger.info(f"Generating SFX clip {i+1}/{len(sfx_plan)}: '{description}'")
            
            # Generate SFX using ElevenLabs sound generation
            url = "https://api.elevenlabs.io/v1/sound-generation"
            headers = {
                "xi-api-key": os.getenv("ELEVENLABS_API_KEY"),
                "Content-Type": "application/json"
            }
            
            # Calculate duration
            duration = entry["end"] - entry["start"]
            duration = max(2, min(duration, 10))  # Limit between 2-10 seconds
            logger.info(f"Calculated duration: {duration}s")
            
            payload = {
                "text": f"Create a {duration}-second sound effect for: {description}. The sound should be perfect for a podcast.",
                "duration_seconds": duration,
                "prompt_influence": 1
            }
            
            try:
                logger.info(f"Sending request to ElevenLabs sound generation API")
                res = requests.post(url, headers=headers, json=payload)
                logger.info(f"Response status: {res.status_code}")
                logger.info(f"Response content type: {res.headers.get('Content-Type', 'unknown')}")
            
                if "audio/mpeg" not in res.headers.get("Content-Type", ""):
                    logger.warning(f"Failed to generate SFX for: {description}")
                    logger.warning(f"Response: {res.text[:200]}...")  # Log first 200 chars
                    continue
            
                logger.info(f"Successfully generated SFX audio, size: {len(res.content)} bytes")
            
                # Convert MP3 to WAV for consistent processing
                audio_seg = AudioSegment.from_file(BytesIO(res.content), format="mp3")
                wav_io = BytesIO()
                audio_seg.export(wav_io, format="wav")
                audio_bytes = wav_io.getvalue()
                logger.info(f"Converted to WAV, size: {len(audio_bytes)} bytes")
        
                # Create base64 URL for frontend
                b64 = base64.b64encode(res.content).decode("utf-8")
                sfx_url = f"data:audio/mpeg;base64,{b64}"
        
                result.append({
                    **entry,
                    "sfxUrl": sfx_url,
                    "audio_bytes": audio_bytes
                })
                logger.info(f"Added SFX clip to result list")
        
            except Exception as e:
                logger.error(f"Error generating SFX clip for '{description}': {e}", exc_info=True)

        logger.info(f"Generated {len(result)} SFX clips successfully")
        return result

    def mix_sfx_audio_bytes(self, original_audio_bytes: bytes, sfx_clips: list) -> bytes:
        """
        Mix SFX clips with original audio.
        Returns the mixed audio as bytes.
        """
        logger.info(f"Mixing {len(sfx_clips)} SFX clips with original audio ({len(original_audio_bytes)} bytes)")
        
        # Load original audio
        try:
            original = AudioSegment.from_file(BytesIO(original_audio_bytes), format="wav")
            logger.info(f"Original audio length (ms): {len(original)}")
            logger.info(f"Loaded original audio: {len(original)}ms duration, {original.channels} channels, {original.frame_rate}Hz")
        
            # Create a copy to mix into
            mixed = original.overlay(AudioSegment.silent(duration=0))
            logger.info("Created base mixed audio track")
        
            # Mix in each SFX clip at the specified position
            for i, clip in enumerate(sfx_clips):
                try:
                    start_ms = int(clip["start"] * 1000)
                    if start_ms >= len(original):
                        logger.warning(f"SFX start time ({start_ms}ms) is after the end of the audio ({len(original)}ms)!")
                        continue
                    logger.info(f"Processing clip {i+1}/{len(sfx_clips)}: '{clip['description']}' at {start_ms}ms")
                    
                    if not clip.get("audio_bytes"):
                        logger.warning(f"Clip {i+1} has no audio_bytes, skipping")
                        continue
                    
                    sfx = AudioSegment.from_file(BytesIO(clip["audio_bytes"]), format="wav")
                    logger.info(f"Loaded SFX audio: {len(sfx)}ms duration")
                
                    # Apply a slight fade in/out
                    sfx = sfx.fade_in(300).fade_out(300)
                    logger.info("Applied fade in/out")
                
                    # Adjust volume (make SFX quieter than speech)
                    sfx = sfx - 3  # Reduce by only 3 dB for testing (was -10)
                    logger.info(f"Adjusted volume (-3dB instead of -10dB for testing)")
                
                    # Overlay at the correct position
                    mixed = mixed.overlay(sfx, position=start_ms)
                    logger.info(f"Overlaid SFX at position {start_ms}ms")
                
                except Exception as e:
                    logger.error(f"Error mixing SFX '{clip['description']}': {e}", exc_info=True)
        
            # Export the final mix
            logger.info("Exporting final mixed audio")
            output = BytesIO()
            mixed.export(output, format="wav")
            result_bytes = output.getvalue()
            logger.info(f"Exported mixed audio: {len(result_bytes)} bytes")
            
            # Check if the mixed audio is different from the original
            if len(result_bytes) == len(original_audio_bytes):
                logger.warning("WARNING: Mixed audio has same size as original, they might be identical")
                if result_bytes == original_audio_bytes:
                    logger.error("ERROR: Mixed audio is identical to original! No SFX were mixed in.")
            
            return result_bytes
            
        except Exception as e:
            logger.error(f"Error in mix_sfx_audio_bytes: {e}", exc_info=True)
            # Return original audio as fallback
            logger.warning("Returning original audio due to mixing error")
            return original_audio_bytes