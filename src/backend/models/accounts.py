from marshmallow import Schema, fields

class AccountSchema(Schema): 
    id = fields.Str(required=False)  # Optional: Auto-generated unique identifier
    ownerId = fields.Str(required=False)  # Optional: Can be inferred from other fields
    subscriptionId = fields.Str(required=False)  # Optional: Only required if subscription is used
    creditId = fields.Str(required=False)  # Optional: Only relevant for accounts with credit features
    email = fields.Email(required=True)  # Required: Email is crucial for account identification
    isCompany = fields.Bool(required=False)  # Optional: If this account is for a company
    companyName = fields.Str(required=False)  # Optional: Company name (only if isCompany is True)
    paymentInfo = fields.Str(required=False)  # Optional: Only required if payment details are needed
    subscriptionStatus = fields.Str(required=False)  # Optional: Only required if tracking subscription status
    createdAt = fields.DateTime(required=False)  # Optional: Can be inferred from created_at
    referralBonus = fields.Int(required=False)  # Optional: Only if referral bonuses are in place
    subscriptionStart = fields.DateTime(required=False)  # Optional: Only if subscription tracking is required
    subscriptionEnd = fields.DateTime(required=False)  # Optional: Only if subscription tracking is required
    isActive = fields.Bool(required=True)  # Required: Indicates if the account is active
    created_at = fields.DateTime(required=True)  # Required: Timestamp of account creation
    isFirstLogin = fields.Bool(required=False)  # Optional: First login flag
    unlockedExtraEpisodeSlots = fields.Int(required=False)  # Optional: Additional episode slots
