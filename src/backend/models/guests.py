from marshmallow import Schema, fields
from backend.models.podtasks import PodtaskSchema

class SocialMediaSchema(Schema):
    """Schema for social media links"""
    linkedin = fields.Str(required=False)
    twitter = fields.Str(required=False)
    instagram = fields.Str(required=False)
    tiktok = fields.Str(required=False)
    facebook = fields.Str(required=False)
    whatsapp = fields.Str(required=False)

class RecommendedGuestSchema(Schema):
    """Schema for recommended guests"""
    name = fields.Str(required=False)
    email = fields.Str(required=False)
    reason = fields.Str(required=False)

class GuestSchema(Schema):
    id = fields.Str(required=True)  # Required: Unique identifier
    episodeId = fields.Str(required=False)
    name = fields.Str(required=True)
    image = fields.Str(required=False)  # Optional: Image of the guest
    description = fields.Str(required=False)  # Optional: Description of the guest
    bio = fields.Str(required=False)  # Optional: Biography of the guest
    email = fields.Email(required=True)  # Required: Email of the guest
    company = fields.Str(required=False)  # Optional: Company of the guest
    phone = fields.Str(required=False)  # Optional: Phone number
    areasOfInterest = fields.List(fields.Str(), required=False)  # Optional: Areas of interest
    status = fields.Str(required=False)  # Optional: Status (e.g., active, inactive)
    scheduled = fields.Int(required=False)  # Optional: Scheduled date/time
    completed = fields.Int(required=False)  # Optional: Completion status
    created_at = fields.DateTime(required=True)  # Required: Timestamp of creation
    user_id = fields.Str(required=True)  # Required: Associated user
    calendarEventId = fields.Str(required=False)  # Optional: Associated calendar event ID
    futureOpportunities = fields.Bool(required=False)  # Optional: Future opportunities
    notes = fields.Str(required=False)  # Optional: Additional notes
    recommendedGuests = fields.List(fields.Nested(RecommendedGuestSchema), required=False)  # Optional: List of recommended guests
    socialmedia = fields.Nested(SocialMediaSchema, required=False)  # Optional: Social media links