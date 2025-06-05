from marshmallow import Schema, fields

class EditSchema(Schema):
    id = fields.Str()
    episodeId = fields.Str(required=True)
    userId = fields.Str(required=True)
    editType = fields.Str(required=True)
    clipName = fields.Str()
    duration = fields.Int()
    createdAt = fields.DateTime()
    clipUrl = fields.Url(required=True)
    status = fields.Str()
    tags = fields.List(fields.Str())
    transcript = fields.Str()
    sentiment = fields.Dict()
    metadata = fields.Dict()
    emotion = fields.Dict()
    voiceMap = fields.Dict(
        keys=fields.Str(),  # Talare, t.ex. "Speaker 1"
        values=fields.Str()  # Röst-ID, t.ex. "voice_id_123"
    )