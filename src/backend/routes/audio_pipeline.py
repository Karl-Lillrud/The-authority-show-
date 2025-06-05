# audio_pipeline.py
import logging
import tempfile
import os
import json
import base64
from typing import List, Dict, Any, Optional, Tuple
from flask import Blueprint, request, jsonify, g
from io import BytesIO

from backend.services.transcriptionService import TranscriptionService
from backend.services.audioService import AudioService
from backend.services.creditService import consume_credits
from backend.utils.blob_storage import upload_file_to_blob
from backend.repository.episode_repository import EpisodeRepository
from backend.repository.edit_repository import create_edit_entry, add_voice_map_to_edit
from backend.utils.ai_utils import check_audio_duration, insufficient_credits_response,enhance_audio_with_ffmpeg,get_osint_info, create_podcast_scripts_paid,text_to_speech_with_elevenlabs

logger = logging.getLogger(__name__)
audio_pipeline_bp = Blueprint("audio_pipeline_bp", __name__)
audio_service = AudioService()
episode_repo = EpisodeRepository()
transcription_service = TranscriptionService()

def safe_consume_credits_after_success(user_id: str, credit_type: Optional[str], step_fn):
    try:
        result = step_fn()
        if credit_type:
            consume_credits(user_id, credit_type)
        return result
    except Exception as e:
        logger.error(f"Error in GPT step: {str(e)}", exc_info=True)
        raise

