from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict
from datetime import datetime

class Edit(BaseModel):
    id: Optional[str] = None
    episodeId: str
    userId: str  # Vem som gjorde redigeringen
    editType: str  # "enhance", "isolate", "ai_cut", etc.
    clipName: Optional[str] = None
    duration: Optional[int] = None
    createdAt: Optional[datetime] = None
    clipUrl: HttpUrl  # Azure blob URL
    status: Optional[str] = None  # t.ex. "done", "processing", "error"
    tags: List[str] = []

    # Nya fält:
    transcript: Optional[str] = None  # transkription av klippet
    sentiment: Optional[Dict[str, float]] = None  # t.ex. {"positive": 0.9, ...}
    metadata: Optional[Dict[str, str]] = None  # {"filename": "...", "source": "..."}
    emotion: Optional[Dict[str, float]] = None  # {"happy": 0.8, ...}
