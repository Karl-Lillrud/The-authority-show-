# backend/models/activity.py
from marshmallow import Schema, fields
from datetime import datetime, timezone


class ActivitySchema(Schema):
    id = fields.Str()
    userId = fields.Str(required=True)  # logged in user
    type = fields.Str(required=True)  # T.ex. "episode_created", "team_created"
    description = fields.Str(required=True)  # T.ex. "Created episode 'Episode Title'"
    details = fields.Dict(allow_none=True)  # Extra metadata, t.ex. episodeId
    createdAt = fields.DateTime(default=datetime.now(timezone.utc))
