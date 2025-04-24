from marshmallow import Schema, fields, pre_load
from backend.models.podtasks import PodtaskSchema
import re


class EpisodeSchema(Schema):
    id = fields.Str()
    podcastId = fields.Str(required=True)
    title = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    publishDate = fields.Str(allow_none=True)  # Ensure publishDate is correctly defined
    duration = fields.Int(allow_none=True)  # Change to integer
    status = fields.Str(allow_none=True)
    recordingAt = fields.DateTime(allow_none=True)  # Allow recordingAt to be optional
    createdAt = fields.DateTime()
    updatedAt = fields.DateTime()
    audioUrl = fields.Url(allow_none=True)
    fileSize = fields.Str(allow_none=True)
    fileType = fields.Str(allow_none=True)
    guid = fields.Str(allow_none=True)
    season = fields.Int(allow_none=True)
    episode = fields.Int(allow_none=True)
    episodeType = fields.Str(allow_none=True)
    explicit = fields.Bool(allow_none=True)
    imageUrl = fields.Url(allow_none=True)
    keywords = fields.List(fields.Str(), allow_none=True)
    chapters = fields.List(fields.Dict(), allow_none=True)
    link = fields.Url(allow_none=True)
    subtitle = fields.Str(allow_none=True)
    summary = fields.Str(allow_none=True)
    author = fields.Str(allow_none=True)
    isHidden = fields.Bool(allow_none=True)
    highlights = fields.List(fields.Str(), allow_none=True)  # New field for highlights
    audioEdits = fields.List(fields.Dict(), allow_none=True)  # New field for audio edits
    isImported = fields.Bool(allow_none=True)
