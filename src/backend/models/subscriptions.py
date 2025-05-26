from pydantic import BaseModel
from typing import Optional

class Subscription(BaseModel):
    id: Optional[str] = None
    subscriptionPlan: Optional[str] = None
    autoRenew: Optional[bool] = None
    discountCode: Optional[str] = None
