from marshmallow import Schema, fields

# No required fields for the moment.
class WorkflowSchema(Schema):
    _id = fields.Str(required=False)  # Optional: Auto-generated or system-defined
    user_id = fields.Str(required=True)  # Required: To associate the workflow with a user
    episode_id = fields.Str(required=True)  # Required: To associate the workflow with an episode
    tasks = fields.List(fields.Dict(), required=True)  # Required: To define the tasks in the workflow
    created_at = fields.DateTime(required=True)  # Required: To track the creation time
    name = fields.Str(required=True)  # Required: Name of the workflow
    description = fields.Str(required=False)  # Optional: Additional description of the workflow
