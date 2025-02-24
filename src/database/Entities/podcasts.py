from marshmallow import Schema, fields


class PodcastSchema(Schema):
    id = fields.Str()
    teamId = fields.Str()
    accountId = fields.Str(required=True)
    podName = fields.Str(required=True)
    ownerName = fields.Str()
    hostName = fields.Str()
    rssFeed = fields.Url()
    googleCal = fields.Url()
    podUrl = fields.Url()
    guestUrl = fields.Url()
    socialMedia = fields.List(fields.Url())
    email = fields.Email()
    description = fields.Str()
    logoUrl = fields.Url()
    category = fields.Str()
    defaultTasks = fields.List(fields.Str())
