from marshmallow import Schema, fields

class GuestsToEpisodes(Schema):
    id = fields.Str(required=True)  # Required feield
    episodeId = fields.Str(required=True) # Required feield
    guestId = fields.Str(required=True)  # Required feield
 
