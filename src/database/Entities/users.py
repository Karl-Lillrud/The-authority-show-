from marshmallow import Schema, fields


class UserSchema(Schema):
    id = fields.Str()  # Many users belong to one account
    name = fields.Str()
    email = fields.Email(required=True)
    passwordHash = fields.Str(
        required=True, load_only=True
    )  # Never send password to frontend
    createdAt = fields.DateTime()
    referralCode = fields.Str()
    referredBy = fields.Str(allow_none=True)
