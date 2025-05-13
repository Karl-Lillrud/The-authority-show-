from datetime import datetime
from flask import Response, jsonify
import gridfs
from gridfs.errors import NoFile
from backend.database.mongo_connection import get_fs, get_db
from backend.repository.episode_repository import EpisodeRepository

episode_repo = EpisodeRepository()

fs = get_fs()  # For file storage only

def save_file(file_bytes: bytes, filename: str, metadata: dict = None) -> str:
    """
    Save file to GridFS with optional metadata and return the file ID as a string.
    """
    if metadata is None:
        metadata = {}

    metadata.setdefault("upload_timestamp", datetime.utcnow())
    file_id = fs.put(file_bytes, filename=filename, metadata=metadata)
    # Always return as string
    return str(file_id)

def fetch_file(file_id: str):
    """
    Fetch file from GridFS using string ID and return as a response.
    """
    try:
        # Store the original string ID
        string_file_id = str(file_id)
        
        # Use string ID directly with GridFS
        # Note: GridFS.get() typically expects ObjectId, so we'll need to adapt the MongoDB connection
        # to accept string IDs or modify the GridFS access pattern
        file_obj = None
        
        # First try directly with string ID (if your GridFS is configured to use string IDs)
        try:
            file_obj = fs.get(string_file_id)
        except Exception:
            # If that fails, we'll look up the file by ID in a different way
            # This uses the files collection directly to find the file by string ID
            db = get_db()
            file_doc = db.fs.files.find_one({"_id": string_file_id})
            if file_doc:
                file_obj = fs.get(string_file_id)
        
        if not file_obj:
            return jsonify({"error": "File not found"}), 404

        file_data = file_obj.read()
        file_type = file_obj.metadata.get("type", "audio")
        if file_type == "video":
            mimetype = "video/mp4"
        elif file_type == "audio":
            mimetype = "audio/wav"
        else:
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
    """
    Get file data as bytes using string ID.
    """
    try:
        # Store the original string ID
        string_file_id = str(file_id)
        
        # Try to get the file using string ID
        try:
            file_obj = fs.get(string_file_id)
        except Exception:
            # If direct access with string ID fails, try finding it another way
            db = get_db()
            file_doc = db.fs.files.find_one({"_id": string_file_id})
            if file_doc:
                file_obj = fs.get(string_file_id)
            else:
                raise NoFile("File not found")
        
        return file_obj.read()
    except Exception as e:
        raise Exception(f"Failed to get file data: {str(e)}")

def get_file_by_id(file_id: str):
    """
    Retrieve file from GridFS by string ID. Returns (file_data: bytes, filename: str).
    Raises FileNotFoundError if not found.
    """
    try:
        # Store the original string ID
        string_file_id = str(file_id)
        
        # Try to get the file using string ID
        try:
            file_obj = fs.get(string_file_id)
        except Exception:
            # If direct access with string ID fails, try finding it another way
            db = get_db()
            file_doc = db.fs.files.find_one({"_id": string_file_id})
            if file_doc:
                file_obj = fs.get(string_file_id)
            else:
                raise NoFile("File not found")
        
        return file_obj.read(), file_obj.filename
    except NoFile:
        raise FileNotFoundError("File not found in GridFS.")
    except Exception as e:
        raise Exception(f"Failed to get file: {str(e)}")