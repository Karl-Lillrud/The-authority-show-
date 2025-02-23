from marshmallow import Schema, fields

class PodtaskSchema(Schema):
    id = fields.Str()
    podcastId = fields.Str(required=True)
    name = fields.Str(required=True)
    action = fields.List(fields.Str())
    dayCount = fields.Int()
    description = fields.Str()
    actionUrl = fields.Url()
    urlDescribe = fields.Str()
    submissionReq = fields.Bool()
    status = fields.Str()
    assignedAt = fields.DateTime()
    dueDate = fields.DateTime()
    priority = fields.Str()

