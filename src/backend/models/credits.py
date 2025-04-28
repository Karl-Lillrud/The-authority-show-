from marshmallow import Schema, fields, validate
from datetime import datetime
import uuid

class CreditHistoryEntrySchema(Schema):
    """Schema for a single entry in the credit history."""
    _id = fields.Str(load_default=lambda: str(uuid.uuid4()))
    timestamp = fields.DateTime(load_default=datetime.utcnow)
    type = fields.Str(required=True, validate=validate.OneOf(
        ["initial_sub", "initial_user", "purchase", "monthly_sub_grant", "consumption", "sub_reset", "user_reset", "adjustment"]
    ))
    amount = fields.Int(required=True) # Can be positive (grant/purchase) or negative (consumption/reset)
    description = fields.Str(required=True)
    balance_after = fields.Dict(keys=fields.Str(), values=fields.Int(), required=False) # Optional: store sub/user balance after tx

class CreditsSchema(Schema):
    """Schema for the main user credits document."""
    _id = fields.Str(load_default=lambda: str(uuid.uuid4()))
    user_id = fields.Str(required=True)
    subCredits = fields.Int(load_default=0, validate=validate.Range(min=0)) # Current month's Sub credits
    storeCredits = fields.Int(load_default=0, validate=validate.Range(min=0)) # Purchased credits
    # availableCredits is calculated, not stored
    usedCredits = fields.Int(load_default=0, validate=validate.Range(min=0)) # Lifetime used credits
    lastUpdated = fields.DateTime(load_default=datetime.utcnow) # Tracks last update, crucial for reset
    carryOverstoreCredits = fields.Bool(load_default=True) # Determines if storeCredits reset monthly
    lastSubResetMonth = fields.Int(allow_none=True) # Store the month (1-12) of the last subCredits reset
    lastSubResetYear = fields.Int(allow_none=True) # Store the year of the last subCredits reset
    creditsHistory = fields.List(fields.Nested(CreditHistoryEntrySchema), load_default=list)

    