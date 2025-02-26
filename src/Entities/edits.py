from marshmallow import Schema, fields

class ClipsSchema(Schema):
    id = fields.Str()
    podcastId = fields.Str(required=True) #Clip should be linked to a podcast
    clipName = fields.Str(required=True)
    duration = fields.Int()
    createdAt = fields.DateTime()
    editedBy = fields.List(fields.Str())
    clipUrl = fields.Url()
    status = fields.Str()
    tags = fields.List(fields.Str())
