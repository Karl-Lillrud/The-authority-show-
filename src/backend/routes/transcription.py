# src/backend/routes/transcript/transcription.py
import os
import logging
import subprocess
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, session,Response, g
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf
import tempfile
import requests
from elevenlabs.client import ElevenLabs
from backend.database.mongo_connection import get_fs, get_db
from backend.services.transcriptionService import TranscriptionService
from backend.services.subscriptionService import SubscriptionService
from backend.services.audioService import AudioService
from backend.services.videoService import VideoService
from backend.services.creditService import consume_credits
from backend.repository.edit_repository import save_transcription_edit
from backend.repository.ai_models import fetch_file, save_file, get_file_by_id
from backend.utils.transcription_utils import check_audio_duration
from backend.utils.subscription_access import get_max_duration_limit
from backend.utils.text_utils import get_osint_info, create_podcast_scripts_paid

transcription_bp = Blueprint("transcription", __name__)
logger = logging.getLogger(__name__)
fs = get_fs()
db = get_db()

# Services
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
transcription_service = TranscriptionService()
audio_service = AudioService()
video_service = VideoService()
subscription_service = SubscriptionService()

@transcription_bp.route("/transcribe", methods=["POST"])
def transcribe():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    filename = file.filename
    file_ext = os.path.splitext(filename)[-1].lower()
    is_video = file_ext in ["mp4", "mov", "avi", "mkv", "webm"]
    
    try:
        user_id = session.get("user_id")

        # Check and enforce credit limit BEFORE doing any processing
        try:
            consume_credits(user_id, "transcription")
        except ValueError as e:
            logger.warning(f"User {user_id} has insufficient credits for transcription.")
            return jsonify({
                "error": str(e),
                "redirect": "/store"
            }), 403

        # Extract audio if needed
        if is_video:
            temp_video_path = f"/tmp/{filename}"
            temp_audio_path = temp_video_path.replace(file_ext, ".wav")

            file.save(temp_video_path)
            subprocess.run(
                f'ffmpeg -i "{temp_video_path}" -ac 1 -ar 16000 "{temp_audio_path}" -y',
                shell=True, check=True
            )
            with open(temp_audio_path, "rb") as f:
                audio_bytes = f.read()
            os.remove(temp_video_path)
            os.remove(temp_audio_path)
        else:
            audio_bytes = file.read()

        # Subscribe plan and duration validation
        subscription = subscription_service.get_user_subscription(user_id)
        subscription_plan = subscription["plan"] if subscription else "FREE"
        logger.info(f"User {user_id} subscription plan: {subscription_plan}")

        max_duration = get_max_duration_limit(subscription_plan)
        logger.info(f"Max transcription duration allowed: {max_duration} seconds")

        # Check audio duration
        logger.info("Checking uploaded audio duration...")
        check_audio_duration(audio_bytes, max_duration_seconds=max_duration)
        logger.info("Audio duration is within the allowed limit.")

        # Transcription process
        logger.info(f"Starting transcription for file: {filename}")
        result = transcription_service.transcribe_audio(audio_bytes, filename)
        logger.info("Transcription completed successfully.")

        # Save as transcription edit
        episode_id = request.form.get("episode_id") or request.args.get("episode_id")
        transcription_text = result["full_transcript"]
        sentiment_result = transcription_service.get_sentiment_and_sfx(transcription_text)

        save_transcription_edit(
            user_id=user_id,
            episode_id=episode_id,
            transcript_text=transcription_text,
            raw_transcript=result["raw_transcription"],
            sentiment=sentiment_result["emotions"],
            emotion=sentiment_result["emotions"],
            filename=filename
        )
        return jsonify(result)

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error during transcription: {e}", exc_info=True)
        return jsonify({"error": "Transcription failed", "details": str(e)}), 500

@transcription_bp.route("/clean", methods=["POST"])
def clean_transcript():
    user_id = g.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.json
    transcript = data.get("transcript", "")
    if not transcript:
        return jsonify({"error": "No transcript provided"}), 400
    try:
        consume_credits(user_id, "clean_transcript")
    except ValueError as e:
        logger.warning(f"User {user_id} has insufficient credits for cleaning.")
        return jsonify({
            "error": str(e),
            "redirect": "/store"
        }), 403

    clean = transcription_service.get_clean_transcript(transcript)
    return jsonify({"clean_transcript": clean})

@transcription_bp.route("/ai_suggestions", methods=["POST"])
def ai_suggestions():
    user_id = g.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.json
    transcript = data.get("transcript", "")
    if not transcript:
        return jsonify({"error": "No transcript provided"}), 400

    try:
        consume_credits(user_id, "ai_suggestions")
    except ValueError as e:
        return jsonify({
            "error": str(e),
            "redirect": "/store"
        }), 403

    suggestions = transcription_service.get_ai_suggestions(transcript)
    return jsonify(suggestions)

