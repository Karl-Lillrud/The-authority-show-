import logging
from typing import Dict, List
from threading import Lock

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class RecordingStudioService:
    def __init__(self):
        self.rooms: Dict[str, List[dict]] = {}
        self.greenrooms: Dict[str, List[dict]] = {}
        self.lock = Lock()

    def _find_user_by_id(self, user_list: List[dict], user_id: str) -> dict:
        return next((u for u in user_list if u.get('id') == user_id), None)

    def _get_host(self, room: str) -> dict | None:
        return next((u for u in self.greenrooms.get(room, []) if u.get('isHost')), None)

    def join_room(self, room: str, user: dict) -> List[dict]:
        with self.lock:
            if room not in self.rooms:
                self.rooms[room] = []

            existing_user = self._find_user_by_id(self.rooms[room], user.get('id'))
            if existing_user:
                existing_user.update(user)
            else:
                self.rooms[room].append(user)

            return self.rooms[room]

    def leave_room(self, room: str, user: dict) -> List[dict]:
        logger.info(f"Leaving room {room}: user={user}")
        with self.lock:
            if room in self.rooms:
                before_count = len(self.rooms[room])
                self.rooms[room] = [u for u in self.rooms[room] if u.get('id') != user.get('id')]
                after_count = len(self.rooms[room])
                logger.info(f"Users before: {before_count}, after: {after_count}")
                if not self.rooms[room]:
                    logger.info(f"Room {room} is empty, deleting room")
                    del self.rooms[room]
            else:
                logger.warning(f"Room {room} not found")
            return self.rooms.get(room, [])

    def get_users_in_room(self, room: str) -> List[dict]:
        return self.rooms.get(room, [])

    def join_greenroom(self, room: str, user: dict) -> List[dict]:
        logger.info(f"Adding user {user.get('id')} to greenroom: {room}")
        with self.lock:
            if room not in self.greenrooms:
                self.greenrooms[room] = []

            existing_user = self._find_user_by_id(self.greenrooms[room], user.get('id'))
            if existing_user:
                existing_user.update(user)
                logger.info(f"Updated existing user {user.get('id')} in greenroom: {room}")
            else:
                self.greenrooms[room].append(user)
                logger.info(f"Added new user {user.get('id')} to greenroom: {room}")

            return self.greenrooms[room]

    def leave_greenroom(self, room: str, user: dict) -> List[dict]:
        logger.info(f"Removing user {user.get('id')} from greenroom: {room}")
        with self.lock:
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
        with self.lock:
            if room in self.greenrooms:
                for user in self.greenrooms[room]:
                    if user.get('id') == user_id:
                        user['isReady'] = is_ready
                        break
            return self.greenrooms.get(room, [])

    def is_host_ready(self, room: str) -> bool:
        host = self._get_host(room)
        return host.get('isReady', False) if host else False

    def can_move_to_studio(self, room: str) -> bool:
        with self.lock:
            host = self._get_host(room)
            if not host or not host.get('isReady'):
                return False
            return all(u.get('isReady', False) for u in self.greenrooms.get(room, []) if not u.get('isHost'))

    def user_exists(self, room: str, user_id: str) -> bool:
        return self._find_user_by_id(self.rooms.get(room, []), user_id) is not None

    def get_all_rooms(self) -> List[str]:
        return list(self.rooms.keys())

    def get_all_greenrooms(self) -> List[str]:
        return list(self.greenrooms.keys())

recording_studio_service = RecordingStudioService()
