# audio_routes.py
import logging
import base64
import requests
from flask import Response
from flask import Blueprint, request, jsonify, g
from backend.services.audioService import AudioService
from backend.repository.ai_models import get_file_by_id, add_audio_edit_to_episode
from backend.utils.blob_storage import upload_file_to_blob  
from backend.repository.episode_repository import EpisodeRepository

episode_repo = EpisodeRepository()
logger = logging.getLogger(__name__)
audio_bp = Blueprint("audio_bp", __name__)
audio_service = AudioService()

@audio_bp.route("/audio/enhancement", methods=["POST"])
def audio_enhancement():
    if "audio" not in request.files or "episode_id" not in request.form:
        return jsonify({"error": "Audio file and episode_id are required"}), 400

    audio_file = request.files["audio"]
    episode_id = request.form["episode_id"]
    filename = audio_file.filename
    audio_bytes = audio_file.read()

    try:
        # Kör förbättring och få tillbaka blob_url till enhanced audio
        blob_url = audio_service.enhance_audio(audio_bytes, filename, episode_id)
        return jsonify({"enhanced_audio_url": blob_url})
    except Exception as e:
        logger.error(f"Error enhancing audio: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@audio_bp.route("/get_enhanced_audio", methods=["GET"])
def get_enhanced_audio():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    try:
        response = requests.get(url)
        response.raise_for_status()

        # Smart MIME-guess från filändelsen (eller default till audio/wav)
        content_type = "audio/mpeg" if url.lower().endswith(".mp3") else "audio/wav"

        return Response(response.content, content_type=content_type)
    except Exception as e:
        logger.error(f"Error fetching enhanced audio from blob: {str(e)}")
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
    episode_id = data.get("episode_id")

    if not file_id or not clips or not episode_id:
        return jsonify({"error": "Invalid request data"}), 400

    try:
        start_time = clips[0]["start"]
        end_time = clips[0]["end"]
        clipped_bytes, filename = audio_service.cut_audio_to_bytes(file_id, start_time, end_time)

        podcast_id = episode_repo.get_podcast_id_by_episode(episode_id)
        blob_path = f"users/{g.user_id}/podcasts/{podcast_id}/episodes/{episode_id}/audio/{filename}"
        blob_url = upload_file_to_blob("podmanagerfiles", blob_path, clipped_bytes)

        add_audio_edit_to_episode(
            episode_id=episode_id,
            file_id="external",
            edit_type="manual_clip",
            filename=filename,
            metadata={"blob_url": blob_url, "start": start_time, "end": end_time}
        )

        return jsonify({"clipped_audio_url": blob_url})
    except Exception as e:
        logger.error(f"Error clipping audio: {str(e)}")
        return jsonify({"error": str(e)}), 500


@audio_bp.route("/ai_cut_audio", methods=["POST"])
def ai_cut_audio():
    try:
        file_id = request.json.get("file_id")
        episode_id = request.json.get("episode_id")
        logger.info(f"🔍 Received AI Cut request for file_id: {file_id}")

        if not file_id:
            return jsonify({"error": "file_id is required"}), 400

        result = audio_service.ai_cut_audio_from_id(file_id, episode_id=episode_id)
        return jsonify(result)

    except Exception as e:
        logger.error(f"AI cut failed: {str(e)}")
        return jsonify({"error": str(e)}), 500

@audio_bp.route("/apply_ai_cuts", methods=["POST"])
def apply_ai_cuts():
    data = request.json
    file_id = data["file_id"]
    cuts = data["cuts"]
    episode_id = data.get("episode_id")

    try:
        cleaned_bytes, cleaned_filename = audio_service.apply_cuts_and_return_bytes(file_id, cuts)

        podcast_id = episode_repo.get_podcast_id_by_episode(episode_id)
        blob_path = f"users/{g.user_id}/podcasts/{podcast_id}/episodes/{episode_id}/audio/{cleaned_filename}"
        blob_url = upload_file_to_blob("podmanagerfiles", blob_path, cleaned_bytes)

        add_audio_edit_to_episode(
            episode_id=episode_id,
            file_id="external",
            edit_type="ai_cut",
            filename=cleaned_filename,
            metadata={"blob_url": blob_url, "applied_ai_cuts": cuts}
        )

        return jsonify({"cleaned_file_url": blob_url})
    except Exception as e:
        logger.error(f"❌ Error applying AI cuts: {str(e)}")
        return jsonify({"error": str(e)}), 500

@audio_bp.route("/cut_from_blob", methods=["POST"])
def cut_audio_from_blob():
    if "audio" not in request.files or "episode_id" not in request.form:
        return jsonify({"error": "Audio file and episode_id are required"}), 400

    try:
        audio_file = request.files["audio"]
        episode_id = request.form["episode_id"]
        start = float(request.form["start"])
        end = float(request.form["end"])
        filename = audio_file.filename
        audio_bytes = audio_file.read()

        blob_url = audio_service.cut_audio_from_blob(audio_bytes, filename, episode_id, start, end)
        return jsonify({"clipped_audio_url": blob_url})
    except Exception as e:
        logger.error(f"Error cutting audio from blob: {str(e)}")
        return jsonify({"error": str(e)}), 500

@audio_bp.route("/get_clipped_audio", methods=["GET"])
def get_clipped_audio():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    try:
        response = requests.get(url)
        response.raise_for_status()

        content_type = "audio/mpeg" if url.lower().endswith(".mp3") else "audio/wav"
        return Response(response.content, content_type=content_type)
    except Exception as e:
        logger.error(f"Error fetching clipped audio from blob: {str(e)}")
        return jsonify({"error": str(e)}), 500
