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
    defaultTasks = fields.List(fields.Nested(PodtaskSchema), allow_none=True)
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

        # Ensure defaultTasks is None if it's an empty list
        if "defaultTasks" in data and isinstance(data["defaultTasks"], list):
            if len(data["defaultTasks"]) == 0:
                data["defaultTasks"] = None
            else:
                # Save defaultTasks as regular tasks to episodes
                data["tasks"] = data["defaultTasks"]
                data["defaultTasks"] = None

        # Extract and edit key highlights from episode content
        if "description" in data and data["description"]:
            data["highlights"] = self.extract_highlights(data["description"])

        return data

    def extract_highlights(self, description):
        # Example logic to extract key highlights from the description
        highlights = []
        sentences = re.split(r'(?<=[.!?]) +', description)
        for sentence in sentences:
            if "important" in sentence.lower() or "key" in sentence.lower():
                highlights.append(sentence)
        return highlights