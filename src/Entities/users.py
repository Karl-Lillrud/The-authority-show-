from marshmallow import Schema, fields

class UserSchema(Schema):
    id = fields.Str()
    accountId = fields.Str()
    name = fields.Str()
    email = fields.Email(required=True)
    passwordHash = fields.Str(required=True, load_only=True) # Never send password to frontend
    createdAt = fields.DateTime()
    referralCode = fields.Str()
    referredBy = fields.Str(allow_none=True)
    
