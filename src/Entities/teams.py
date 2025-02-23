from marshmallow import Schema, fields

class TeamSchema(Schema):
    id = fields.Str()
    name = fields.Str(required=True)
    role = fields.List(fields.Str()) #owner role 
    email = fields.Email()
    phone = fields.Str()
    isActive = fields.Bool()
    joinedAt = fields.DateTime()
    lastActive = fields.DateTime()
