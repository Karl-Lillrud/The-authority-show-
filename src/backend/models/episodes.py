from marshmallow import Schema, fields, pre_load
from backend.models.podtasks import PodtaskSchema
from typing import Optional  # Import Optional

# Define the directory to save uploaded files
UPLOAD_FOLDER = r"C:\Users\arins\OneDrive\Desktop\uploadfoler"


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
