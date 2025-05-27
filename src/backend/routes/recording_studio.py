from flask import Blueprint, render_template, session, g, redirect, url_for, request, jsonify
from flask_socketio import join_room, leave_room, emit, SocketIO
from datetime import datetime, timedelta, timezone
import logging

from backend.database.mongo_connection import database
from backend.services.recording_studio_service import recording_studio_service

recording_studio_bp = Blueprint("recording_studio_bp", __name__)

# MongoDB collections
invitations_collection = database.GuestInvitations
episodes_collection = database.Episodes
guests_collection = database.Guests

# Configure logger
logger = logging.getLogger(__name__)

# Store active studio participants
studio_participants = {}  # {room: [{userId, socketId, name, isHost}]}

# Helper function to check if a client is the host
def is_host(room, socket_id):
    return any(p['isHost'] and p['socketId'] == socket_id for p in studio_participants.get(room, []))

# Validate invitation
def validate_invitation(episode_id, guest_id, token):
    query = {
        "episode_id": episode_id,
        "guest_id": guest_id,
        "invite_token": token,
        "status": "pending",
        "expires_at": {"$gte": datetime.now(timezone.utc)}
    }
    invitation = invitations_collection.find_one(query)
    if invitation:
        logger.info(f"Valid invitation found: episode_id={episode_id}, guest_id={guest_id}")
        return True
    logger.warning(f"Invalid invitation: episode_id={episode_id}, guest_id={guest_id}")
    return False

