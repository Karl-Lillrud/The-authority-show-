import os
from marshmallow import Schema, fields, pre_load
from backend.models.podtasks import PodtaskSchema
from typing import Optional  # Import Optional

# Define the directory to save uploaded files, Example:
# UPLOAD_FOLDER = r"C:\Users\username\path\to\upload\folder"
UPLOAD_FOLDER = r"C:\Users\sarwe\Desktop\LIa"

# Check if the UPLOAD_FOLDER path exists and is accessible
try:
    if not os.path.exists(UPLOAD_FOLDER) or not os.access(UPLOAD_FOLDER, os.W_OK):
        raise PermissionError(
            f"UPLOAD_FOLDER path '{UPLOAD_FOLDER}' is not accessible. "
            "Please update the path in 'episodes.py' to a valid directory."
        )
except PermissionError as e:
    # Re-raise the error with a simplified traceback
    raise SystemExit(f"{__file__}:11: {e}")


class EpisodeSchema(Schema):
    id = fields.Str()
    podcastId = fields.Str(required=True)
    title = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    publishDate = fields.DateTime(allow_none=True)
    duration = fields.Int(allow_none=True)
    status = fields.Str(allow_none=True)
    defaultTasks = fields.List(fields.Nested(PodtaskSchema), allow_none=True)
    createdAt = fields.DateTime()
    updatedAt = fields.DateTime()
    mp3File: Optional[bytes] = None  # Assuming mp3File is a binary file

    @pre_load
    def process_empty_strings(self, data, **kwargs):
        # Convert empty strings to None for fields that expect specific types
        for key in ["publishDate", "description", "duration", "status"]:
            if key in data and data[key] == "":
                data[key] = None
        return data
