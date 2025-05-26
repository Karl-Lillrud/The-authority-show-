from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: Optional[str] = None
    email: EmailStr
    fullName: Optional[str] = None
    phone: Optional[str] = None
    createdAt: Optional[datetime] = None
    referralCode: Optional[str] = None
    referredBy: Optional[str] = None
    googleCal: Optional[str] = None  # Offentlig kalenderlänk
    googleCalRefreshToken: Optional[str] = None  # Google Calendar refresh token
