from marshmallow import Schema, fields

class ClipsSchema(Schema):
    id = fields.Str(required=False)  # Optional: Auto-generated unique identifier
    episodeId = fields.Str(required=True)  # Required: Each clip should be tied to an episode
    clipName = fields.Str(required=True)  # Required: Name of the clip
    duration = fields.Int(required=False)  # Optional: Duration of the clip (if applicable)
    createdAt = fields.DateTime(required=True)  # Required: Timestamp when the clip was created
    editedBy = fields.List(fields.Str(), required=False)  # Optional: List of editors who modified the clip
    clipUrl = fields.Url(required=False)  # Optional: URL for the clip if uploaded
    status = fields.Str(required=False)  # Optional: Status of the clip (e.g., "active", "inactive")
    tags = fields.List(fields.Str(), required=False)  # Optional: Tags associated with the clip
