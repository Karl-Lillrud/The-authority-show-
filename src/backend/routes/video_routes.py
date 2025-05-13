# video_routes.py
import logging
from flask import Blueprint, request, jsonify, Response, g
import gridfs
from backend.services.videoService import VideoService
from backend.repository.ai_models import get_file_data  # if you use it elsewhere
from backend.database.mongo_connection import get_fs
from backend.services.creditService import consume_credits


fs = get_fs()
logger = logging.getLogger(__name__)
video_bp = Blueprint("video_bp", __name__)
video_service = VideoService()


@video_bp.route("/ai_videoedit", methods=["POST"])
def ai_videoedit():
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files["video"]
    video_bytes = video_file.read()
    filename = video_file.filename

    try:
        video_id = video_service.upload_video(video_bytes, filename)
        return jsonify({"message": "Video uploaded", "video_id": video_id})
    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}")
        return jsonify({"error": str(e)}), 500


@video_bp.route("/ai_videoenhance", methods=["POST"])
def ai_videoenhance():
    data = request.json
    video_id = data.get("video_id")
    if not video_id:
        return jsonify({"error": "No video_id provided"}), 400

    try:
        try:
            consume_credits(g.user_id, "video_enhancement")
        except ValueError as e:
            logger.warning(f"User {g.user_id} has insufficient credits for video_enhancement: {e}")
            return jsonify({
                "error": str(e),
                "redirect": "/store"
            }), 403

        processed_id = video_service.enhance_video(video_id)
        return jsonify({"processed_video_id": processed_id})
    except Exception as e:
        logger.error(f"Error enhancing video: {str(e)}")
        return jsonify({"error": str(e)}), 500


@video_bp.route("/ai_videoanalysis", methods=["POST"])
def ai_videoanalysis():
    data = request.json
    video_id = data.get("video_id")
    if not video_id:
        return jsonify({"error": "No video_id provided"}), 400

    try:
        analysis = video_service.analyze_video(video_id)
        return jsonify(analysis)
    except Exception as e:
        logger.error(f"Error analyzing video: {str(e)}")
        return jsonify({"error": str(e)}), 500


@video_bp.route("/clip_video", methods=["POST"])
def clip_video():
    data = request.json
    video_id = data.get("video_id")
    clips = data.get("clips", [])

    if not video_id or not clips:
        return jsonify({"error": "Invalid request data"}), 400

    try:
        start_time = clips[0]["start"]
        end_time = clips[0]["end"]
        clipped_id = video_service.cut_video(video_id, start_time, end_time)
        return jsonify({"clipped_video": clipped_id})
    except Exception as e:
        logger.error(f"Error clipping video: {str(e)}")
        return jsonify({"error": str(e)}), 500


@video_bp.route("/get_video/<file_id>", methods=["GET"])
def get_video(file_id: str):
    try:
        file_obj = fs.get(file_id)
        if not file_obj:
            return jsonify({"error": "File not found"}), 404

        file_data = file_obj.read()
        return Response(
            file_data,
            mimetype="video/mp4",
            headers={
                "Content-Disposition": f"attachment; filename={file_obj.filename}"
            },
        )
    except gridfs.errors.NoFile:
        return jsonify({"error": "File not found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

