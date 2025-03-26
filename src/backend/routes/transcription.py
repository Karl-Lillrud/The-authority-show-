# src/backend/routes/transcript/transcription.py

import os
import logging
from flask import Blueprint, request, jsonify
from elevenlabs.client import ElevenLabs

from backend.services.transcriptionService import TranscriptionService
from backend.services.audioService import AudioService
from backend.services.videoService import VideoService
from backend.repository.Ai_models import fetch_file

transcription_bp = Blueprint("transcription", __name__)
logger = logging.getLogger(__name__)

# Services
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
transcription_service = TranscriptionService(elevenlabs_client)
audio_service = AudioService()
video_service = VideoService()


@transcription_bp.route("/transcribe", methods=["POST"])
def transcribe():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    filename = file.filename
    file_ext = os.path.splitext(filename)[-1].lower()
    file_bytes = file.read()

    is_video = file_ext in [".mp4", ".mov", ".avi", ".mkv", ".webm"]

    try:
        if is_video:
            file_id = video_service.upload_video(file_bytes, filename)
            transcript_data = video_service.analyze_video(file_id)
        else:
            file_id = audio_service.enhance_audio(file_bytes, filename)
            transcript_data = audio_service.analyze_audio(file_bytes)

        return jsonify({
            "file_id": file_id,
            **transcript_data
        })

    except Exception as e:
        logger.error(f"Transcription error: {str(e)}", exc_info=True)
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


@transcription_bp.route("/get_file/<file_id>", methods=["GET"])
def get_file(file_id):
    return fetch_file(file_id)