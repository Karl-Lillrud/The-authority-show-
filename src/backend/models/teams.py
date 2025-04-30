from marshmallow import Schema, fields


class MemberSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True)
    email = fields.Email(required=True)


class TeamSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    ownerId = fields.Str(required=True)
    ownerEmail = fields.Email(required=True)
    members = fields.List(
        fields.Nested(MemberSchema), 
        load_default=[] # Use load_default if you need an empty list when the field is missing during loading
    ) 
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)
