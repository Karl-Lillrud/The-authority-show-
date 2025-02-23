from marshmallow import Schema, fields

class AccountSchema(Schema): 
    id = fields.Str()
    userId = fields.Str()
    subscriptionId = fields.Str()
    creditId = fields.Str()
    email = fields.Email(required=True)
    isCompany = fields.Bool()
    companyName = fields.Str()
    paymentInfo = fields.Str()
    subscriptionStatus = fields.Str
    createdAt = fields.DateTime()
    referralBonus = fields.Int()
    subscriptionStart = fields.DateTime()
    subscriptionEnd = fields.DateTime()
    isActive = fields.Bool()