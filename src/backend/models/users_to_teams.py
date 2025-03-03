from datetime import datetime
from marshmallow import Schema, fields

class UserToTeamSchema(Schema):
    id = fields.Str()           
    userId = fields.Str()       
    teamId = fields.Str()
    role = fields.Str()        
    assignedAt = fields.DateTime(default=datetime.utcnow)
    status = fields.Str(default="pending")  # NEW: Tracks invite status ("pending", "accepted", "declined")
