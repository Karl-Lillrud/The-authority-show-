from datetime import datetime
from pydantic import BaseModel, Field

class UserToTeam(BaseModel):  # If a large podcast account with multiple users,
    id: str = Field(default=None)  # then one user can be a part of multiple teams
    userId: str  # and one team can have multiple users
    teamId: str
    role: str  # Role of the user in the team
    assignedAt: datetime = Field(default_factory=datetime.utcnow)