from marshmallow import Schema, fields

class GuestSchema(Schema):
    id = fields.Str()
    podcastId = fields.Str(required=False) #Guest should be linked to a podcast
    name = fields.Str(required=True)
    image = fields.Str()
    tags = fields.List(fields.Str())
    description = fields.Str()
    bio = fields.Str()
    email = fields.Email()
    linkedin = fields.Str()
    twitter = fields.Str()
    areasOfInterest = fields.List(fields.Str())
    status = fields.Str()
    scheduled = fields.Int() #Schedule sen
    completed = fields.Int()
    createdAt = fields.DateTime() #Endpoints will fix this
    notes = fields.Str()
