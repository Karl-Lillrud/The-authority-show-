from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timezone

class Activity(BaseModel):
    id: Optional[str] = None
    userId: str  # required
    type: str  # required, e.g. "episode_created", "team_created"
    description: str  # required
    details: Optional[Dict[str, Any]] = None  # extra metadata like episodeId
    createdAt: datetime = datetime.now(timezone.utc)
