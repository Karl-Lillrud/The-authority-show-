# audio_routes.py
import logging
import requests
import json
from flask import Blueprint, request, jsonify, g, Response,session

from backend.services.audioService import AudioService
from backend.services.subscriptionService import SubscriptionService
from backend.services.creditService import consume_credits
from backend.utils.blob_storage import upload_file_to_blob  
from backend.utils.subscription_access import get_max_duration_limit
from backend.utils.ai_utils import check_audio_duration,insufficient_credits_response
from backend.repository.edit_repository import create_edit_entry
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
        user_id = g.user_id
        try:
            consume_credits(user_id, "audio_enhancement")
        except ValueError as e:
            return insufficient_credits_response("audio_enhancement", e)
        
        subscription_service = SubscriptionService()
        subscription = subscription_service.get_user_subscription(user_id)
        plan = subscription.get("plan", "FREE")
        max_duration = get_max_duration_limit(plan)

        check_audio_duration(audio_bytes, max_duration_seconds=max_duration)
        logger.info("Audio duration validated for enhancement")

        blob_url = audio_service.enhance_audio(audio_bytes, filename, episode_id)
        return jsonify({"enhanced_audio_url": blob_url,
                        "clipUrl": blob_url})
    
    except ValueError as e:
        logger.warning(f"Duration validation error: {e}")
        return jsonify({"error": str(e)}), 400
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
        user_id = g.user_id  
        consume_credits(user_id, "ai_audio_analysis") 

        analysis_result = audio_service.analyze_audio(audio_bytes)
        return jsonify(analysis_result)

    except ValueError as e:
            return insufficient_credits_response("audio_analysis", e)

    except Exception as e:
        logger.error(f"Error analyzing audio: {str(e)}")
        return jsonify({"error": str(e)}), 500

@audio_bp.route("/voice_isolate", methods=["POST"])
def isolate_voice():
    if "audio" not in request.files or "episode_id" not in request.form:
        return jsonify({"error": "Audio file and episode_id are required"}), 400

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    # Consume credits BEFORE processing
    try:
        consume_credits(user_id, "voice_isolation")
    except ValueError as e:
        logger.warning(f"User {user_id} has insufficient credits for voice isolation.")
        return jsonify({
            "error": str(e),
            "redirect": "/store"
        }), 403

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

    
@audio_bp.route("/get_isolated_audio", methods=["GET"])
def get_isolated_audio():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400
    
    try:
        response = requests.get(url)
        return Response(response.content, content_type="audio/wav")
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@audio_bp.route("/audio_background_mix", methods=["POST"])
def audio_background_mix():
    """
    Endpoint to generate only the background SFX loop + mixed audio.
    Expects:
      - multipart form with 'audio' file
      - form field 'emotion' (string label from analyze_audio)
    """
    if "audio" not in request.files or "emotion" not in request.form:
        return jsonify({"error": "Missing audio file or emotion label"}), 400

    audio_bytes = request.files["audio"].read()
    emotion     = request.form["emotion"]

    try:
        data = audio_service.generate_background_and_mix(audio_bytes, emotion)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error generating background & mix: {e}")
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
        try:
            consume_credits(g.user_id, "audio_cutting")
        except ValueError as e:
            return insufficient_credits_response("audio_cutting", e)

        start_time = clips[0]["start"]
        end_time = clips[0]["end"]
        clipped_bytes, filename = audio_service.cut_audio_to_bytes(file_id, start_time, end_time)

        podcast_id = episode_repo.get_podcast_id_by_episode(episode_id)
        blob_path = f"users/{g.user_id}/podcasts/{podcast_id}/episodes/{episode_id}/audio/{filename}"
        blob_url = upload_file_to_blob("podmanagerfiles", blob_path, clipped_bytes)

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
        return jsonify({"clipped_audio_url": blob_url})
    except Exception as e:
        logger.error(f"Error clipping audio: {str(e)}")
        return jsonify({"error": str(e)}), 500

