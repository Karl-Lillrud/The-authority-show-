from flask import Blueprint, send_file, jsonify
from backend.database.mongo_connection import get_fs
from bson import ObjectId
from io import BytesIO
import logging

files_bp = Blueprint("files", __name__)
fs = get_fs()
logger = logging.getLogger(__name__)

@files_bp.route("/<file_id>", methods=["GET"])
def get_file(file_id):
    """Serve a file from GridFS"""
    try:
        # Get the file from GridFS
        file_obj = fs.get(ObjectId(file_id))
        if not file_obj:
            return jsonify({"error": "File not found"}), 404

        # Create a BytesIO object from the file data
        file_data = BytesIO(file_obj.read())
        
        # Get the content type from the file metadata or default to audio/mpeg
        content_type = file_obj.content_type if hasattr(file_obj, 'content_type') else 'audio/mpeg'
        
        # Send the file with the appropriate content type
        return send_file(
            file_data,
            mimetype=content_type,
            as_attachment=False,
            download_name=file_obj.filename
        )

    except Exception as e:
        logger.error(f"Error serving file {file_id}: {e}")
        return jsonify({"error": str(e)}), 500 