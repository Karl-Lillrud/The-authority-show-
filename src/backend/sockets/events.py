from flask_socketio import emit, join_room, leave_room
from backend import socketio

# --- Guest client events ---
@socketio.on('guest_join')
def handle_guest_join(data):
    room = data.get('room')
    guest_id = data.get('guest_id')
    join_room(room)
    emit('guest_joined', {'room': room, 'guest_id': guest_id}, room=room)

@socketio.on('guest_leave')
def handle_guest_leave(data):
    room = data.get('room')
    guest_id = data.get('guest_id')
    leave_room(room)
    emit('guest_left', {'room': room, 'guest_id': guest_id}, room=room)

# --- User client events ---
@socketio.on('user_join')
def handle_user_join(data):
    room = data.get('room')
    user_id = data.get('user_id')
    join_room(room)
    emit('user_joined', {'room': room, 'user_id': user_id}, room=room)

@socketio.on('user_leave')
def handle_user_leave(data):
    room = data.get('room')
    user_id = data.get('user_id')
    leave_room(room)
    emit('user_left', {'room': room, 'user_id': user_id}, room=room)

# --- Common status events ---
@socketio.on('status_update')
def handle_status_update(data):
    room = data.get('room')
    status = data.get('status')
    sender = data.get('sender')
    emit('status_update', {'room': room, 'status': status, 'sender': sender}, room=room)

@socketio.on('crash_recovery')
def handle_crash_recovery(data):
    room = data.get('room')
    user = data.get('user')
    reason = data.get('reason')
    emit('crash_recovery', {'room': room, 'user': user, 'reason': reason}, room=room)

@socketio.on('recording_status')
def handle_recording_status(data):
    room = data.get('room')
    user = data.get('user')
    status = data.get('status')  
    emit('recording_status', {'room': room, 'user': user, 'status': status}, room=room)