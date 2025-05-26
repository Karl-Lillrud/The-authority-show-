from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional, List, Dict

class Podcast(BaseModel):
    id: Optional[str] = None
    teamId: Optional[str] = None
    accountId: str  # Required
    podName: str  # Required

    ownerName: Optional[str] = None
    hostName: Optional[str] = None
    rssFeed: Optional[HttpUrl] = None
    googleCal: Optional[str] = None
    guestUrl: Optional[str] = None
    socialMedia: Optional[List[str]] = None
    email: Optional[EmailStr] = None
    description: Optional[str] = None
    logoUrl: Optional[str] = None
    category: Optional[str] = None
    podUrl: Optional[HttpUrl] = None
    title: Optional[str] = None
    language: Optional[str] = None
    author: Optional[str] = None
    copyright_info: Optional[str] = None
    imageUrl: Optional[str] = None
    podRss: Optional[str] = None
    generator: Optional[str] = None
    lastBuildDate: Optional[str] = None
    itunesType: Optional[str] = None
    link: Optional[str] = None
    itunesOwner: Optional[Dict] = None
    bannerUrl: Optional[str] = None
    tagline: Optional[str] = None
    hostBio: Optional[str] = None
    hostImage: Optional[str] = None
    isImported: Optional[bool] = False  # Default value
