from marshmallow import Schema, fields

class GuestsToEpisodes(Schema):
    id = fields.Str()
    episodeId = fields.Str()       
    guestId = fields.Str()
 
