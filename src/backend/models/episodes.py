from marshmallow import Schema, fields, pre_load


class EpisodeSchema(Schema):
    id = fields.Str()
    podcastId = fields.Str(required=True)
    title = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    publishDate = fields.DateTime(allow_none=True)
    duration = fields.Int(allow_none=True)
    status = fields.Str(allow_none=True)
    createdAt = fields.DateTime()
    updatedAt = fields.DateTime()

    @pre_load
    def process_empty_strings(self, data, **kwargs):
        # Convert empty strings to None for fields that expect specific types
        for key in ["publishDate", "description", "duration", "status"]:
            if key in data and data[key] == "":
                data[key] = None
        return data
