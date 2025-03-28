from marshmallow import Schema, fields, pre_load, validate
from backend.models.podtasks import PodtaskSchema
import re


class EpisodeSchema(Schema):
    id = fields.Str()
    podcastId = fields.Str(required=True)
    title = fields.Str(required=True)  # Ensure title is required
    description = fields.Str(required=True)  # Ensure description is required
    publishDate = fields.DateTime(required=True)  # Ensure publishDate is required
    duration = fields.Int(allow_none=True)  # Change to integer
    status = fields.Str(allow_none=True)
    recordingAt = fields.DateTime()
    createdAt = fields.DateTime()
    updatedAt = fields.DateTime()
    audioUrl = fields.Str(allow_none=True)  # Change from URL to Str
    fileSize = fields.Str(allow_none=True)
    fileType = fields.Str(allow_none=True)
    guid = fields.Str(allow_none=True)
    season = fields.Int(allow_none=True)
    episode = fields.Int(allow_none=True)
    episodeType = fields.Str(
        required=True, validate=validate.OneOf(["Full", "Trailer", "Bonus"])
    )  # Add episodeType with validation
    explicit = fields.Bool(required=True)  # Explicit content flag is required
    imageUrl = fields.Url(required=True)  # Ensure image URL is required
    episodeFiles = fields.List(
        fields.Dict(keys=fields.Str(), values=fields.Raw()), required=False
    )  # Make episodeFiles optional
    category = fields.Str(required=True)  # Add category field

    # New fields
    keywords = fields.List(fields.Str(), allow_none=True)
    chapters = fields.List(fields.Dict(), allow_none=True)
    link = fields.Url(allow_none=True)
    subtitle = fields.Str(allow_none=True)
    summary = fields.Str(allow_none=True)
    author = fields.Str(required=True)  # Ensure author is required
    isHidden = fields.Bool(allow_none=True)
    highlights = fields.List(fields.Str(), allow_none=True)  # New field for highlights
