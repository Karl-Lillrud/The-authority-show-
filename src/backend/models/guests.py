from marshmallow import Schema, fields
from backend.models.podtasks import PodtaskSchema

class GuestSchema(Schema):
    id = fields.Str()
    episodeId = fields.Str(required=False)
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
    defaultTasks = fields.List(fields.Nested(PodtaskSchema), allow_none=True)
    notes = fields.Str()
