# audio_routes.py
import logging
from flask import Blueprint, request, jsonify
from backend.services.audioService import AudioService

logger = logging.getLogger(__name__)
audio_bp = Blueprint("audio_bp", __name__)
audio_service = AudioService()

@audio_bp.route("/audio/enhancement", methods=["POST"])
def audio_enhancement():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    filename = audio_file.filename
    audio_bytes = audio_file.read()

    try:
        enhanced_file_id = audio_service.enhance_audio(audio_bytes, filename)
        return jsonify({"enhanced_audio": enhanced_file_id})
    except Exception as e:
        logger.error(f"Error enhancing audio: {str(e)}")
        return jsonify({"error": str(e)}), 500


@audio_bp.route("/audio_analysis", methods=["POST"])
def audio_analysis():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    audio_bytes = audio_file.read()

    try:
        analysis_result = audio_service.analyze_audio(audio_bytes)
        return jsonify(analysis_result)
    except Exception as e:
        logger.error(f"Error analyzing audio: {str(e)}")
        return jsonify({"error": str(e)}), 500


@audio_bp.route("/clip_audio", methods=["POST"])
def clip_audio():
    data = request.json
    file_id = data.get("file_id")
    clips = data.get("clips", [])

    if not file_id or not clips:
        return jsonify({"error": "Invalid request data"}), 400

    try:
        # Example: just handle the first clip
        start_time = clips[0]["start"]
        end_time = clips[0]["end"]
        clipped_id = audio_service.cut_audio(file_id, start_time, end_time)
        return jsonify({"clipped_audio": clipped_id})
    except Exception as e:
        logger.error(f"Error clipping audio: {str(e)}")
        return jsonify({"error": str(e)}), 500

@audio_bp.route("/ai_cut_audio", methods=["POST"])
def ai_cut_audio():
    try:
        file_id = request.json.get("file_id")
        logger.info(f"🔍 Received AI Cut request for file_id: {file_id}")

        if not file_id:
            return jsonify({"error": "file_id is required"}), 400

        result = audio_service.ai_cut_audio_from_id(file_id)
        return jsonify(result)

    except Exception as e:
        logger.error(f"AI cut failed: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@audio_bp.route("/apply_ai_cuts", methods=["POST"])
def apply_ai_cuts():
    data = request.json
    file_id = data["file_id"]
    cuts = data["cuts"]
    try:
        cleaned_id = audio_service.apply_cuts_and_return_new_file(file_id, cuts)
        return jsonify({"cleaned_file_id": cleaned_id}), 200
    except Exception as e:
        logger.error(f"❌ Error applying AI cuts: {str(e)}")
        return jsonify({"error": str(e)}), 500