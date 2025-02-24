from marshmallow import Schema, fields


class EpisodeSchema(Schema):
    id = fields.Str()
    guestId = fields.Str(required=True)  # Reference to the guest
    podcastId = fields.Str(required=True)
    title = fields.Str(required=True)
    description = fields.Str()
    publishDate = fields.DateTime()
    duration = fields.Int()
    status = fields.Str()
    createdAt = fields.DateTime()
    updatedAt = fields.DateTime()
