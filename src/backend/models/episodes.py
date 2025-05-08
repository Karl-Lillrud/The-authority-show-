from marshmallow import Schema, fields, pre_load, validates, ValidationError
from backend.models.podtasks import PodtaskSchema
from datetime import datetime
import re


class EpisodeSchema(Schema):
    id = fields.Str(dump_only=True)
    podcastId = fields.Str(required=True, data_key="podcast_id")
    accountId = fields.Str(required=False, allow_none=True)  # Add accountId, make it optional for now
    title = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    summary = fields.Str(allow_none=True)  # Added from RSS parsing
    subtitle = fields.Str(allow_none=True)  # Added from RSS parsing
    publishDate = fields.DateTime(allow_none=True)  # Changed to DateTime for proper handling
    duration = fields.Int(allow_none=True)  # Allow None, ensure it's an integer if provided
    audioUrl = fields.Url(allow_none=True)
    fileSize = fields.Int(allow_none=True)
    fileType = fields.Str(allow_none=True)
    guid = fields.Str(allow_none=True)
    link = fields.Url(allow_none=True)
    imageUrl = fields.Url(allow_none=True)
    season = fields.Str(allow_none=True)  # Changed to Str to handle non-integer values from RSS
    episode = fields.Str(allow_none=True)  # Changed to Str to handle non-integer values from RSS
    episodeType = fields.Str(allow_none=True)
    explicit = fields.Boolean(allow_none=True)
    author = fields.Str(allow_none=True)  # Added from RSS parsing
    keywords = fields.List(fields.Str(), allow_none=True)
    chapters = fields.List(fields.Dict(), allow_none=True)  # Assuming chapters are dicts
    status = fields.Str(allow_none=True)
    isHidden = fields.Boolean(missing=False, allow_none=True)
    recordingAt = fields.DateTime(allow_none=True)
    isImported = fields.Boolean(missing=False, allow_none=True)
    createdAt = fields.DateTime(dump_only=True, data_key="created_at")
    updatedAt = fields.DateTime(dump_only=True, data_key="updated_at")
    highlights = fields.List(fields.Str(), allow_none=True)  # New field for highlights
    audioEdits = fields.List(fields.Dict(), allow_none=True)  # New field for audio edits

    @validates("duration")
    def validate_duration(self, value):
        if value is not None:
            try:
                int(value)  # Check if it can be an int
            except (ValueError, TypeError):
                raise ValidationError("Duration must be a valid integer or null.")
    
    @validates("publishDate")
    def validate_publish_date(self, value):
        if isinstance(value, str):
            try:
                # Attempt to parse if it's a string, useful if RSS provides non-standard date strings
                # This basic parsing might need to be more robust depending on RSS date formats
                return datetime.strptime(value, '%a, %d %b %Y %H:%M:%S %z')  # Example RFC 822 format
            except (ValueError, TypeError):
                # If parsing fails, and it's not None, raise error or handle
                # For now, if it's a string and not parsable, it might fail later if not caught by fields.DateTime
                pass 
        return value  # Return as is if already datetime or None
