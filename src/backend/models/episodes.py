from marshmallow import Schema, fields, pre_load
from backend.models.podtasks import PodtaskSchema
import re


class EpisodeSchema(Schema):
    title = fields.String(required=True)
    description = fields.String()
    pubDate = fields.String()
    audio = fields.Dict()
    guid = fields.String()
    season = fields.Integer(allow_none=True)
    episode = fields.Integer(allow_none=True)
    episodeType = fields.String(allow_none=True)
    explicit = fields.String(allow_none=True)
    image = fields.String(allow_none=True)
    keywords = fields.String(allow_none=True)
    chapters = fields.Raw(allow_none=True)
    link = fields.String()
    subtitle = fields.String(allow_none=True)
    summary = fields.String(allow_none=True)
    author = fields.String()
    isHidden = fields.Boolean(allow_none=True)
    duration = fields.Integer(allow_none=True)
    isImported = fields.Boolean(allow_none=True)
    fileSize = fields.String(allow_none=True)
    fileType = fields.String(allow_none=True)
    audioUrl = fields.String(allow_none=True)
    imageUrl = fields.String(allow_none=True)
    podcastId = fields.String(allow_none=True)
    status = fields.String(allow_none=True)
    publishDate = fields.String(allow_none=True)