@audio_pipeline_bp.route("/audio/process_pipeline", methods=["POST"])
def process_audio_pipeline():
    word_timestamps = None
    steps_raw = request.form.get("steps")
    episode_id = request.form.get("episode_id")
    audio_file = request.files.get("audio")
    cuts_raw = request.form.get("cuts")
    target_language = request.form.get("target_language", "English")  # NYTT: För translate_transcript
    voice_id = request.form.get("voice_id")
    edit_id = request.form.get("edit_id")
    voice_map_raw = request.form.get("voice_map")
    translated_transcript = request.form.get("translated_transcript")
    try:
        voice_map = json.loads(voice_map_raw) if voice_map_raw else None
    except Exception as e:
        logger.warning(f"⚠️ Failed to parse voice_map JSON: {e}")
        voice_map = None

    if not steps_raw or not episode_id or not audio_file:
        return jsonify({"error": "Missing required fields: steps, episode_id, or audio"}), 400

    try:
        steps = json.loads(steps_raw)
    except Exception as e:
        return jsonify({"error": f"Invalid steps format: {str(e)}"}), 400

    try:
        cuts = json.loads(cuts_raw) if cuts_raw else []
    except Exception as e:
        return jsonify({"error": f"Invalid cuts format: {str(e)}"}), 400

    if not steps:
        return jsonify({"error": "No processing steps provided"}), 400

    # Read audio bytes
    try:
        audio_bytes = audio_file.read()
    except Exception as e:
        logger.error(f"Error reading uploaded audio file: {str(e)}")
        return jsonify({"error": "Could not read uploaded audio file"}), 400

    # Validate steps
    valid_steps = [
        "transcribe", "enhance", "ai_cut", "voice_isolation", "cut_audio",
        "analyze_audio", "plan_and_mix_sfx",
        "clean_transcript", "generate_show_notes", "ai_suggestions", "generate_quotes",
        "generate_quote_images", "osint_lookup", "generate_intro_outro", "intro_outro_to_speech", "generate_audio_clip",
        "voice_cloning", "translate_transcript"  # NYA STEG
    ]
    for step in steps:
        if step not in valid_steps:
            return jsonify({"error": f"Invalid step: {step}. Valid steps are: {valid_steps}"}), 400

    # Validate cuts if required
    if "cut_audio" in steps:
        if not cuts:
            return jsonify({"error": "cuts parameter is required when cut_audio step is included"}), 400

        for i, cut in enumerate(cuts):
            if "start" not in cut or "end" not in cut:
                return jsonify({"error": f"Cut at index {i} is missing start or end time"}), 400
            if cut["start"] >= cut["end"]:
                return jsonify({"error": f"Cut at index {i} has invalid time range (start must be less than end)"}), 400

    # --- Credit handling ---
    user_id = g.user_id
    credit_types = {
        "transcribe": "transcription",
        "enhance": "audio_enhancement",
        "ai_cut": "ai_audio_cutting",
        "voice_isolation": "voice_isolation",
        "cut_audio": "audio_cutting",
        "analyze_audio": "ai_audio_analysis",
        "plan_and_mix_sfx": "audio_clip",
        "clean_transcript": "clean_transcript",
        "generate_show_notes": "show_notes",
        "ai_suggestions": "ai_suggestions",
        "generate_quotes": "ai_quotes",
        "generate_quote_images": "ai_quote_images",
        "osint_lookup": "ai_osint",
        "generate_intro_outro": "ai_intro",
        "intro_outro_to_speech": "ai_intro",
        "generate_audio_clip": "audio_clip",
        "voice_cloning": "voice_cloning",  # NY KREDITTYP
        "translate_transcript": "translation"  # NY KREDITTYP
    }

    for step in steps:
        credit_type = credit_types.get(step)
        if credit_type:
            try:
                # Just check (simulate) credit availability here (no deduction yet)
                pass
            except ValueError as e:
                return insufficient_credits_response(credit_type, e)

    current_audio = audio_bytes
    filename = f"pipeline_audio.wav"
    metadata = {"steps_applied": [], "transcript": "", "cuts": []}

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            temp_path = os.path.join(temp_dir, "input.wav")
            with open(temp_path, "wb") as f:
                f.write(current_audio)

            ordered_step_priority = [
                "transcribe",
                "translate_transcript",  # First translate to get timestamps
                "voice_cloning",         # Then clone voice
                "generate_audio_clip",   # Finally generate audio
                "voice_isolation",
                "enhance",
                "analyze_audio",
                "ai_cut",
                "clean_transcript", 
                "generate_show_notes", 
                "ai_suggestions", 
                "generate_quotes",
                "generate_quote_images", 
                "osint_lookup", 
                "generate_intro_outro", 
                "intro_outro_to_speech",
                "cut_audio", 
                "plan_and_mix_sfx"
            ]

            steps = sorted(set(steps), key=lambda x: ordered_step_priority.index(x) if x in ordered_step_priority else 999)

            for step in steps:
                logger.info(f"Processing step: {step}")
                credit_type = credit_types.get(step)

                try:
                    if step in ["clean_transcript", "generate_show_notes", "ai_suggestions", "generate_quotes", "translate_transcript"] and not metadata.get("transcript"):
                        raise ValueError(f"Step '{step}' requires transcript. Ensure 'transcribe', 'analyze_audio' or 'ai_cut' is included.")

                    if step == "enhance":
                        current_audio, temp_path = process_enhance_step(current_audio, temp_path, temp_dir)
                        metadata["steps_applied"].append(step)
                        if credit_type: consume_credits(user_id, credit_type)

                    elif step == "ai_cut":
                        current_audio, temp_path, result = process_ai_cut_step(current_audio, temp_path, temp_dir, filename)
                        metadata["steps_applied"].append(step)
                        metadata["transcript"] = result.get("cleaned_transcript", "")
                        metadata["cuts"] = result.get("suggested_cuts", [])
                        if credit_type: consume_credits(user_id, credit_type)

                    elif step == "voice_isolation":
                        current_audio, temp_path = process_voice_isolation_step(current_audio, temp_path, temp_dir)
                        metadata["steps_applied"].append(step)
                        if credit_type: consume_credits(user_id, credit_type)

                    elif step == "transcribe":
                        result = transcription_service.transcribe_audio(current_audio, filename, user_id, episode_id)
                        metadata["steps_applied"].append(step)
                        metadata["transcript"] = result.get("full_transcript", "")
                        metadata["raw_transcription"] = result.get("raw_transcription", "")
                        metadata["word_timestamps"] = result.get("word_timestamps", []) 
                        if credit_type: consume_credits(user_id, credit_type)

                    elif step == "cut_audio":
                        current_audio, temp_path = process_cut_audio_step(current_audio, temp_path, temp_dir, cuts)
                        metadata["steps_applied"].append(step)
                        if credit_type: consume_credits(user_id, credit_type)

                    elif step == "analyze_audio":
                        result = process_analyze_audio_step(current_audio)
                        metadata["steps_applied"].append(step)
                        metadata["transcript"] = result.get("transcript", "")
                        metadata["analysis"] = result
                        word_timestamps = result.get("word_timestamps", None)
                        if credit_type: consume_credits(user_id, credit_type)

                    elif step == "plan_and_mix_sfx":
                        current_audio, temp_path, result = process_plan_and_mix_sfx_step(current_audio, temp_path, temp_dir, word_timestamps)
                        metadata["steps_applied"].append(step)
                        metadata["sfx_plan"] = result.get("sfx_plan", [])
                        metadata["sfx_clips"] = result.get("sfx_clips", [])
                        if credit_type: consume_credits(user_id, credit_type)

                    elif step == "clean_transcript":
                        cleaned = safe_consume_credits_after_success(user_id, credit_type, lambda: transcription_service.get_clean_transcript(metadata["transcript"]))
                        metadata["steps_applied"].append(step)
                        metadata["clean_transcript"] = cleaned

                    elif step == "generate_show_notes":
                        notes = safe_consume_credits_after_success(user_id, credit_type, lambda: transcription_service.get_show_notes(metadata["transcript"]))
                        metadata["steps_applied"].append(step)
                        metadata["show_notes"] = notes

                    elif step == "ai_suggestions":
                        suggestions = safe_consume_credits_after_success(user_id, credit_type, lambda: transcription_service.get_ai_suggestions(metadata["transcript"]))
                        metadata["steps_applied"].append(step)
                        metadata["ai_suggestions"] = suggestions

                    elif step == "generate_quotes":
                        quotes = safe_consume_credits_after_success(user_id, credit_type, lambda: transcription_service.get_quotes(metadata["transcript"]))
                        metadata["steps_applied"].append(step)
                        metadata["quotes"] = quotes

                    elif step == "generate_quote_images":
                        quotes = metadata.get("quotes", "")
                        if not quotes:
                            raise ValueError("No quotes found to generate images from")
                        quotes_list = [q.strip() for q in quotes.split("\n\n") if q.strip()]
                        images = safe_consume_credits_after_success(user_id, credit_type, lambda: transcription_service.get_quote_images(quotes_list, method="local"))
                        metadata["steps_applied"].append(step)
                        metadata["quote_images"] = images

                    elif step == "osint_lookup":
                        guest_name = request.form.get("osint_query", "").strip()
                        if not guest_name:
                            raise ValueError("Missing guest name for OSINT")
                        osint_result = safe_consume_credits_after_success(user_id, credit_type, lambda: get_osint_info(guest_name))
                        metadata["steps_applied"].append(step)
                        metadata["osint"] = osint_result

                    elif step == "generate_intro_outro":
                        guest_name = request.form.get("osint_query", "").strip()
                        raw_transcript = metadata.get("raw_transcription", "")
                        if not guest_name or not raw_transcript:
                            raise ValueError("Missing guest name or raw transcript")
                        def generate_script():
                            osint_data = get_osint_info(guest_name)
                            return create_podcast_scripts_paid(osint_data, guest_name, raw_transcript)
                        intro_outro_script = safe_consume_credits_after_success(user_id, credit_type, generate_script)
                        metadata["steps_applied"].append(step)
                        metadata["intro_outro_script"] = intro_outro_script

                    elif step == "intro_outro_to_speech":
                        script = metadata.get("intro_outro_script", "")
                        if not script:
                            raise ValueError("Intro/outro script is missing")
                        def convert_to_audio():
                            audio_bytes = text_to_speech_with_elevenlabs(script)
                            return base64.b64encode(audio_bytes).decode("utf-8")
                        b64 = safe_consume_credits_after_success(user_id, credit_type, convert_to_audio)
                        metadata["steps_applied"].append(step)
                        metadata["intro_outro_audio_url"] = f"data:audio/mp3;base64,{b64}"

                    elif step == "generate_audio_clip":
                        transcript = (
                            translated_transcript
                            or metadata.get("translated_transcript")
                            or metadata.get("transcript", "")
                        )
                        if not transcript:
                            raise ValueError("Transcript missing for TTS.")

                        # Get the cloned voice ID from metadata
                        voice_id = metadata.get("voice_id")
                        if not voice_id:
                            raise ValueError("No cloned voice ID found. Please run voice cloning first.")

                        def create_clip():
                            return transcription_service.generate_audio_from_translated(
                                transcript,
                                target_language,
                                voice_id=voice_id
                            )

                        b64 = safe_consume_credits_after_success(user_id, credit_type, create_clip)
                        metadata["steps_applied"].append(step)
                        translated_clip_path = os.path.join(temp_dir, f"translated_clip_{filename}.mp3")
                        with open(translated_clip_path, "wb") as f:
                            f.write(b64)
                        podcast_id = episode_repo.get_podcast_id_by_episode(episode_id)
                        blob_path = f"users/{user_id}/podcasts/{podcast_id}/episodes/{episode_id}/audio/translated_clip_{filename}.mp3"
                        with open(translated_clip_path, "rb") as f:
                            clip_stream = BytesIO(f.read())
                        translated_clip_url = upload_file_to_blob("podmanagerfiles", blob_path, clip_stream)
                        metadata["translated_clip_url"] = translated_clip_url

                    # NYTT: translate_transcript
                    elif step == "translate_transcript":
                        if not metadata.get("raw_transcription"):
                            raise ValueError("Raw transcription with timestamps is required for translation. Ensure 'transcribe' or 'analyze_audio' is included.")
                        def translate():
                            return transcription_service.translate_transcript(metadata["raw_transcription"], target_language)
                        translated_transcript = safe_consume_credits_after_success(user_id, credit_type, translate)
                        metadata["steps_applied"].append(step)
                        metadata["translated_transcript"] = translated_transcript

                    elif step == "voice_cloning":
                        if not audio_file:
                            raise ValueError("Audio file is required for voice cloning.")
                        def clone_voice():
                            # Clone one voice from the audio file
                            voice_id = transcription_service.clone_user_voice(audio_bytes, user_id)
                            return voice_id
                        voice_id = safe_consume_credits_after_success(user_id, credit_type, clone_voice)
                        metadata["steps_applied"].append(step)
                        metadata["voice_id"] = voice_id  # Store voice_id in metadata
                        logger.info(f"Voice cloned successfully with ID: {voice_id}")

                except Exception as e:
                    logger.error(f"Error in step '{step}': {str(e)}", exc_info=True)
                    return jsonify({"error": f"Step '{step}' failed: {str(e)}", "steps_applied": metadata["steps_applied"]}), 500

            # Final audio upload
            podcast_id = episode_repo.get_podcast_id_by_episode(episode_id)
            output_filename = f"pipeline_{'-'.join(metadata['steps_applied'])}_{filename}"
            blob_path = f"users/{user_id}/podcasts/{podcast_id}/episodes/{episode_id}/audio/{output_filename}"

            with open(temp_path, "rb") as f:
                final_audio_bytes = f.read()

            final_audio_stream = BytesIO(final_audio_bytes)
            blob_url = upload_file_to_blob("podmanagerfiles", blob_path, final_audio_stream)

            create_edit_entry(
                episode_id=episode_id,
                user_id=user_id,
                edit_type="pipeline",
                clip_url=blob_url,
                clipName=output_filename,
                metadata={
                    "steps_applied": metadata["steps_applied"],
                    "edit_type": "pipeline",
                    "voice_map": metadata.get("voice_map"),
                    "translated_transcript": metadata.get("translated_transcript"),
                }
            )

            return jsonify({
                "final_audio_url": blob_url,
                "steps_applied": metadata["steps_applied"],
                "transcript": metadata.get("transcript"),
                "translated_transcript": metadata.get("translated_transcript"),  # NYTT
                "voice_map": metadata.get("voice_map"),  # NYTT
                "cuts": metadata.get("cuts", []),
                "ai_suggestions": metadata.get("ai_suggestions"),
                "quotes": metadata.get("quotes"),
                "show_notes": metadata.get("show_notes"),
                "clean_transcript": metadata.get("clean_transcript"),
                "sfx_plan": metadata.get("sfx_plan"),
                "sfx_clips": metadata.get("sfx_clips"),
                "quote_images": metadata.get("quote_images"),
                "osint": metadata.get("osint"),
                "intro_outro_script": metadata.get("intro_outro_script"),
                "intro_outro_audio_url": metadata.get("intro_outro_audio_url"),
                "translated_clip_url": metadata.get("translated_clip_url"),
            })

        except Exception as e:
            logger.error(f"Error in audio pipeline: {str(e)}", exc_info=True)
            return jsonify({"error": f"Pipeline processing failed: {str(e)}", "steps_applied": metadata["steps_applied"]}), 500


