from marshmallow import Schema, fields


class EditsSchema(Schema):
    id = fields.Str()
    episodeId = fields.Str(required=True)
    editName = fields.Str(required=True)
    duration = fields.Int()
    createdAt = fields.DateTime()
    editedBy = fields.List(fields.Str())
    editUrl = fields.Url()
    status = fields.Str()
    tags = fields.List(fields.Str())
