from marshmallow import Schema, fields

class ClipsSchema(Schema):
    id = fields.Str()
    episodeId = fields.Str(required=True)
    clipName = fields.Str(required=True)
    duration = fields.Int()
    createdAt = fields.DateTime()
    editedBy = fields.List(fields.Str())
    clipUrl = fields.Url()
    status = fields.Str()
    tags = fields.List(fields.Str())
