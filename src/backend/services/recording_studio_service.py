from asyncio.log import logger
from typing import Dict, List
from datetime import datetime

class RecordingStudioService:
    def __init__(self):
        self.rooms: Dict[str, List[dict]] = {}
        self.greenrooms: Dict[str, List[dict]] = {}

    def join_room(self, room: str, user: dict) -> List[dict]:
        if room not in self.rooms:
            self.rooms[room] = []
        
        # Check if user already exists in room
        existing_user = next((u for u in self.rooms[room] if u.get('id') == user.get('id')), None)
        if existing_user:
            existing_user.update(user)
        else:
            self.rooms[room].append(user)
        
        return self.rooms[room]

    def leave_room(self, room: str, user: dict) -> List[dict]:
        print(f"Leaving room {room}: user={user}")
        if room in self.rooms:
            before_count = len(self.rooms[room])
            self.rooms[room] = [u for u in self.rooms[room] if u.get('id') != user.get('id')]
            after_count = len(self.rooms[room])
            print(f"Users before: {before_count}, after: {after_count}")
            if not self.rooms[room]:
                print(f"Room {room} is empty, deleting room")
                del self.rooms[room]
        else:
            print(f"Room {room} not found")
        return self.rooms.get(room, [])

    def get_users_in_room(self, room: str) -> List[dict]:
        return self.rooms.get(room, [])

    def join_greenroom(self, room: str, user: dict) -> List[dict]:
        logger.info(f"Adding user {user.get('id')} to greenroom: {room}")
        if room not in self.greenrooms:
            self.greenrooms[room] = []
        
        existing_user = next((u for u in self.greenrooms[room] if u.get('id') == user.get('id')), None)
        if existing_user:
            existing_user.update(user)
            logger.info(f"Updated existing user {user.get('id')} in greenroom: {room}")
        else:
            self.greenrooms[room].append(user)
            logger.info(f"Added new user {user.get('id')} to greenroom: {room}")
        
        return self.greenrooms[room]

    def leave_greenroom(self, room: str, user: dict) -> List[dict]:
        logger.info(f"Removing user {user.get('id')} from greenroom: {room}")
        if room in self.greenrooms:
            self.greenrooms[room] = [u for u in self.greenrooms[room] if u.get('id') != user.get('id')]
            if not self.greenrooms[room]:
                logger.info(f"Greenroom {room} is empty, deleting")
                del self.greenrooms[room]
        else:
            logger.warning(f"Greenroom {room} not found")
        return self.greenrooms.get(room, [])

    def get_users_in_greenroom(self, room: str) -> List[dict]:
        return self.greenrooms.get(room, [])

    def update_user_status(self, room: str, user_id: str, is_ready: bool) -> List[dict]:
        if room in self.greenrooms:
            for user in self.greenrooms[room]:
                if user.get('id') == user_id:
                    user['isReady'] = is_ready
                    break
        return self.greenrooms.get(room, [])

    def is_host_ready(self, room: str) -> bool:
        if room in self.greenrooms:
            host = next((u for u in self.greenrooms[room] if u.get('isHost')), None)
            return host.get('isReady', False) if host else False
        return False

    def can_move_to_studio(self, room: str) -> bool:
        if room in self.greenrooms:
            # Check if host is ready and all participants are ready
            host = next((u for u in self.greenrooms[room] if u.get('isHost')), None)
            if not host or not host.get('isReady'):
                return False
            
            # Check if all participants are ready
            return all(u.get('isReady', False) for u in self.greenrooms[room] if not u.get('isHost'))
        return False

recording_studio_service = RecordingStudioService()