@transcription_bp.route("/show_notes", methods=["POST"])
def show_notes():
    user_id = g.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.json
    transcript = data.get("transcript", "")
    if not transcript:
        return jsonify({"error": "No transcript provided"}), 400

    try:
        consume_credits(user_id, "show_notes")
    except ValueError as e:
        return jsonify({
            "error": str(e),
            "redirect": "/store"
        }), 403

    notes = transcription_service.get_show_notes(transcript)
    return jsonify({"show_notes": notes})

@transcription_bp.route("/quotes", methods=["POST"])
def quotes():
    user_id = g.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.json
    transcript = data.get("transcript", "")
    if not transcript:
        return jsonify({"error": "No transcript provided"}), 400

    try:
        consume_credits(user_id, "ai_quotes")
    except ValueError as e:
        return jsonify({
            "error": str(e),
            "redirect": "/store"
        }), 403

    quotes_text = transcription_service.get_quotes(transcript)
    return jsonify({"quotes": quotes_text})

@transcription_bp.route("/quote_images", methods=["POST"])
def quote_images():
    user_id = g.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.json
    quotes_text = data.get("quotes", "")
    if not quotes_text.strip():
        return jsonify({"error": "No quotes provided"}), 400

    try:
        consume_credits(user_id, "ai_quote_images")
    except ValueError as e:
        return jsonify({
            "error": str(e),
            "redirect": "/store"
        }), 403

    quotes_list = [q.strip() for q in quotes_text.split("\n\n") if q.strip()]
    image_urls = transcription_service.get_quote_images(quotes_list)
    return jsonify({"quote_images": image_urls})

@transcription_bp.route("/translate", methods=["POST"])
def translate():
    data = request.json
    text = data.get("text", "")
    language = data.get("language", "English")

    try:
        translated = transcription_service.translate_text(text, language)
        return jsonify({"translated_text": translated})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@transcription_bp.route("/get_file/<file_id>", methods=["GET"])
def get_file(file_id):
    return fetch_file(file_id)

@transcription_bp.route("/ai_cut_audio", methods=["POST"])
def ai_cut_audio():
    try:
        if "file_id" in request.json:
            file_id = request.json["file_id"]
            file_bytes, filename = get_file_by_id(file_id)
        elif "audio" in request.files:
            file = request.files["audio"]
            file_bytes = file.read()
            filename = file.filename
            file_id = save_file(file_bytes, filename, {"type": "transcription"})
        else:
            return jsonify({"error": "No file or file_id provided"}), 400

        result = audio_service.ai_cut_audio(file_bytes, filename)
        result["file_id"] = str(file_id)
        return jsonify(result), 200

    except Exception as e:
        logger.error(f"AI cut failed: {e}")
        return jsonify({"error": str(e)}), 500
    
# # Function to check if a file already exists in MongoDB GridFS
# def file_exists(filename):
#     existing_file = fs.find_one({"filename": filename})
#     return existing_file if existing_file else None

# get audio info
@transcription_bp.route("/get_audio_info", methods=["POST"])
def get_audio_info():
    """Generate waveform and get duration of uploaded audio file, now using MongoDB GridFS."""

    if "audio" not in request.files:
        logger.error("ERROR: No audio file provided")
        return jsonify({"error": "No audio file provided"}), 400

    try:
        # Retrieve the uploaded file
        audio_file = request.files["audio"]
        filename = audio_file.filename

        # Save the original file to MongoDB
        file_id = fs.put(
            audio_file.read(),
            filename=filename,
            metadata={
                "upload_timestamp": datetime.utcnow(),
                "type": "transcription",
            },  # Add type
        )

        # Retrieve the file from GridFS for processing
        file_data = fs.get(file_id).read()
        logger.info(f"Retrieved original file from GridFS with ID: {file_id}")

        # Save to a temporary file for analysis
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(file_data)
            temp_file_path = temp_file.name
        logger.info(f"Temporary file created at: {temp_file_path}")

        # Load audio using SoundFile
        data, sample_rate = sf.read(temp_file_path)

        # Check if the audio is empty
        if data is None or len(data) == 0:
            logger.error("ERROR: Loaded audio is empty")
            return jsonify({"error": "Loaded audio is empty"}), 500

        duration = len(data) / sample_rate
        logger.info(f"Audio duration: {duration} seconds")

        # Generate waveform image
        waveform_filename = f"waveform_{filename}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as wf_temp:
            waveform_path = wf_temp.name

        fig, ax = plt.subplots(figsize=(10, 3))
        time_axis = np.linspace(0, duration, num=len(data))
        ax.plot(time_axis, data, color="blue")
        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Amplitude")
        plt.savefig(waveform_path)
        plt.close(fig)

        # Save waveform to MongoDB GridFS with upload_timestamp
        with open(waveform_path, "rb") as wf:
            waveform_file_id = fs.put(
                wf.read(),
                filename=waveform_filename,
                metadata={
                    "upload_timestamp": datetime.utcnow(),
                    "type": "transcription",
                },  # Add type
            )
        logger.info(f"Waveform saved to MongoDB GridFS with ID: {waveform_file_id}")
        # Cleanup temp files
        os.remove(temp_file_path)
        os.remove(waveform_path)

        return jsonify(
            {
                "duration": duration,
                "audio_file_id": str(file_id),  # Send correct file ID for actual audio
                "waveform": str(waveform_file_id),  # Send waveform file ID
            }
        )

    except Exception as e:
        logger.error(f"ERROR: Failed to process audio - {str(e)}")
        return jsonify({"error": f"Failed to process audio: {str(e)}"}), 500

