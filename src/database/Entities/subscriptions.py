from marshmallow import Schema, fields


class SubscriptionSchema(Schema):  # This is one subscription
    id = fields.Str()  #
    subscriptionPlan = fields.Str()
    autoRenew = fields.Bool()
    discountCode = fields.Str()
