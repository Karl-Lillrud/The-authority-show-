from marshmallow import Schema, fields

class GuestSchema(Schema):
    id = fields.Str()
    podcastId = fields.Str(required=True)
    name = fields.Str(required=True)
    image = fields.Url()
    tags = fields.List(fields.Str())
    description = fields.Str()
    bio = fields.Str()
    email = fields.Email()
    linkedin = fields.Url()
    twitter = fields.Url()
    areasOfInterest = fields.List(fields.Str())
    status = fields.Str()
    scheduled = fields.Int()
    completed = fields.Int()
    createdAt = fields.DateTime()
    notes = fields.Str()