def process_enhance_step(audio_bytes: bytes, input_path: str, temp_dir: str) -> Tuple[bytes, str]:
    """
    Process the enhance step: improve audio quality using FFmpeg.
    
    Args:
        audio_bytes: Current audio bytes
        input_path: Path to the current audio file
        temp_dir: Temporary directory for processing
        
    Returns:
        Tuple of (new audio bytes, new file path)
    """
    logger.info("Processing enhance step")
    
    # Create output path
    output_path = os.path.join(temp_dir, "enhanced.wav")
    
    # Enhance audio using the utility function
    success = enhance_audio_with_ffmpeg(input_path, output_path)
    
    if not success:
        raise RuntimeError("Audio enhancement failed")
    
    # Read the enhanced audio
    with open(output_path, "rb") as f:
        enhanced_data = f.read()
    
    return enhanced_data, output_path


def process_ai_cut_step(audio_bytes: bytes, input_path: str, temp_dir: str, filename: str) -> Tuple[bytes, str, Dict[str, Any]]:
    """
    Process the AI cut step: analyze audio and suggest cuts.
    
    Args:
        audio_bytes: Current audio bytes
        input_path: Path to the current audio file
        temp_dir: Temporary directory for processing
        filename: Original filename
        
    Returns:
        Tuple of (new audio bytes, new file path, AI cut result)
    """
    logger.info("Processing AI cut step")
    
    # Use the AudioService to analyze and cut the audio
    with open(input_path, "rb") as f:
        input_bytes = f.read()
    
    # Call the AI cut function
    result = audio_service.ai_cut_audio(input_bytes, filename)
    
    # Check if there are suggested cuts
    suggested_cuts = result.get("suggested_cuts", [])
    if not suggested_cuts:
        logger.warning("No suggested cuts found in AI cut result")
        return audio_bytes, input_path, result
    
    # Apply the suggested cuts
    output_path = os.path.join(temp_dir, "ai_cut.wav")
    
    # Use the AudioService to apply cuts
    from pydub import AudioSegment
    audio = AudioSegment.from_file(input_path, format="wav")
    cuts_ms = sorted([
        (int(c["start"] * 1000), int(c["end"] * 1000))
        for c in suggested_cuts if 0 <= c["start"] < c["end"]
    ])
    
    merged = []
    for start, end in cuts_ms:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    
    segments = [audio[start:end] for start, end in merged]
    if not segments:
        logger.warning("No valid segments after merging cuts")
        return audio_bytes, input_path, result
    
    final_audio = sum(segments)
    final_audio.export(output_path, format="wav")
    
    # Read the cut audio
    with open(output_path, "rb") as f:
        cut_data = f.read()
    
    return cut_data, output_path, result


