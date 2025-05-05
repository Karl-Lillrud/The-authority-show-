from marshmallow import Schema, fields

class UserSchema(Schema):
    id = fields.Str() 
    email = fields.Email(required=True)
    fullName = fields.Str(allow_none=True)
    phone = fields.Str(allow_none=True)
    createdAt = fields.DateTime()
    referralCode = fields.Str()
    referredBy = fields.Str(allow_none=True)

class User:
    googleCal: str  # Store the publicly shareable calendar link
    googleCalRefreshToken: str  # Store the Google Calendar refresh token
    googleCal: str  # Store the publicly shareable calendar link