@audio_bp.route("/ai_cut_audio", methods=["POST"])
def ai_cut_audio():
    try:
        file_id = request.json.get("file_id")
        episode_id = request.json.get("episode_id")
        logger.info(f"Received AI Cut request for file_id: {file_id}")

        if not file_id:
            return jsonify({"error": "file_id is required"}), 400

        try:
            consume_credits(g.user_id, "ai_audio_cutting")
        except ValueError as e:
            return insufficient_credits_response("ai_audio_cutting", e)

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

        create_edit_entry(
            episode_id=episode_id,
            user_id=g.user_id,
            edit_type="ai_cut_cleaned",
            clip_url=blob_url,
            clipName=f"cleaned_{cleaned_filename}",
            metadata={
                "edit_type": "ai_cut_cleaned"
            }
        )

        return jsonify({"cleaned_file_url": blob_url})
    except Exception as e:
        logger.error(f"Error applying AI cuts: {str(e)}")
        return jsonify({"error": str(e)}), 500

@audio_bp.route("/cut_from_blob", methods=["POST"])
def cut_audio_from_blob():
    if "audio" not in request.files or "episode_id" not in request.form:
        return jsonify({"error": "Audio file and episode_id are required"}), 400

    try:
        try:
            consume_credits(g.user_id, "audio_cutting")
        except ValueError as e:
            return insufficient_credits_response("cut_from_blob", e)

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
    
@audio_bp.route("/ai_cut_from_blob", methods=["POST"])
def ai_cut_from_blob():
    if "audio" not in request.files or "episode_id" not in request.form:
        return jsonify({"error": "Audio file and episode_id are required"}), 400

    try:
        try:
            consume_credits(g.user_id, "ai_audio_cutting")
        except ValueError as e:
            return insufficient_credits_response("ai_audio_cutting", e)

        audio_file = request.files["audio"]
        episode_id = request.form["episode_id"]
        filename = audio_file.filename
        audio_bytes = audio_file.read()

        result = audio_service.ai_cut_audio(audio_bytes, filename, episode_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI cut from blob failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@audio_bp.route("/apply_ai_cuts_from_blob", methods=["POST"])
def apply_ai_cuts_from_blob():
    if "audio" not in request.files or "episode_id" not in request.form or "cuts" not in request.form:
        return jsonify({"error": "Missing audio, episode_id or cuts"}), 400

    try:
        audio_file = request.files["audio"]
        episode_id = request.form["episode_id"]
        cuts = json.loads(request.form["cuts"])
        filename = audio_file.filename
        audio_bytes = audio_file.read()

        blob_url = audio_service.apply_cuts_on_blob(audio_bytes, filename, cuts, episode_id)
        return jsonify({"cleaned_file_url": blob_url})
    except Exception as e:
        logger.error(f"Error applying AI cuts from blob: {str(e)}")
        return jsonify({"error": str(e)}), 500

@audio_bp.route("/get_cleaned_audio", methods=["GET"])
def get_cleaned_audio():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    try:
        response = requests.get(url)
        response.raise_for_status()

        content_type = "audio/mpeg" if url.lower().endswith(".mp3") else "audio/wav"
        return Response(response.content, content_type=content_type)
    except Exception as e:
        logger.error(f"Error fetching cleaned audio from blob: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@audio_bp.route("/plan_and_mix_sfx", methods=["POST"])
def plan_and_mix_sfx():
    if "audio" not in request.files:
        return jsonify({"error": "Missing audio file"}), 400

    audio_bytes = request.files["audio"].read()

    try:
        data = audio_service.plan_and_mix_sfx(audio_bytes)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error generating SFX plan & mix: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    
@audio_bp.route("/proxy_audio")
def proxy_audio():
    from flask import request, Response
    import requests

    url = request.args.get("url")
    logger.info(f"🛰️ Proxy fetching: {url}")

    if not url:
        return jsonify({"error": "Missing 'url' query param"}), 400

    try:
        r = requests.get(url, stream=True, timeout=10)
        if r.status_code != 200:
            logger.warning(f"❌ Upstream fetch failed with status {r.status_code}")
            return jsonify({"error": f"Upstream fetch failed: {r.status_code}"}), r.status_code

        return Response(
            r.iter_content(chunk_size=4096),
            content_type=r.headers.get("Content-Type", "audio/mpeg"),
        )
    except Exception as e:
        logger.error(f"❌ Failed to proxy fetch: {e}")
        return jsonify({"error": str(e)}), 500
