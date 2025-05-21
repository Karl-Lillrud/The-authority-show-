from flask import Blueprint, request
from flask_socketio import join_room, leave_room, emit
from .. import socketio
from backend.services.recording_studio_service import recording_studio_service

recording_studio_bp = Blueprint('recording_studio', __name__)

# Socket.IO event: handle user connection
@socketio.on('connect')
def handle_connect():
    emit('connected', {'message': 'Connected to server'})

# Socket.IO event: join a room
@socketio.on('join_room')
def handle_join_room(data):
    room = data.get('room')
    user = data.get('user')
    join_room(room)
    users = recording_studio_service.join_room(room, user)
    emit('room_joined', {'room': room, 'user': user, 'users': users}, room=room)

# Socket.IO event: leave a room
@socketio.on('leave_room')
def handle_leave_room(data):
    room = data.get('room')
    user = data.get('user')
    leave_room(room)
    users = recording_studio_service.leave_room(room, user)
    emit('room_left', {'room': room, 'user': user, 'users': users}, room=room)

# Socket.IO event: get users in a room
@socketio.on('get_users_in_room')
def handle_get_users_in_room(data):
    room = data.get('room')
    users = recording_studio_service.get_users_in_room(room)
    emit('users_in_room', {'room': room, 'users': users})

# Optionally, handle disconnect
def handle_disconnect():
    emit('disconnected', {'message': 'Disconnected from server'})
socketio.on_event('disconnect', handle_disconnect)
