# src/backend/routes/transcript/transcription.py

import os
import logging
from flask import Blueprint, request, jsonify, Response
from datetime import datetime
from bson import ObjectId
from elevenlabs.client import ElevenLabs
from backend.services.transcriptionService import TranscriptionService
import gridfs
from backend.database.mongo_connection import get_db, get_fs

fs = gridfs.GridFS(get_db())
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
    
@transcription_bp.route("/get_file/<file_id>", methods=["GET"])
def get_file(file_id):
    try:
        object_id = ObjectId(file_id)
        file_obj = fs.get(object_id)

        if not file_obj:
            return jsonify({"error": "File not found"}), 404

        file_data = file_obj.read()
        return Response(
            file_data,
            mimetype="audio/wav",
            headers={"Content-Disposition": f"attachment; filename={file_obj.filename}"}
        )

    except gridfs.errors.NoFile:
        return jsonify({"error": "File not found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500