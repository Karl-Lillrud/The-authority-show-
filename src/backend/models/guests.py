from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class SocialMedia(BaseModel):
    """Schema for social media links"""
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    instagram: Optional[str] = None
    tiktok: Optional[str] = None
    facebook: Optional[str] = None
    whatsapp: Optional[str] = None

class RecommendedGuest(BaseModel):
    """Schema for recommended guests"""
    name: Optional[str] = None
    email: Optional[str] = None
    reason: Optional[str] = None

class Guest(BaseModel):
    id: Optional[str] = None
    episodeId: Optional[str] = None
    name: str
    image: Optional[str] = None
    description: Optional[str] = None
    bio: Optional[str] = None
    email: Optional[EmailStr] = None
    company: Optional[str] = None
    phone: Optional[str] = None  # String to support formats like "+46 123 456 789"
    areasOfInterest: Optional[List[str]] = []
    status: Optional[str] = None
    scheduled: Optional[int] = None
    completed: Optional[int] = None
    created_at: Optional[datetime] = None
    user_id: Optional[str] = None
    calendarEventId: Optional[str] = None
    futureOpportunities: Optional[bool] = None
    notes: Optional[str] = None
    recommendedGuests: Optional[List[RecommendedGuest]] = []
    socialmedia: Optional[SocialMedia] = None
