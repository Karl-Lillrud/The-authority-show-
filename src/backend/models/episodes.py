from marshmallow import Schema, fields, pre_load, validate
from backend.models.podtasks import PodtaskSchema


class EpisodeSchema(Schema):
    id = fields.Str()
    podcastId = fields.Str(required=True)
    title = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    publishDate = fields.DateTime(required=True)  # Ensure publishDate is correctly defined
    duration = fields.Int(allow_none=True)  # Change to integer
    status = fields.Str(allow_none=True)
    defaultTasks = fields.List(fields.Nested(PodtaskSchema), allow_none=True)
    createdAt = fields.DateTime()
    updatedAt = fields.DateTime()
    audioUrl = fields.Str(allow_none=True)  # Change from URL to Str
    fileSize = fields.Str(allow_none=True)
    fileType = fields.Str(allow_none=True)
    guid = fields.Str(allow_none=True)
    season = fields.Int(allow_none=True)
    episode = fields.Int(allow_none=True)
    episodeType = fields.Str(allow_none=True)
    explicit = fields.Bool(allow_none=True)
    imageUrl = fields.Url(allow_none=True)
    episodeFiles = fields.List(fields.Dict(keys=fields.Str(), values=fields.Raw()), required=False)  # Make episodeFiles optional
    fileSize = fields.Str(allow_none=True)
    fileType = fields.Str(allow_none=True)
    guid = fields.Str(allow_none=True)
    season = fields.Int(allow_none=True)
    episode = fields.Int(allow_none=True)
    episodeType = fields.Str(allow_none=True)
    explicit = fields.Bool(allow_none=True)
    imageUrl = fields.Url(allow_none=True)
    episodeFiles = fields.List(fields.Dict(keys=fields.Str(), values=fields.Raw()))  # Correctly handle episodeFiles field

    # New fields
    keywords = fields.List(fields.Str(), allow_none=True)
    chapters = fields.List(fields.Dict(), allow_none=True)
    link = fields.Url(allow_none=True)
    subtitle = fields.Str(allow_none=True)
    summary = fields.Str(allow_none=True)
    author = fields.Str(allow_none=True)
    isHidden = fields.Bool(allow_none=True)

    @pre_load
    def process_empty_strings(self, data, **kwargs):
        # Convert empty strings to None for fields that expect specific types
        for key in [
            "publishDate",  # Ensure publishDate is correctly processed
            "description",
            "duration",
            "status",
            "audioUrl",
            "fileSize",
            "fileType",
            "guid",
            "season",
            "episode",
            "imageUrl",
            "link",
            "subtitle",
            "summary",
            "author",
        ]:
            if key in data and data[key] == "":
                data[key] = None
        return data
