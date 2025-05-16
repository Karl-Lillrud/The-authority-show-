from pydantic import BaseModel
from typing import Optional

class GuestsToEpisodes(BaseModel):
    id: Optional[str] = None
    episodeId: str
    guestId: str