def process_voice_isolation_step(audio_bytes: bytes, input_path: str, temp_dir: str) -> Tuple[bytes, str]:
    """
    Process the voice isolation step: separate voice from background noise.
    
    Args:
        audio_bytes: Current audio bytes
        input_path: Path to the current audio file
        temp_dir: Temporary directory for processing
        
    Returns:
        Tuple of (new audio bytes, new file path)
    """
    logger.info("Processing voice isolation step")
    
    # Create output path
    output_path = os.path.join(temp_dir, "isolated.wav")
    
    # Use ElevenLabs API for voice isolation
    import requests
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    if not elevenlabs_api_key:
        raise RuntimeError("Missing ELEVENLABS_API_KEY environment variable")
    
    with open(input_path, "rb") as f:
        response = requests.post(
            "https://api.elevenlabs.io/v1/audio-isolation",
            headers={"xi-api-key": elevenlabs_api_key},
            files={"audio": f}
        )
    
    if response.status_code != 200:
        raise RuntimeError(f"Voice isolation failed: {response.status_code} {response.text}")
    
    # Save the isolated audio
    with open(output_path, "wb") as out_file:
        out_file.write(response.content)
    
    # Read the isolated audio
    with open(output_path, "rb") as f:
        isolated_data = f.read()
    
    return isolated_data, output_path


