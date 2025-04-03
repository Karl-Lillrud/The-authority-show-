from marshmallow import Schema, fields
from datetime import datetime

class CreditsSchema(Schema):
    id = fields.Str()
    userId = fields.Str(required=True)
    availableCredits = fields.Int(default=0)
    usedCredits = fields.Int(default=0)
    creditLimit = fields.Int(default=3000)
    lastUpdated = fields.DateTime(default=datetime.utcnow)
    creditsHistory = fields.List(fields.Dict(), missing=[])
