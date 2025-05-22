# Service logic for room join/leave and user management (expand as needed)
class RecordingStudioService:
    def __init__(self):
        self.active_rooms = {}  # {room_id: set(user_ids)}

    def join_room(self, room, user):
        if room not in self.active_rooms:
            self.active_rooms[room] = set()
        self.active_rooms[room].add(user)
        return list(self.active_rooms[room])

    def leave_room(self, room, user):
        if room in self.active_rooms and user in self.active_rooms[room]:
            self.active_rooms[room].remove(user)
            if not self.active_rooms[room]:
                del self.active_rooms[room]
        return list(self.active_rooms.get(room, []))

    def get_users_in_room(self, room):
        return list(self.active_rooms.get(room, []))

recording_studio_service = RecordingStudioService()
