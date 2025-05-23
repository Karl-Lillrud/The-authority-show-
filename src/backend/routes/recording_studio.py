from flask import Blueprint, render_template, session, g, redirect, url_for, request, jsonify
from flask_socketio import join_room, leave_room, emit, SocketIO
from datetime import datetime
import logging

from backend.database.mongo_connection import database
from backend.services.invitation_service import InvitationService
from backend.services.recording_studio_service import recording_studio_service

recording_studio_bp = Blueprint("recording_studio_bp", __name__)

# MongoDB collections
invitations_collection = database.Invitations
episodes_collection = database.Episodes
guests_collection = database.Guests

# Configure logger
logger = logging.getLogger(__name__)

# ---------------------------------------------
# 🔌 REGISTER SOCKET.IO EVENTS
# ---------------------------------------------
def register_socketio_events(socketio: SocketIO):
    @socketio.on('connect')
    def handle_connect():
        emit('connected', {'message': 'Connected to server'})

    @socketio.on('disconnect')
    def handle_disconnect():
        emit('disconnected', {'message': 'Disconnected from server'})

    @socketio.on('join_room')
    def handle_join_room(data):
        room = data.get('room')
        user = data.get('user')
        join_room(room)
        users = recording_studio_service.join_room(room, user)
        emit('room_joined', {'room': room, 'user': user, 'users': users}, room=room)

    @socketio.on('leave_room')
    def handle_leave_room(data):
        room = data.get('room')
        user = data.get('user')
        leave_room(room)
        users = recording_studio_service.leave_room(room, user)
        emit('room_left', {'room': room, 'user': user, 'users': users}, room=room)

    @socketio.on('get_users_in_room')
    def handle_get_users_in_room(data):
        room = data.get('room')
        users = recording_studio_service.get_users_in_room(room)
        emit('users_in_room', {'room': room, 'users': users})

    @socketio.on('participant_ready')
    def handle_participant_ready(data):
        room = data.get('room')
        user = data.get('user')
        emit('participant_ready', {'room': room, 'user': user}, room=room)

    @socketio.on('recording_started')
    def handle_recording_started(data):
        room = data.get('room')
        user = data.get('user')
        emit('recording_started', {'room': room, 'user': user}, room=room)

    @socketio.on('recording_stopped')
    def handle_recording_stopped(data):
        room = data.get('room')
        user = data.get('user')
        emit('recording_stopped', {'room': room, 'user': user}, room=room)

    @socketio.on('join_greenroom')
    def handle_join_greenroom(data):
        room = data.get('room')
        user = data.get('user')
        join_room(room)
        users = recording_studio_service.join_greenroom(room, user)
        emit('greenroom_joined', {'room': room, 'user': user, 'users': users}, room=room)

    @socketio.on('leave_greenroom')
    def handle_leave_greenroom(data):
        room = data.get('room')
        user = data.get('user')
        leave_room(room)
        users = recording_studio_service.leave_greenroom(room, user)
        emit('greenroom_left', {'room': room, 'user': user, 'users': users}, room=room)

    @socketio.on('update_device_settings')
    def handle_update_device_settings(data):
        room = data.get('room')
        user = data.get('user')
        settings = data.get('settings')
        emit('device_settings_updated', {'room': room, 'user': user, 'settings': settings}, room=room)

    @socketio.on('host_ready')
    def handle_host_ready(data):
        room = data.get('room')
        user = data.get('user')
        emit('host_ready', {'room': room, 'user': user}, room=room)

    @socketio.on('move_to_studio')
    def handle_move_to_studio(data):
        room = data.get('room')
        user = data.get('user')
        emit('move_to_studio', {'room': room, 'user': user}, room=room)

# ---------------------------------------------
# ROUTES
# ---------------------------------------------

@recording_studio_bp.route('/invite', methods=['POST'])
def create_invitation():
    try:
        data = request.get_json()
        email = data.get("email")
        episode_id = data.get("episode_id")
        guest_id = data.get("guest_id")  # Include guest_id in the request

        if not all([email, episode_id, guest_id]):
            return jsonify({"error": "Email, episode_id, and guest_id are required"}), 400

        # Use the updated InvitationService to handle the invitation logic
        response, status_code = InvitationService.send_session_invitation(email, episode_id, guest_id)

        # Log the invitation details
        logger.info(f"Generated invite token: {response.get('token')}")
        logger.info(f"Greenroom URL: {response.get('greenroom_url')}")
        logger.info(f"Email sent to: {email}")

        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
            return jsonify({"error": "Missing required fields"}), 400

        update_fields = {
            "audioUrl": file_url,
            "fileSize": size,
            "duration": duration,
            "updated_at": datetime.utcnow()
        }

        result = episodes_collection.update_one({"_id": episode_id}, {"$set": update_fields})
        if result.matched_count == 0:
            return jsonify({"error": "Episode not found"}), 404

        return jsonify({"message": "Recording metadata updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@recording_studio_bp.route('/participants/<episode_id>', methods=['GET'])
def get_participants(episode_id):
    try:
        episode = episodes_collection.find_one({"_id": episode_id}, {"userid": 1})
        if not episode:
            return jsonify({"error": "Episode not found"}), 404

        guests = list(guests_collection.find({"episode_id": episode_id}, {"_id": 1}))

        participants = {
            "host": episode["userid"],
            "guests": [str(guest["_id"]) for guest in guests]
        }

        return jsonify(participants), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@recording_studio_bp.route('/verify_invite/<invite_token>', methods=['GET'])
def verify_invite(invite_token):
    try:
        invitation = invitations_collection.find_one({"invite_token": invite_token})
        if not invitation:
            return jsonify({"error": "Invalid invitation token"}), 404

        current_time = datetime.utcnow()
        if "expires_at" in invitation and current_time > invitation["expires_at"]:
            return jsonify({"error": "Invitation token has expired"}), 400

        join_url = url_for("recording_studio_bp.recording_studio", _external=True, token=invite_token)

        return jsonify({
            "message": "Invitation token is valid",
            "episode_id": invitation["episode_id"],
            "join_url": join_url
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@recording_studio_bp.route('/studio')
def recording_studio():
    return render_template('recordingstudio/recording_studio.html')

@recording_studio_bp.route('/greenroom', methods=['GET'])
def greenroom():
    """
    Render the greenroom page with guestId and token.
    """
    guest_id = request.args.get("guestId")
    token = request.args.get("token")
    return render_template('greenroom/greenroom.html', guestId=guest_id, token=token)
