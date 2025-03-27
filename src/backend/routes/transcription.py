# src/backend/routes/transcript/transcription.py

import os
import logging
import subprocess
from datetime import datetime
from io import BytesIO
from flask import Blueprint, request, jsonify
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf
import tempfile

from elevenlabs.client import ElevenLabs
from backend.database.mongo_connection import get_fs
from backend.services.transcriptionService import TranscriptionService
from backend.services.audioService import AudioService
from backend.services.videoService import VideoService
from backend.repository.Ai_models import fetch_file, save_file, get_file_by_id
from backend.utils.text_utils import generate_show_notes,generate_ai_suggestions
from backend.utils.ai_utils import remove_filler_words


transcription_bp = Blueprint("transcription", __name__)
logger = logging.getLogger(__name__)
fs = get_fs()

# Services
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
transcription_service = TranscriptionService()
audio_service = AudioService()
video_service = VideoService()

@transcription_bp.route("/transcribe", methods=["POST"])
def transcribe():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    filename = file.filename
    file_ext = os.path.splitext(filename)[-1].lower()
    is_video = file_ext in ["mp4", "mov", "avi", "mkv", "webm"]

    try:
        # 🟢 Extract audio if needed
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

        # 🧠 Transcribe using service
        result = transcription_service.transcribe_audio(audio_bytes, filename)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Transcription failed: {e}", exc_info=True)
        return jsonify({"error": "Transcription failed", "details": str(e)}), 500


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
    
    
# Function to check if a file already exists in MongoDB GridFS
def file_exists(filename):
    existing_file = fs.find_one({"filename": filename})
    return existing_file if existing_file else None


# get audio info
@transcription_bp.route("/get_audio_info", methods=["POST"])
def get_audio_info():
    """Generate waveform and get duration of uploaded audio file, now using MongoDB GridFS."""

    if "audio" not in request.files:
        logger.error("❌ ERROR: No audio file provided")
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
        logger.info(f"📥 Retrieved original file from GridFS with ID: {file_id}")

        # Save to a temporary file for analysis
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(file_data)
            temp_file_path = temp_file.name
        logger.info(f"📂 Temporary file created at: {temp_file_path}")

        # Load audio using SoundFile
        data, sample_rate = sf.read(temp_file_path)

        # Check if the audio is empty
        if data is None or len(data) == 0:
            logger.error("❌ ERROR: Loaded audio is empty")
            return jsonify({"error": "Loaded audio is empty"}), 500

        duration = len(data) / sample_rate
        logger.info(f"🕒 Audio duration: {duration} seconds")

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

        logger.info(f"📤 Waveform saved to MongoDB GridFS with ID: {waveform_file_id}")

        logger.info(f"📤 Waveform saved to MongoDB GridFS with ID: {waveform_file_id}")

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
        logger.error(f"❌ ERROR: Failed to process audio - {str(e)}")
        return jsonify({"error": f"Failed to process audio: {str(e)}"}), 500