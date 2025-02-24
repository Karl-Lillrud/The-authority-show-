from marshmallow import Schema, fields


class CreditsSchema(Schema):
    id = fields.Str()
    availableCredits = fields.Int()
    usedCredits = fields.Int()
    lastUpdated = fields.DateTime()
    creditsHistory = fields.List(fields.Dict(keys=fields.Str(), values=fields.Raw()))
    creditLimit = fields.Int()
