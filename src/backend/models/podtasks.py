from marshmallow import Schema, fields

class PodtaskSchema(Schema):
    id = fields.Str()

    # Optional podcast, episode, team, and members
    podcastId = fields.Str(allow_none=True)    # Optional for general tasks
    episodeId = fields.Str(allow_none=True)    # Optional
    teamId = fields.Str(allow_none=True)       # Optional
    members = fields.List(fields.Str(), allow_none=True)  # Optional list of user IDs

    name = fields.Str(required=True)
    action = fields.List(fields.Str())
    dayCount = fields.Int()
    description = fields.Str()
    actionUrl = fields.Url(allow_none=True)
    urlDescribe = fields.Str()
    submissionReq = fields.Bool()
    status = fields.Str()
    assignedAt = fields.DateTime()
    dueDate = fields.DateTime()
    priority = fields.Str()
