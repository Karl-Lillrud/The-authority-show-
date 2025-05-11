from marshmallow import Schema, fields
from backend.models.podtasks import PodtaskSchema


class PodcastSchema(Schema):
    id = fields.Str()
    teamId = fields.Str()
    accountId = fields.Str(required=True)  # Ensure account is provided
    podName = fields.Str(required=True)  # Podcast name must be required
    ownerName = fields.Str(allow_none=True)
    hostName = fields.Str(allow_none=True)
    rssFeed = fields.Url(allow_none=True)
    googleCal = fields.String(allow_none=True)  # Allow null values
    guestUrl = fields.String(allow_none=True)  # Allow null values
    socialMedia = fields.List(fields.String(), allow_none=True)
    email = fields.Email(allow_none=True)
    description = fields.Str(allow_none=True)
    logoUrl = fields.Str(allow_none=True)  # Changed from fields.Url to fields.Str
    category = fields.Str(allow_none=True)
    podUrl = fields.Url(allow_none=True)
    title = fields.Str(allow_none=True)  # Added field
    language = fields.Str(allow_none=True)  # Added field
    author = fields.Str(allow_none=True)  # Added field
    copyright_info = fields.Str(allow_none=True)  # Added field
    imageUrl = fields.Str(allow_none=True)  # Added field
    podRss = fields.Str(allow_none=True)  # Ensure this field is included
    generator = fields.Str(allow_none=True)  # Added field
    lastBuildDate = fields.Str(allow_none=True)  # Added field
    itunesType = fields.Str(allow_none=True)  # Added field
    link = fields.Str(allow_none=True)  # Added field
    itunesOwner = fields.Dict(allow_none=True)  # Added field
    bannerUrl = fields.Str(allow_none=True)  # Added field
    tagline = fields.Str(allow_none=True)  # Added field
    hostBio = fields.Str(allow_none=True)  # Added field
    hostImage = fields.Str(allow_none=True)  # Added field
    isImported = fields.Bool(allow_none=True, load_default=False)  # Added field, default to False