# ---------------------------------------------
# 🔌 REGISTER SOCKET.IO EVENTS
# ---------------------------------------------
def register_socketio_events(socketio: SocketIO):
    @socketio.on('connect')
    def handle_connect():
        logger.info(f"Client connected: {request.sid}")
        emit('connected', {'message': 'Connected to server'})

    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info(f"Client disconnected: {request.sid}")
        for room in studio_participants:
            participant = next((p for p in studio_participants[room] if p['socketId'] == request.sid), None)
            if participant:
                studio_participants[room] = [p for p in studio_participants[room] if p['socketId'] != request.sid]
                leave_room(room)
                emit('participant_left', {'userId': participant['userId']}, room=room)
                logger.info(f"User {participant['userId']} disconnected from studio: {room}")
                if not studio_participants[room]:
                    del studio_participants[room]  # Clean up empty room
                break

    @socketio.on('join_studio')
    def handle_join_studio(data):
        room = data.get('room')
        episodeId = data.get('episodeId')
        isHost = data.get('isHost', False)
        user = data.get('user', {})
        user_id = user.get('id')
        name = user.get('name', 'Guest')

        if not all([room, episodeId, user_id]):
            logger.error(f"Invalid join_studio data: {data}")
            emit('error', {'error': 'missing_fields', 'message': 'Room, episodeId, and user ID required'}, to=request.sid)
            return

        if room != episodeId:
            logger.error(f"Validation failed: Room {room} does not match episodeId {episodeId}")
            emit('error', {'error': 'invalid_room', 'message': 'Room must match episodeId'}, to=request.sid)
            return

        # Validate episode exists
        episode = episodes_collection.find_one({"_id": episodeId})
        if not episode:
            logger.error(f"Episode not found: {episodeId}")
            emit('error', {'error': 'episode_not_found', 'message': 'Episode not found'}, to=request.sid)
            return

        # Validate guest invitation if not host
        if not isHost:
            token = data.get('token')
            if not token or not validate_invitation(episodeId, user_id, token):
                logger.error(f"Invalid invitation for guest {user_id} in episode {episodeId}")
                emit('error', {'error': 'invalid_invitation', 'message': 'Invalid or expired invitation'}, to=request.sid)
                return

        join_room(room)
        logger.info(f"{'Host' if isHost else 'Guest'} {user_id} joined studio: {room}, Episode: {episodeId}")

        # Add or update participant
        if room not in studio_participants:
            studio_participants[room] = []
        existing = next((p for p in studio_participants[room] if p['userId'] == user_id), None)
        if existing:
            existing.update({'socketId': request.sid, 'name': name, 'isHost': isHost})
        else:
            studio_participants[room].append({
                'userId': user_id,
                'socketId': request.sid,
                'name': name,
                'isHost': isHost
            })

        emit('studio_joined', {'room': room, 'episodeId': episodeId, 'isHost': isHost}, room=room)
        emit('participant_joined', {
            'userId': user_id,
            'streamId': f"stream-{user_id}",
            'guestName': name
        }, room=room)

    @socketio.on('request_join_studio')
    def handle_request_join_studio(data):
        room = data.get('room')
        episode_id = data.get('episodeId')
        guest_id = data.get('guestId')
        guest_name = data.get('guestName', 'Guest')
        token = data.get('token')

        logger.info(f"Received request_join_studio: room={room}, episode_id={episode_id}, guest_id={guest_id}")

        if not all([room, episode_id, guest_id, token]):
            logger.error("Validation failed: Missing required fields")
            emit('error', {'error': 'missing_fields', 'message': 'Missing required fields'}, to=request.sid)
            return

        if room != episode_id:
            logger.error(f"Validation failed: Room {room} does not match episodeId {episode_id}")
            emit('error', {'error': 'invalid_room', 'message': 'Room must match episodeId'}, to=request.sid)
            return

        if not validate_invitation(episode_id, guest_id, token):
            logger.error(f"Validation failed: Invalid invitation for episode_id={episode_id}, guest_id={guest_id}")
            emit('error', {'error': 'invalid_invitation', 'message': 'Invalid or expired invitation'}, to=request.sid)
            return

        if room in studio_participants:
            host = next((p for p in studio_participants[room] if p['isHost']), None)
            if host:
                emit('request_join_studio', {
                    'guestId': guest_id,
                    'guestName': guest_name,
                    'episodeId': episode_id,
                    'room': room
                }, to=host['socketId'])
                logger.info(f"Forwarded join request to host: {host['socketId']}")
            else:
                logger.error(f"No host found in studio room: {room}")
                emit('error', {'error': 'no_host', 'message': 'No host in studio'}, to=request.sid)
        else:
            logger.error(f"Studio room not found: {room}")
            emit('error', {'error': 'room_not_found', 'message': 'Studio room not found'}, to=request.sid)

    @socketio.on('approve_join_studio')
    def handle_approve_join_studio(data):
        guest_id = data.get('guestId')
        episode_id = data.get('episodeId')
        room = data.get('room')

        if not all([guest_id, episode_id, room]):
            logger.error(f"Invalid approve_join_studio data: {data}")
            emit('error', {'error': 'missing_fields', 'message': 'Guest ID, episode ID, and room required'}, to=request.sid)
            return

        if room != episode_id:
            logger.error(f"Validation failed: Room {room} does not match episodeId {episode_id}")
            emit('error', {'error': 'invalid_room', 'message': 'Room must match episodeId'}, to=request.sid)
            return

        if not is_host(room, request.sid):
            logger.error(f"Unauthorized approve_join_studio attempt by {request.sid}")
            emit('error', {'error': 'unauthorized', 'message': 'Only host can approve join requests'}, to=request.sid)
            return

        greenroom_users = recording_studio_service.get_users_in_greenroom(room)  # Fixed method name
        guest = next((u for u in greenroom_users if u['id'] == guest_id), None)
        if not guest:
            logger.error(f"Guest {guest_id} not found in greenroom: {room}")
            emit('error', {'error': 'guest_not_found', 'message': 'Guest not in greenroom'}, to=request.sid)
            return

        # Remove from greenroom first
        recording_studio_service.leave_greenroom(room, {'id': guest_id})

        # Add to studio participants
        if room not in studio_participants:
            studio_participants[room] = []
        studio_participants[room].append({
            'userId': guest_id,
            'socketId': guest['socketId'],
            'name': guest.get('name', 'Guest'),
            'isHost': False
        })

        logger.info(f"Approved join for Guest {guest_id}: {room}, Episode {episode_id}")
        emit('join_studio_approved', {
            'room': room,
            'episodeId': episode_id,
            'guestId': guest_id
        }, to=guest['socketId'])

    @socketio.on('deny_join_studio')
    def handle_deny_join_studio(data):
        guest_id = data.get('guestId')
        reason = data.get('reason', 'Denied by host')
        room = data.get('room')

        if not all([guest_id, room]):
            logger.error(f"Invalid deny_join_studio data: {data}")
            emit('error', {'error': 'missing_fields', 'message': 'Guest ID and room required'}, to=request.sid)
            return

        if not is_host(room, request.sid):
            logger.error(f"Unauthorized deny_join_studio attempt by {request.sid}")
            emit('error', {'error': 'unauthorized', 'message': 'Only host can deny join requests'}, to=request.sid)
            return

        greenroom_users = recording_studio_service.get_greenroom_users(room)
        guest = next((u for u in greenroom_users if u['id'] == guest_id), None)
        if guest:
            logger.info(f"Denied join for Guest {guest_id}: {reason}")
            emit('join_studio_denied', {'reason': reason}, to=guest['socketId'])
        else:
            logger.warning(f"Guest {guest_id} not found for deny: {room}")
            emit('error', {'error': 'guest_not_found', 'message': 'Guest not in greenroom'}, to=request.sid)

    @socketio.on('join_greenroom')
    def handle_join_greenroom(data):
        room = data.get('room')
        user = data.get('user')
        token = data.get('token')
        if not all([room, user, user.get('id'), token]):
            logger.error(f"Invalid join_greenroom data: {data}")
            emit('error', {'error': 'missing_fields', 'message': 'Room, user ID, and token required'}, to=request.sid)
            return

        if not validate_invitation(room, user['id'], token):
            logger.error(f"Invalid invitation for guest {user['id']} in room {room}")
            emit('error', {'error': 'invalid_invitation', 'message': 'Invalid or expired invitation'}, to=request.sid)
            return

        join_room(room)
        users = recording_studio_service.join_greenroom(room, user)
        logger.info(f"Guest {user['id']} joined greenroom: {room}")
        emit('greenroom_joined', {'room': room, 'users': users}, room=room)
        emit('participant_update', {'users': users}, room=room)

    @socketio.on('participant_stream')
    def handle_participant_stream(data):
        room = data.get('room')
        userId = data.get('userId')
        streamId = data.get('streamId')
        guestName = data.get('guestName', 'Guest')
        if not all([room, userId, streamId]):
            logger.error(f"Invalid participant_stream data: {data}")
            emit('error', {'error': 'missing_fields', 'message': 'Room, userId, and streamId required'}, to=request.sid)
            return
        logger.info(f"Participant stream: userId={userId}, room={room}")
        emit('participant_stream', {
            'userId': userId,
            'streamId': streamId,
            'guestName': guestName
        }, room=room)

    @socketio.on('host_ready')
    def handle_host_ready(data):
        room = data.get('room')
        user = data.get('user')
        if not room:
            logger.error(f"Invalid host_ready data: {data}")
            emit('error', {'error': 'missing_fields', 'message': 'Room required'}, to=request.sid)
            return

        if not is_host(room, request.sid):
            logger.error(f"Unauthorized host_ready attempt by {request.sid}")
            emit('error', {'error': 'unauthorized', 'message': 'Only host can signal ready'}, to=request.sid)
            return

        logger.info(f"Host ready: {room}")
        emit('host_ready', {'room': room, 'user': user}, room=room)

    @socketio.on('recording_started')
    def handle_recording_started(data):
        room = data.get('room')
        user = data.get('user')
        if not room:
            logger.error(f"Invalid recording_started data: {data}")
            emit('error', {'error': 'missing_fields', 'message': 'Room required'}, to=request.sid)
            return

        if not is_host(room, request.sid):
            logger.error(f"Unauthorized recording_started attempt by {request.sid}")
            emit('error', {'error': 'unauthorized', 'message': 'Only host can start recording'}, to=request.sid)
            return

        logger.info(f"Recording started: {room}")
        emit('recording_started', {'room': room, 'user': user}, room=room)

    @socketio.on('recording_stopped')
    def handle_recording_stopped(data):
        room = data.get('room')
        user = data.get('user')
        if not room:
            logger.error(f"Invalid recording_stopped data: {data}")
            emit('error', {'error': 'missing_fields', 'message': 'Room required'}, to=request.sid)
            return

        if not is_host(room, request.sid):
            logger.error(f"Unauthorized recording_stopped attempt by {request.sid}")
            emit('error', {'error': 'unauthorized', 'message': 'Only host can stop recording'}, to=request.sid)
            return

        logger.info(f"Recording stopped: {room}")
        emit('recording_stopped', {'room': room, 'user': user}, room=room)

