# src/backend/routes/transcript/transcription.py

import os
import logging
from flask import Blueprint, request, jsonify
from datetime import datetime
from bson import ObjectId
from elevenlabs.client import ElevenLabs

# Import your new service classes or methods:
from backend.services.transcriptionService import TranscriptionService

logger = logging.getLogger(__name__)

# Keep the same blueprint name so app.py doesn’t break
transcription_bp = Blueprint("transcription", __name__)

elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
# Instantiate your service
transcription_service = TranscriptionService(elevenlabs_client)

@transcription_bp.route("/transcribe", methods=["POST"])
def transcribe():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    filename = file.filename
    file_ext = os.path.splitext(filename)[-1].lower()
    is_video = file_ext in [".mp4", ".mov", ".avi", ".mkv", ".webm"]
    file_data = file.read()

    try:
        result = transcription_service.transcribe_file(file_data, filename, is_video)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error during transcription: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

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
