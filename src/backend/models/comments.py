from marshmallow import Schema, fields

class CommentSchema(Schema):
    id = fields.Str()
    podtaskId = fields.Str(allow_none=True)  # Link to the podtask
    userId = fields.Str(allow_none=True)     # User who created the comment
    userName = fields.Str()                # Name of the user who created the comment
    text = fields.Str(required=True)       # Comment content
    createdAt = fields.DateTime()          # When the comment was created
    updatedAt = fields.DateTime(allow_none=True)  # When the comment was last updated
