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
    id = fields.Str()
    episodeId = fields.Str(required=False)
    name = fields.Str(required=True)
    image = fields.Str()
    description = fields.Str()
    bio = fields.Str()
    email = fields.Email()
    company = fields.Str()
    phone = fields.Str()  # Changed from Int to Str to handle phone formats
    areasOfInterest = fields.List(fields.Str())
    status = fields.Str()
    scheduled = fields.Int()
    completed = fields.Int()
    created_at = fields.DateTime()
    user_id = fields.Str()
    calendarEventId = fields.Str()
    futureOpportunities = fields.Bool()
    notes = fields.Str()
    recommendedGuests = fields.List(fields.Nested(RecommendedGuestSchema))
    socialmedia = fields.Nested(SocialMediaSchema)