@transcription_bp.route("/voice_isolate", methods=["POST"])
def isolate_voice():
    if "audio" not in request.files or "episode_id" not in request.form:
        return jsonify({"error": "Audio file and episode_id are required"}), 400

    audio_file = request.files["audio"]
    episode_id = request.form["episode_id"]
    filename = audio_file.filename
    audio_bytes = audio_file.read()

    try:
        blob_url = audio_service.isolate_voice(audio_bytes, filename, episode_id)
        return jsonify({"isolated_blob_url": blob_url})  
    except Exception as e:
        logger.error(f"Error during voice isolation: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@transcription_bp.route("/get_isolated_audio", methods=["GET"])
def get_isolated_audio():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400
    try:
        response = requests.get(url)
        return Response(response.content, content_type="audio/wav")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@transcription_bp.route("/ai_edits", methods=["GET"])
def render_ai_edits():
    episode_id = request.args.get("episodeId")
    if not episode_id or episode_id == "unknown":
        logger.error(f"Invalid or missing episode ID: {episode_id}")
        return jsonify({"error": "Invalid or missing episode ID"}), 400

    logger.info(f"Rendering AI Edits page for episode ID: {episode_id}")
    try:
        return render_template("ai_edits/ai_edits.html", 
                               episode_id=episode_id, 
                               user_id=session.get("user_id"))
    except Exception as e:
        logger.error(f"Error rendering ai_edits.html: {e}")
        return jsonify({"error": "Failed to render AI Edits page"}), 500
    
@transcription_bp.route("/analyze_sentiment_sfx", methods=["POST"])
def analyze_sentiment_sfx():
    data = request.json
    transcript = data.get("transcript", "")
    if not transcript:
        return jsonify({"error": "No transcript provided"}), 400

    try:
        result = transcription_service.get_sentiment_and_sfx(transcript)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error analyzing sentiment + SFX: {str(e)}")
        return jsonify({"error": str(e)}), 500

@transcription_bp.route("/osint_lookup", methods=["POST"])
def osint_lookup():
    data = request.get_json()
    guest_name = data.get("guest_name")
    if not guest_name:
        return jsonify({"error": "Missing guest name"}), 400
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    try:
        consume_credits(user_id, "ai_osint")
    except ValueError as e:
        return jsonify({"error": str(e), "redirect": "/store"}), 403

    try:
        osint_info = get_osint_info(guest_name)
        return jsonify({"osint_info": osint_info})
    except Exception as e:
        logger.error(f"OSINT error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@transcription_bp.route("/generate_intro_outro", methods=["POST"])
def generate_intro_outro():
    data = request.get_json()
    guest_name = data.get("guest_name")
    transcript = data.get("transcript")

    if not guest_name or not transcript:
        return jsonify({"error": "Missing guest name or transcript"}), 400

    try:
        user_id = session.get("user_id")

        try:
            consume_credits(user_id, "ai_intro_outro")
        except ValueError as e:
            return jsonify({
                "error": str(e),
                "redirect": "/store"
            }), 403

        osint_info = get_osint_info(guest_name)
        script = create_podcast_scripts_paid(osint_info, guest_name, transcript)

        return jsonify({"script": script})
    except Exception as e:
        logger.error(f"Intro/Outro generation error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@transcription_bp.route("/intro_outro_audio", methods=["POST"])
def generate_intro_outro_audio():
    data = request.get_json()
    script = data.get("script")

    if not script:
        return jsonify({"error": "Missing script"}), 400

    try:
        from backend.utils.text_utils import text_to_speech_with_elevenlabs
        audio_bytes = text_to_speech_with_elevenlabs(script)

        import base64
        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        return jsonify({"audio_base64": f"data:audio/mp3;base64,{b64_audio}"})
    except Exception as e:
        logger.error(f"ElevenLabs TTS failed: {str(e)}")
        return jsonify({"error": str(e)}), 500

