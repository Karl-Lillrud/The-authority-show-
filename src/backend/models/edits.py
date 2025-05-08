from marshmallow import Schema, fields

class EditSchema(Schema):
    id = fields.Str()
    episodeId = fields.Str(required=True)
    userId = fields.Str(required=True)  # Vem som gjorde redigeringen
    editType = fields.Str(required=True)  # "enhance", "isolate", "ai_cut", etc.
    clipName = fields.Str()
    duration = fields.Int()
    createdAt = fields.DateTime()
    clipUrl = fields.Url(required=True)  # Azure blob URL
    status = fields.Str()  # t.ex. "done", "processing", "error"
    tags = fields.List(fields.Str())

    # Nya fält:
    transcript = fields.Str()  # transkription av klippet
    sentiment = fields.Dict()  # t.ex. {"positive": 0.9, "neutral": 0.1, "negative": 0.0}
    metadata = fields.Dict()  # Övrig data som {"filename": "...", "source": "..."}
    emotion = fields.Dict()  # Emotionell analys av klippet, t.ex. {"happy": 0.8, "sad": 0.1, "angry": 0.1}
