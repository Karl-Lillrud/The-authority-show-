from marshmallow import Schema, fields, validates, ValidationError
from datetime import datetime

class EpisodeSchema(Schema):
    id = fields.Str(dump_only=True)
    podcastId = fields.Str(data_key="podcastId")
    accountId = fields.Str(required=False, allow_none=True)
    title = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    summary = fields.Str(allow_none=True)
    subtitle = fields.Str(allow_none=True)
    publishDate = fields.DateTime(allow_none=True)
    duration = fields.Int(allow_none=True)
    audioUrl = fields.Url(allow_none=True)
    fileSize = fields.Int(allow_none=True)
    fileType = fields.Str(allow_none=True)
    guid = fields.Str(allow_none=True)
    link = fields.Url(allow_none=True)
    imageUrl = fields.Url(allow_none=True)
    season = fields.Str(allow_none=True)
    episode = fields.Str(allow_none=True)
    episodeType = fields.Str(allow_none=True)
    explicit = fields.Boolean(allow_none=True)
    author = fields.Str(allow_none=True)
    keywords = fields.List(fields.Str(), allow_none=True)
    chapters = fields.List(fields.Dict(), allow_none=True)
    status = fields.Str(allow_none=True)
    isHidden = fields.Boolean(load_default=False, allow_none=True)
    recordingAt = fields.DateTime(allow_none=True)
    isImported = fields.Boolean(load_default=False, allow_none=True)
    createdAt = fields.DateTime(dump_only=True, data_key="created_at")
    updatedAt = fields.DateTime(dump_only=True, data_key="updated_at")
    highlights = fields.List(fields.Str(), allow_none=True)
    audioEdits = fields.List(fields.Dict(), allow_none=True)

    @validates("duration")
    def validate_duration(self, value):
        if value is not None:
            if not isinstance(value, int):
                raise ValidationError("Duration must be an integer or null.")

    @validates("publishDate")
    def validate_publish_date(self, value):
        if not isinstance(value, (datetime, type(None))):
            raise ValidationError("publishDate must be a datetime object or null.")
