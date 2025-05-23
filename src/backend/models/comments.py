from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Comment(BaseModel):
    id: Optional[str] = None
    podtaskId: Optional[str] = None      # Link to the podtask
    userId: Optional[str] = None         # User who created the comment
    userName: str                        # Name of the user who created the comment
    text: str                            # Comment content (required)
    createdAt: datetime                  # When the comment was created
    updatedAt: Optional[datetime] = None # When the comment was last updated
