from marshmallow import Schema, fields

# No required fields for the moment.
class WorkflowSchema(Schema):
    _id = fields.Str()
    user_id = fields.Str()
    episode_id = fields.Str()
    tasks = fields.List(fields.Dict())
    created_at = fields.DateTime()
    name = fields.Str()
    description = fields.Str()
