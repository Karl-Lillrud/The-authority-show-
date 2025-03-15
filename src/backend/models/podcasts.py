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
    imageUrl = fields.Str(allow_none=True)  # Add imageUrl field
    googleCal = fields.String(allow_none=True)  # Allow null values
    guestUrl = fields.String(allow_none=True)  # Allow null values
    socialMedia = fields.List(
        fields.Dict(), allow_none=True
    )  # Changed to Dict for platform/url pairs
    email = fields.Email(allow_none=True)
    defaultTasks = fields.List(fields.Nested(PodtaskSchema), allow_none=True)
    description = fields.Str(allow_none=True)
    logoUrl = fields.Str(allow_none=True)  # Changed from fields.Url to fields.Str
    category = fields.Str(allow_none=True)
    podUrl = fields.Url(allow_none=True)
    author = fields.Str(allow_none=True)  # Added author field
    episodes = fields.List(fields.Dict(), allow_none=True)  # Added episodes field
