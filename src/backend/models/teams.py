from marshmallow import Schema, fields


class TeamSchema(Schema):
    id = fields.Str()  # Team ID
    podcastId = fields.Str()  # Podcast ID associated with the team
    name = fields.Str(required=True)  # Team Name
    email = fields.Email()  # Contact email for the team
    description = fields.Str()  # Description of the team
    isActive = fields.Bool()  # Whether the team is active or not
    joinedAt = fields.DateTime()  # Date and time when the team was created
    lastActive = fields.DateTime()  # Last time the team was active or interacted with
    members = fields.List(
        fields.Dict(), load_default=[]
    )  # List of members (user data) for the team
