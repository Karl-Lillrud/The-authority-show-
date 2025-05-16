from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
import uuid

class CreditHistoryEntry(BaseModel):
    """Pydantic model for a single entry in the credit history."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Changed from _id to id
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    type: str = Field(..., description="One of allowed types")
    amount: int  # Can be positive (grant/purchase) or negative (consumption/reset)
    description: str
    balance_after: Optional[Dict[str, int]] = None  # Optional: sub/user balance after tx

    @validator('type')
    def validate_type(cls, v):
        allowed = {
            "initial_sub", "initial_user", "purchase", "monthly_sub_grant",
            "consumption", "sub_reset", "user_reset", "adjustment"
        }
        if v not in allowed:
            raise ValueError(f"Invalid type: {v}")
        return v


class Credits(BaseModel):
    """Pydantic model for the main user credits document."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Changed from _id to id
    user_id: str
    subCredits: int = Field(default=0, ge=0)
    storeCredits: int = Field(default=0, ge=0)
    usedCredits: int = Field(default=0, ge=0)
    lastUpdated: datetime = Field(default_factory=datetime.utcnow)
    carryOverstoreCredits: bool = True
    lastSubResetMonth: Optional[int] = None  # Should be 1–12 if provided
    lastSubResetYear: Optional[int] = None
    creditsHistory: List[CreditHistoryEntry] = Field(default_factory=list)
