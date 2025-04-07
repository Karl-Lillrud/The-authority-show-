from marshmallow import Schema, fields

class UserSchema(Schema):
    id = fields.Str() 
    email = fields.Email(required=True)
    passwordHash = fields.Str(required=True, load_only=True)  # Never send password to frontend
    fullName = fields.Str(allow_none=True)
    phone = fields.Str(allow_none=True)
    createdAt = fields.DateTime()
    referralCode = fields.Str()
    referredBy = fields.Str(allow_none=True)
    googleRefresh = fields.Str(allow_none=True)  # Store the real Google Calendar refresh token
