# video_routes.py
import logging
from flask import Blueprint, request, jsonify
from backend.services.videoService import VideoService

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
