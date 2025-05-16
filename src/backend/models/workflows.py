from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class Workflow(BaseModel):
    id: Optional[str] = None  # Changed from _id to id for Pydantic compatibility
    user_id: Optional[str] = None
    episode_id: Optional[str] = None
    tasks: Optional[List[Dict]] = []
    created_at: Optional[datetime] = None
    name: Optional[str] = None
    description: Optional[str] = None