def process_cut_audio_step(audio_bytes: bytes, input_path: str, temp_dir: str, cuts: List[Dict[str, float]]) -> Tuple[bytes, str]:
    """
    Process the cut audio step: trim audio based on specified cuts.
    
    Args:
        audio_bytes: Current audio bytes
        input_path: Path to the current audio file
        temp_dir: Temporary directory for processing
        cuts: List of cuts with start and end times
        
    Returns:
        Tuple of (new audio bytes, new file path)
    """
    logger.info(f"Processing cut audio step with {len(cuts)} cuts")
    
    # Create output path
    output_path = os.path.join(temp_dir, "cut.wav")
    
    # Use the AudioService to apply cuts
    from pydub import AudioSegment
    audio = AudioSegment.from_file(input_path, format="wav")
    cuts_ms = sorted([
        (int(c["start"] * 1000), int(c["end"] * 1000))
        for c in cuts if 0 <= c["start"] < c["end"]
    ])
    
    if not cuts_ms:
        raise ValueError("No valid cuts provided")
    
    merged = []
    for start, end in cuts_ms:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    
    segments = [audio[start:end] for start, end in merged]
    if not segments:
        raise ValueError("No valid segments after merging cuts")
    
    final_audio = sum(segments)
    final_audio.export(output_path, format="wav")
    
    # Read the cut audio
    with open(output_path, "rb") as f:
        cut_data = f.read()
    
    return cut_data, output_path


