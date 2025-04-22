from datetime import datetime
from bson import ObjectId
from flask import Response, jsonify
import gridfs
from gridfs.errors import NoFile
from backend.database.mongo_connection import get_fs
from backend.repository.episode_repository import EpisodeRepository

episode_repo = EpisodeRepository()

fs = get_fs()

def save_file(file_bytes: bytes, filename: str, metadata: dict = None) -> str:
    """
    Save file to GridFS with optional metadata and return the file ID as a string.
    """
    if metadata is None:
        metadata = {}

    metadata.setdefault("upload_timestamp", datetime.utcnow())
    file_id = fs.put(file_bytes, filename=filename, metadata=metadata)
    return str(file_id)

def fetch_file(file_id: str):
    try:
        file_obj = fs.get(ObjectId(file_id))
        if not file_obj:
            return jsonify({"error": "File not found"}), 404

        file_data = file_obj.read()
        # Check metadata for file type, default to audio if not provided
        file_type = file_obj.metadata.get("type", "audio")
        if file_type == "video":
            mimetype = "video/mp4"
        elif file_type == "audio":
            mimetype = "audio/wav"
        else:
            # Fallback or add more types as needed
            mimetype = "application/octet-stream"

        return Response(
            file_data,
            mimetype=mimetype,
            headers={"Content-Disposition": f"attachment; filename={file_obj.filename}"}
        )
    except gridfs.errors.NoFile:
        return jsonify({"error": "File not found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_file_data(file_id: str) -> bytes:
    file_obj = fs.get(ObjectId(file_id))
    return file_obj.read()

def get_file_by_id(file_id: str):
    """
    Retrieve file from GridFS by ID. Returns (file_data: bytes, filename: str).
    Raises FileNotFoundError if not found.
    """
    try:
        file_obj = fs.get(ObjectId(file_id))
        return file_obj.read(), file_obj.filename
    except NoFile:
        raise FileNotFoundError("File not found in GridFS.")

def add_audio_edit_to_episode(episode_id: str, file_id: str, edit_type: str, filename: str, metadata: dict = None):
    """
    Push a new audio edit entry into the episode's `audioEdits` array.
    """
    metadata = metadata or {}

    edit_entry = {
        "fileId": str(file_id),
        "editType": edit_type,
        "filename": filename,
        "createdAt": datetime.utcnow().isoformat(),
        "metadata": metadata
    }

    try:
        result = episode_repo.collection.update_one(
            {"_id": episode_id},
            {"$push": {"audioEdits": edit_entry}}
        )
        return result.modified_count == 1
    except Exception as e:
        raise RuntimeError(f"Failed to add audio edit to episode: {str(e)}")