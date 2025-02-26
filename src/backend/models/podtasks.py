from marshmallow import Schema, fields

class PodtaskSchema(Schema):
    id = fields.Str()
    podcastId = fields.Str() #not required if they wanna create general tasks for all podcasts
    name = fields.Str()      #Option is to select podcast to assign task to or not
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