def process_analyze_audio_step(audio_bytes: bytes) -> Dict[str, Any]:
    logger.info("Processing analyze audio step")
    analysis_result = audio_service.analyze_audio(audio_bytes)
    return analysis_result


def process_plan_and_mix_sfx_step(audio_bytes: bytes, input_path: str, temp_dir: str, word_timestamps: Optional[list] = None) -> Tuple[bytes, str, Dict[str, Any]]:
    """
    Process the plan and mix SFX step: plan and mix sound effects with the audio.

    Args:
        audio_bytes: Current audio bytes
        input_path: Path to the current audio file
        temp_dir: Temporary directory for processing
        word_timestamps: Optional list of timestamped words

    Returns:
        Tuple of (new audio bytes, new file path, SFX result)
    """
    logger.info("Processing plan and mix SFX step")

    # Call the audio service to plan and mix SFX with optional timestamps
    sfx_result = audio_service.plan_and_mix_sfx(audio_bytes, word_timestamps)

    # Get the mixed audio from the result
    mixed_audio_base64 = sfx_result.get("merged_audio", "")
    if not mixed_audio_base64 or not mixed_audio_base64.startswith("data:audio/wav;base64,"):
        logger.warning("No valid mixed audio returned from plan_and_mix_sfx")
        return audio_bytes, input_path, sfx_result

    # Extract the base64 data and decode it
    mixed_audio_base64 = mixed_audio_base64.split(",")[1]
    mixed_audio = base64.b64decode(mixed_audio_base64)

    # Save the mixed audio to a new file
    output_path = os.path.join(temp_dir, "sfx_mixed.wav")
    with open(output_path, "wb") as f:
        f.write(mixed_audio)

    return mixed_audio, output_path, sfx_result
