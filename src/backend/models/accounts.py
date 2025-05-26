from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class Account(BaseModel):
    id: Optional[str] = None
    ownerId: Optional[str] = None
    subscriptionId: Optional[str] = None
    creditId: Optional[str] = None
    email: EmailStr  # required
    isCompany: Optional[bool] = None
    companyName: Optional[str] = None
    paymentInfo: Optional[str] = None
    subscriptionStatus: Optional[str] = None
    createdAt: Optional[datetime] = None
    referralBonus: Optional[int] = None
    subscriptionStart: Optional[datetime] = None
    subscriptionEnd: Optional[datetime] = None
    isActive: bool  # required
    created_at: datetime  # required
    isFirstLogin: Optional[bool] = None
    unlockedExtraEpisodeSlots: Optional[int] = None
