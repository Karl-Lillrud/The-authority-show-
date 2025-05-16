from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class Member(BaseModel):
    id: Optional[str] = None  # dump_only -> Optional (not required on input)
    name: str
    email: EmailStr

class Team(BaseModel):
    id: Optional[str] = None  # dump_only -> Optional (not required on input)
    name: str
    description: Optional[str] = None
    ownerId: str
    ownerEmail: EmailStr
    members: List[Member] = []  # default empty list if missing
    createdAt: Optional[datetime] = None  # dump_only -> Optional
    updatedAt: Optional[datetime] = None  # dump_only -> Optional