# ---------------------------------------------
# ROUTES
# ---------------------------------------------

@recording_studio_bp.route('/recording/metadata', methods=['POST'])
def log_recording_metadata():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        episode_id = data.get("episode_id")
        file_url = data.get("file_url")
        size = data.get("file_size")
        duration = data.get("duration")

        if not all([user_id, episode_id, file_url, size, duration]):
            logger.error(f"Missing required fields for metadata: {data}")
            return jsonify({"error": "Missing required fields"}), 400

        update_fields = {
            "audioUrl": file_url,
            "fileSize": size,
            "duration": duration,
            "updated_at": datetime.now(timezone.utc)
        }

        result = episodes_collection.update_one({"_id": episode_id}, {"$set": update_fields})
        if result.matched_count == 0:
            logger.error(f"Episode not found: {episode_id}")
            return jsonify({"error": "Episode not found"}), 404

        logger.info(f"Recording metadata updated for episode: {episode_id}")
        return jsonify({"message": "Recording metadata updated successfully"}), 200
    except Exception as e:
        logger.error(f"Error logging metadata: {str(e)}")
        return jsonify({"error": str(e)}), 500

@recording_studio_bp.route('/participants/<episode_id>', methods=['GET'])
def get_participants(episode_id):
    try:
        episode = episodes_collection.find_one({"_id": episode_id}, {"userid": 1})
        if not episode:
            logger.error(f"Episode not found: {episode_id}")
            return jsonify({"error": "Episode not found"}), 404

        guests = list(guests_collection.find({"episode_id": episode_id}, {"_id": 1}))
        participants = {
            "host": episode["userid"],
            "guests": [str(guest["_id"]) for guest in guests]
        }
        logger.info(f"Retrieved participants for episode: {episode_id}")
        return jsonify(participants), 200
    except Exception as e:
        logger.error(f"Error retrieving participants: {str(e)}")
        return jsonify({"error": str(e)}), 500

