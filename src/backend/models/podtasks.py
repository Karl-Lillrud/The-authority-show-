from marshmallow import Schema, fields

class PodtaskSchema(Schema):
    id = fields.Str()

    # Optional podcast, episode, team, and members, guestId. "Team can make a task for a team and"
    #members can be assigned to a task towards episode or podcast, guest.
    podcastId = fields.Str(allow_none=True)    # Optional 
    episodeId = fields.Str(allow_none=True)    # Optional
    teamId = fields.Str(allow_none=True)       # Optional
    members = fields.List(fields.Str(), allow_none=True)  # Optional list of user IDs
    guestId = fields.Str(allow_none=True)      # Optional
    name = fields.Str(required=True)
    action = fields.List(fields.Str()) #should manly be manual until code or system for automation is in place
    dayCount = fields.Int()
    description = fields.Str()
    actionUrl = fields.Url(allow_none=True)
    urlDescribe = fields.Str()
    submissionReq = fields.Bool()
    status = fields.Str()
    assignedAt = fields.DateTime()
    dueDate = fields.DateTime()
    priority = fields.Str()
