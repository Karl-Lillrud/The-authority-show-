from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

class Podtask(BaseModel):
    id: Optional[str] = None

    podcastId: Optional[str] = None
    episodeId: Optional[str] = None
    teamId: Optional[str] = None
    members: Optional[List[str]] = None
    guestId: Optional[str] = None

    name: str  # required
    action: List[str]
    dayCount: Optional[int] = None
    description: Optional[str] = None
    actionUrl: Optional[HttpUrl] = None
    urlDescribe: Optional[str] = None
    submissionReq: Optional[bool] = None
    status: Optional[str] = None
    assignedAt: Optional[datetime] = None

    # Extra fields
    dueDate: Optional[str] = None
    assignee: Optional[str] = None
    assigneeName: Optional[str] = None
    dependencies: Optional[List[str]] = None
    aiTool: Optional[str] = None
    priority: Optional[str] = None