@recording_studio_bp.route('/verify_invite/<invite_token>', methods=['GET'])
def verify_invite(invite_token):
    try:
        invitation = invitations_collection.find_one({
            "invite_token": invite_token,
            "status": "pending",
            "expires_at": {"$gte": datetime.now(timezone.utc)}
        })
        if not invitation:
            logger.error(f"Invalid or expired invitation token")
            return jsonify({"error": "Invalid or expired invitation token"}), 404

        join_url = url_for("recording_studio_bp.recording_studio", _external=True, token=invite_token)
        logger.info(f"Valid invitation token for episode_id={invitation['episode_id']}")
        return jsonify({
            "message": "Invitation token is valid",
            "episode_id": invitation["episode_id"],
            "join_url": join_url
        }), 200
    except Exception as e:
        logger.error(f"Error verifying invite: {str(e)}")
        return jsonify({"error": str(e)}), 500

@recording_studio_bp.route('/studio')
def recording_studio():
    room = request.args.get('room')
    episode_id = request.args.get('episodeId')
    if not room:
        logger.warning(f"Missing room parameter for studio, using episodeId: {episode_id}")
        room = episode_id
    if not episode_id or room != episode_id:
        logger.error(f"Invalid studio parameters: room={room}, episodeId={episode_id}")
        return jsonify({"error": "Room must match episodeId"}), 400
    return render_template('recordingstudio/recording_studio.html')

@recording_studio_bp.route('/greenroom', methods=['GET'])
def greenroom():
    guest_id = request.args.get("guestId")
    token = request.args.get("token")
    episode_id = request.args.get("episodeId")
    room = request.args.get("room")

    if not all([guest_id, episode_id, room, token]):
        logger.error(f"Missing greenroom parameters: guestId={guest_id}, episodeId={episode_id}, room={room}")
        return jsonify({"error": "Missing required parameters"}), 400

    if room != episode_id:
        logger.error(f"Validation failed: Room {room} does not match episodeId {episode_id}")
        return jsonify({"error": "Room must match episodeId"}), 400

    if not validate_invitation(episode_id, guest_id, token):
        logger.error(f"Invalid invitation for episode_id={episode_id}, guest_id={guest_id}")
        return jsonify({"error": "Invalid or expired invitation"}), 403

    logger.info(f"Rendering greenroom: guestId={guest_id}, episodeId={episode_id}, room={room}")
    return render_template("greenroom/greenroom.html", guestId=guest_id, token=token, episodeId=episode_id, room=room)