from marshmallow import Schema, fields

class SubscriptionSchema(Schema): # This is one subscription if more subscriptions are needed
    id = fields.Str()           # Anoter schema should be created
    subscriptionPlan = fields.Str()
    autoRenew = fields.Bool()
    discountCode = fields.Str()
