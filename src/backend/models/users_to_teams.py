from datetime import datetime
from marshmallow import Schema, fields
 
class UserToTeamSchema(Schema): # If a large podcast account with multiple users,
    id = fields.Str()           # then one user can be a part of multiple teams
    userId = fields.Str()       # and one team can have multiple users
    teamId = fields.Str()
    role = fields.Str()        # Role of the user in the team
    assignedAt = fields.DateTime(load_default=datetime.utcnow)