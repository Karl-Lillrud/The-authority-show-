import datetime
from flask import Blueprint, request
from flask_socketio import join_room, leave_room, emit, SocketIO
import logging
from backend.database.mongo_connection import database
from backend.services.recording_studio_service import recording_studio_service
from backend.routes.recording_studio import validate_invitation

recording_studio_bp = Blueprint("recording_studio_bp", __name__)

# MongoDB collections
invitations_collection = database.GuestInvitations
episodes_collection = database.Episodes
guests_collection = database.Guests

# Configure logger
logger = logging.getLogger(__name__)

# Store active studio participants
studio_participants = {}  

def is_host(room, socket_id):
    return any(p.get('isHost') and p.get('socketId') == socket_id for p in studio_participants.get(room, []))

def get_participant_by_socket(room, socket_id):
    return next((p for p in studio_participants.get(room, []) if p['socketId'] == socket_id), None)

def get_participant_by_user_id(room, user_id):
    return next((p for p in studio_participants.get(room, []) if p['userId'] == user_id), None)

def get_other_participants(room, exclude_user_id):
    return [p for p in studio_participants.get(room, []) if p['userId'] != exclude_user_id]

def register_socketio_events(socketio: SocketIO):
    @socketio.on('connect')
    def handle_connect():
        logger.info(f"Client connected: {request.sid}")
        emit('connected', {'message': 'Connected to server'})

    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info(f"Client disconnected: {request.sid}")
        for room in list(studio_participants.keys()):
            participant = next((p for p in studio_participants[room] if p['socketId'] == request.sid), None)
            if participant:
                # Check if user is in greenroom or recently joined studio
                greenroom_users = recording_studio_service.get_users_in_greenroom(room)
                if any(u['id'] == participant['userId'] for u in greenroom_users):
                    logger.info(f"User {participant['userId']} is in greenroom, skipping participant_left")
                    continue
                # Allow a grace period for studio transitions
                if 'joinTime' in participant and (datetime.datetime.now() - participant['joinTime']).total_seconds() < 5:
                    logger.info(f"User {participant['userId']} recently joined studio, skipping participant_left")
                    continue
                
                # Notify other participants about disconnection
                emit('participant_left', {
                    'userId': participant['userId'],
                    'streamId': f"stream-{participant['userId']}"
                }, room=room)
                
                # Remove from studio participants
                studio_participants[room] = [p for p in studio_participants[room] if p['socketId'] != request.sid]
                leave_room(room)
                
                logger.info(f"User {participant['userId']} disconnected from studio: {room}")
                if not studio_participants[room]:
                    del studio_participants[room]
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

        episode = episodes_collection.find_one({"_id": episodeId})
        if not episode:
            logger.error(f"Episode not found: {episodeId}")
            emit('error', {'error': 'episode_not_found', 'message': 'Episode not found'}, to=request.sid)
            return

        if not isHost:
            token = data.get('token')
            if not token or not validate_invitation(episodeId, user_id, token):
                logger.error(f"Invalid invitation for guest {user_id} in episode {episodeId}")
                emit('error', {'error': 'invalid_invitation', 'message': 'Invalid or expired invitation'}, to=request.sid)
                return

        join_room(room)
        logger.info(f"{'Host' if isHost else 'Guest'} {user_id} joined studio: {room}, Episode: {episodeId}")

        if room not in studio_participants:
            studio_participants[room] = []
        
        existing = next((p for p in studio_participants[room] if p['userId'] == user_id), None)
        is_new_participant = not existing
        
        if existing:
            existing.update({'socketId': request.sid, 'name': name, 'isHost': isHost, 'joinTime': datetime.datetime.now()})
            logger.info(f"Updated existing participant {user_id} in studio: {room}")
        else:
            studio_participants[room].append({
                'userId': user_id,
                'socketId': request.sid,
                'name': name,
                'isHost': isHost,
                'joinTime': datetime.datetime.now()
            })
            logger.info(f"Added new participant {user_id} to studio: {room}")

        # Send current participants list to the joining user
        current_participants = [
            {
                'userId': p['userId'],
                'streamId': f"stream-{p['userId']}",
                'guestName': p['name'],
                'isHost': p['isHost']
            } 
            for p in studio_participants[room] if p['userId'] != user_id
        ]
        
        emit('studio_joined', {
            'room': room, 
            'episodeId': episodeId, 
            'isHost': isHost,
            'participants': current_participants
        }, to=request.sid)

        # Only emit participant_joined for new participants
        if is_new_participant:
            emit('participant_joined', {
                'userId': user_id,
                'streamId': f"stream-{user_id}",
                'guestName': name,
                'isHost': isHost
            }, room=room)
            
            # Initiate WebRTC connections with existing participants
            other_participants = get_other_participants(room, user_id)
            if other_participants:
                logger.info(f"Initiating WebRTC connections for {user_id} with {len(other_participants)} participants")
                emit('initiate_webrtc_connections', {
                    'participants': [
                        {
                            'userId': p['userId'],
                            'socketId': p['socketId'],
                            'name': p['name'],
                            'isHost': p['isHost']
                        } 
                        for p in other_participants
                    ]
                }, to=request.sid)

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

        # Add guest to greenroom with name
        recording_studio_service.join_greenroom(room, {'id': guest_id, 'socketId': request.sid, 'name': guest_name})

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

        greenroom_users = recording_studio_service.get_users_in_greenroom(room)
        guest = next((u for u in greenroom_users if u['id'] == guest_id), None)
        if not guest:
            logger.error(f"Guest {guest_id} not found in greenroom: {room}")
            emit('error', {'error': 'guest_not_found', 'message': 'Guest not in greenroom'}, to=request.sid)
            return

        # Add to studio first
        if room not in studio_participants:
            studio_participants[room] = []
        existing = next((p for p in studio_participants[room] if p['userId'] == guest_id), None)
        if not existing:
            studio_participants[room].append({
                'userId': guest_id,
                'socketId': guest['socketId'],
                'name': guest.get('name', 'Guest'),
                'isHost': False,
                'joinTime': datetime.datetime.now()
            })

        # Then remove from greenroom
        recording_studio_service.leave_greenroom(room, {'id': guest_id})

        logger.info(f"Approved join for Guest {guest_id}: {room}, Episode {episode_id}")

        # Get current participants for the approved guest
        current_participants = [
            {
                'userId': p['userId'],
                'streamId': f"stream-{p['userId']}",
                'guestName': p['name'],
                'isHost': p['isHost']
            } 
            for p in studio_participants[room] if p['userId'] != guest_id
        ]

        emit('join_studio_approved', {
            'room': room,
            'episodeId': episode_id,
            'guestId': guest_id,
            'guestName': guest.get('name', 'Guest'),
            'participants': current_participants
        }, to=guest['socketId'])

        # Log participant_joined emission
        logger.info(f"Emitting participant_joined for guest {guest_id} with name {guest.get('name', 'Guest')}")
        emit('participant_joined', {
            'userId': guest_id,
            'streamId': f"stream-{guest_id}",
            'guestName': guest.get('name', 'Guest'),
            'isHost': False
        }, room=room)

        return {'success': True, 'message': f'Guest {guest_id} approved'}

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

    @socketio.on('log_connection')
    def handle_log_connection(data):
        logger.info(f"Client connection: userId={data.get('userId')}, socketId={data.get('socketId')}, role={data.get('role')}")
        
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

    # WebRTC Signaling Events - Fixed for targeted communication
    @socketio.on('offer')
    def handle_offer(data):
        room = data.get('room')
        target_user_id = data.get('targetUserId')
        from_user_id = data.get('fromUserId')
        offer = data.get('offer')

        if not all([room, target_user_id, from_user_id, offer]):
            logger.error(f"Invalid offer data: {data}")
            emit('error', {'error': 'missing_fields', 'message': 'Room, targetUserId, fromUserId, and offer required'}, to=request.sid)
            return

        target_participant = get_participant_by_user_id(room, target_user_id)
        if not target_participant:
            logger.error(f"Target participant {target_user_id} not found in room {room}")
            emit('error', {'error': 'participant_not_found', 'message': 'Target participant not found'}, to=request.sid)
            return

        logger.info(f"Forwarding WebRTC offer from {from_user_id} to {target_user_id} in room {room}")
        emit('offer', {
            'fromUserId': from_user_id,
            'targetUserId': target_user_id,
            'offer': offer,
            'room': room
        }, to=target_participant['socketId'])

    @socketio.on('answer')
    def handle_answer(data):
        room = data.get('room')
        target_user_id = data.get('targetUserId')
        from_user_id = data.get('fromUserId')
        answer = data.get('answer')

        if not all([room, target_user_id, from_user_id, answer]):
            logger.error(f"Invalid answer data: {data}")
            emit('error', {'error': 'missing_fields', 'message': 'Room, targetUserId, fromUserId, and answer required'}, to=request.sid)
            return

        target_participant = get_participant_by_user_id(room, target_user_id)
        if not target_participant:
            logger.error(f"Target participant {target_user_id} not found in room {room}")
            emit('error', {'error': 'participant_not_found', 'message': 'Target participant not found'}, to=request.sid)
            return

        logger.info(f"Forwarding WebRTC answer from {from_user_id} to {target_user_id} in room {room}")
        emit('answer', {
            'fromUserId': from_user_id,
            'targetUserId': target_user_id,
            'answer': answer,
            'room': room
        }, to=target_participant['socketId'])

    @socketio.on('ice_candidate')
    def handle_ice_candidate(data):
        room = data.get('room')
        target_user_id = data.get('targetUserId')
        from_user_id = data.get('fromUserId')
        candidate = data.get('candidate')

        if not all([room, target_user_id, from_user_id, candidate]):
            logger.error(f"Invalid ICE candidate data: {data}")
            emit('error', {'error': 'missing_fields', 'message': 'Room, targetUserId, fromUserId, and candidate required'}, to=request.sid)
            return

        target_participant = get_participant_by_user_id(room, target_user_id)
        if not target_participant:
            logger.error(f"Target participant {target_user_id} not found in room {room}")
            emit('error', {'error': 'participant_not_found', 'message': 'Target participant not found'}, to=request.sid)
            return

        logger.info(f"Forwarding ICE candidate from {from_user_id} to {target_user_id} in room {room}")
        emit('ice_candidate', {
            'fromUserId': from_user_id,
            'targetUserId': target_user_id,
            'candidate': candidate,
            'room': room
        }, to=target_participant['socketId'])

    @socketio.on('participant_stream')
    def handle_participant_stream(data):
        room = data.get('room')
        userId = data.get('userId')
        streamId = data.get('streamId')
        guestName = data.get('guestName', 'Guest')
        stream_type = data.get('streamType', 'camera')  # camera, screen, audio
        
        if not all([room, userId, streamId]):
            logger.error(f"Invalid participant_stream data: {data}")
            emit('error', {'error': 'missing_fields', 'message': 'Room, userId, and streamId required'}, to=request.sid)
            return
        
        logger.info(f"Participant stream update: userId={userId}, room={room}, type={stream_type}")
        emit('participant_stream', {
            'userId': userId,
            'streamId': streamId,
            'guestName': guestName,
            'streamType': stream_type
        }, room=room)

    @socketio.on('stream_ready')
    def handle_stream_ready(data):
        room = data.get('room')
        user_id = data.get('userId')
        stream_id = data.get('streamId')
        
        if not all([room, user_id, stream_id]):
            logger.error(f"Invalid stream_ready data: {data}")
            emit('error', {'error': 'missing_fields', 'message': 'Room, userId, and streamId required'}, to=request.sid)
            return
        
        logger.info(f"Stream ready: userId={user_id}, room={room}")
        emit('stream_ready', {
            'userId': user_id,
            'streamId': stream_id
        }, room=room)

    @socketio.on('request_stream')
    def handle_request_stream(data):
        room = data.get('room')
        requester_id = data.get('requesterId')
        target_id = data.get('targetId')
        
        if not all([room, requester_id, target_id]):
            logger.error(f"Invalid request_stream data: {data}")
            emit('error', {'error': 'missing_fields', 'message': 'Room, requesterId, and targetId required'}, to=request.sid)
            return
        
        target_participant = get_participant_by_user_id(room, target_id)
        if not target_participant:
            logger.error(f"Target participant {target_id} not found in room {room}")
            emit('error', {'error': 'participant_not_found', 'message': 'Target participant not found'}, to=request.sid)
            return
        
        logger.info(f"Stream requested by {requester_id} from {target_id} in room {room}")
        emit('stream_requested', {
            'requesterId': requester_id,
            'targetId': target_id,
            'room': room
        }, to=target_participant['socketId'])

    @socketio.on('update_stream_state')
    def handle_update_stream_state(data):
        room = data.get('room')
        user_id = data.get('userId')
        video_enabled = data.get('videoEnabled')
        audio_enabled = data.get('audioEnabled')
        
        if not all([room, user_id]) or video_enabled is None or audio_enabled is None:
            logger.error(f"Invalid update_stream_state data: {data}")
            emit('error', {'error': 'missing_fields', 'message': 'Room, userId, videoEnabled, and audioEnabled required'}, to=request.sid)
            return
        
        logger.info(f"Stream state update: userId={user_id}, video={video_enabled}, audio={audio_enabled}")
        emit('update_stream_state', {
            'userId': user_id,
            'videoEnabled': video_enabled,
            'audioEnabled': audio_enabled
        }, room=room)

    @socketio.on('host_ready')
    def handle_host_ready(data):
        room = data.get('room')
        user = data.get('user')
        if not room:
            logger.error(f"Invalid host_ready data: {data}")
            emit('error', {'error': 'missing_fields', 'message': 'Room required'}, to=request.sid)
            return
        emit('host_ready', {'room': room, 'user': user}, room=room)

    # Recording Events
    @socketio.on('recording_started')
    def handle_recording_started(data):
        room = data.get('room')
        user_id = data.get('user', {}).get('id')

        if not room or not user_id:
            emit('error', {'error': 'missing_fields', 'message': 'Room and user ID required'}, to=request.sid)
            return

        if not is_host(room, request.sid):
            emit('error', {'error': 'unauthorized', 'message': 'Only host can start recording'}, to=request.sid)
            return

        logger.info(f"Recording started by host {user_id} in room {room}")
        emit('recording_started', {'startedBy': user_id}, room=room)

    @socketio.on('recording_stopped')
    def handle_recording_stopped(data):
        room = data.get('room')
        user_id = data.get('user', {}).get('id')

        if not room or not user_id:
            emit('error', {'error': 'missing_fields', 'message': 'Room and user ID required'}, to=request.sid)
            return

        if not is_host(room, request.sid):
            emit('error', {'error': 'unauthorized', 'message': 'Only host can stop recording'}, to=request.sid)
            return

        logger.info(f"Recording stopped by host {user_id} in room {room}")
        emit('recording_stopped', {'stoppedBy': user_id}, room=room)

    @socketio.on('recording_paused')
    def handle_recording_paused(data):
        room = data.get('room')
        is_paused = data.get('isPaused')
        user_id = data.get('user', {}).get('id')

        if not room or is_paused is None or not user_id:
            logger.error(f"Invalid recording_paused data: {data}")
            emit('error', {'error': 'missing_fields', 'message': 'Room, isPaused, and user ID required'}, to=request.sid)
            return

        if not is_host(room, request.sid):
            logger.error(f"Unauthorized recording_paused attempt by {request.sid}")
            emit('error', {'error': 'unauthorized', 'message': 'Only host can pause/resume recording'}, to=request.sid)
            return

        logger.info(f"Recording {'paused' if is_paused else 'resumed'} by host {user_id} in room {room}")
        emit('recording_paused', {'isPaused': is_paused, 'by': user_id}, room=room)

    @socketio.on('save_recording')
    def handle_save_recording(data):
        room = data.get('room')
        user_id = data.get('user', {}).get('id')

        if not room or not user_id:
            emit('error', {'error': 'missing_fields', 'message': 'Room and user ID required'}, to=request.sid)
            return

        if not is_host(room, request.sid):
            emit('error', {'error': 'unauthorized', 'message': 'Only host can save recording'}, to=request.sid)
            return

        logger.info(f"Recording save requested by host {user_id} in room {room}")
        emit('save_recording', {'requestedBy': user_id}, room=room)

    @socketio.on('discard_recording')
    def handle_discard_recording(data):
        room = data.get('room')
        user_id = data.get('user', {}).get('id')

        if not room or not user_id:
            emit('error', {'error': 'missing_fields', 'message': 'Room and user ID required'}, to=request.sid)
            return

        if not is_host(room, request.sid):
            emit('error', {'error': 'unauthorized', 'message': 'Only host can discard recording'}, to=request.sid)
            return

        logger.info(f"Recording discard requested by host {user_id} in room {room}")
        emit('discard_recording', {'requestedBy': user_id}, room=room)