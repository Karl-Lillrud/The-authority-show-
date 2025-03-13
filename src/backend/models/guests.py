from marshmallow import Schema, fields
from models.podtasks import TaskSchema

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
    defaultTasks = fields.List(fields.Nested(TaskSchema), allow_none=True)
    notes = fields.Str()
