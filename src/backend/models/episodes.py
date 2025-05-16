from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, List, Dict, Union
from datetime import datetime

class Episode(BaseModel):
    id: Optional[str] = Field(default=None)
    podcastId: str
    accountId: Optional[str] = None
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    summary: Optional[str] = None
    subtitle: Optional[str] = None
    publishDate: Optional[datetime] = None
    duration: Optional[int] = None
    audioUrl: Optional[HttpUrl] = None
    fileSize: Optional[int] = None
    fileType: Optional[str] = None
    guid: Optional[str] = None
    link: Optional[HttpUrl] = None
    imageUrl: Optional[HttpUrl] = None
    season: Optional[int] = None
    episode: Optional[int] = None
    episodeType: Optional[str] = None
    explicit: Optional[bool] = None
    author: Optional[str] = None
    keywords: Optional[List[str]] = None
    chapters: Optional[List[Dict]] = None
    status: Optional[str] = None
    isHidden: Optional[bool] = None
    recordingAt: Optional[datetime] = None
    isImported: Optional[bool] = None
    createdAt: Optional[datetime] = None  # dump_only
    updatedAt: Optional[datetime] = None  # dump_only
    highlights: Optional[List[str]] = None
    audioEdits: Optional[List[Dict]] = None

    @validator("duration")
    def validate_duration(cls, value):
        if value is not None and value < 0:
            raise ValueError("Duration cannot be negative.")
        return value

    @validator("publishDate")
    def validate_publish_date(cls, value):
        if value is not None and not isinstance(value, datetime):
            raise ValueError("publishDate must be a datetime object or null.")
        return value
