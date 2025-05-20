from marshmallow import Schema, fields, validates, ValidationError
from marshmallow.validate import Length, Range
from datetime import datetime

class EpisodeSchema(Schema):
    id = fields.Str(dump_only=True)
    podcastId = fields.Str(required=True, data_key="podcastId")
    accountId = fields.Str(allow_none=True, data_key="accountId")
    title = fields.Str(required=True, validate=Length(min=1))
    description = fields.Str(allow_none=True)
    summary = fields.Str(allow_none=True)
    subtitle = fields.Str(allow_none=True)
    publishDate = fields.DateTime(allow_none=True, data_key="publishDate")
    duration = fields.Int(allow_none=True)
    audioUrl = fields.Url(allow_none=True, data_key="audioUrl")
    fileSize = fields.Int(allow_none=True, data_key="fileSize")
    fileType = fields.Str(allow_none=True, data_key="fileType")
    guid = fields.Str(allow_none=True)
    link = fields.Url(allow_none=True)
    imageUrl = fields.Url(allow_none=True, data_key="imageUrl")
    season = fields.Int(allow_none=True)
    episode = fields.Int(allow_none=True)
    episodeType = fields.Str(allow_none=True, data_key="episodeType")
    explicit = fields.Bool(allow_none=True)
    author = fields.Str(allow_none=True)
    keywords = fields.List(fields.Str(), allow_none=True)
    chapters = fields.List(fields.Dict(), allow_none=True)

    # ✅ Updated: allow any string for status
    status = fields.Str(allow_none=True)

    isHidden = fields.Bool(allow_none=True, data_key="isHidden")
    recordingAt = fields.DateTime(allow_none=True, data_key="recordingAt")
    isImported = fields.Bool(allow_none=True, data_key="isImported")
    createdAt = fields.DateTime(dump_only=True, data_key="created_at")
    updatedAt = fields.DateTime(dump_only=True, data_key="updated_at")
    highlights = fields.List(fields.Str(), allow_none=True)
    audioEdits = fields.List(fields.Dict(), allow_none=True)

    @validates("duration")
    def validate_duration(self, value):
        if value is not None:
            if not isinstance(value, int):
                raise ValidationError("Duration must be an integer.")
            if value < 0:
                raise ValidationError("Duration cannot be negative.")
        return value

    @validates("publishDate")
    def validate_publish_date(self, value):
        if not isinstance(value, (datetime, type(None))):
            raise ValidationError("publishDate must be a datetime object or null.")
