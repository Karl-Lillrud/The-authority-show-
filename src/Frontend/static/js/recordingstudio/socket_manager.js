// src/Frontend/static/js/recordingstudio/socket_manager.js
import { showNotification } from '../components/notifications.js';
import { updateRecordingTime } from './recording_manager.js';

export function initializeSocket({
    socket,
    room,
    episodeId,
    guestId,
    isHost,
    domElements,
    connectedUsers,
    greenroomUsers,
    peerConnections,
    localStream,
    updateParticipantsList,
    showJoinRequest,
    addParticipantStream,
    updateIndicators,
    updateLocalControls,
    fetchGuestsByEpisode
}) {
    const leaveTimeouts = new Map();

    socket.on('connect', () => {
        console.log('Socket.IO connected:', socket.id);
        showNotification('Connected to server', 'success');
        socket.emit('log_connection', { userId: guestId || 'host', socketId: socket.id, role: isHost ? 'host' : 'guest' });
    });

    socket.on('reconnect_attempt', (attempt) => {
        console.log(`Socket.IO reconnect attempt: ${attempt}`);
        showNotification(`Reconnecting to server (attempt ${attempt})`, 'info');
    });

    socket.on('connect_error', () => {
        console.error('Socket.IO connection error');
        showNotification('Failed to connect to server.', 'error');
    });

    socket.on('studio_joined', async (data) => {
        console.log('Joined studio room:', data);
        try {
            const guests = await fetchGuestsByEpisode(episodeId);
            updateParticipantsList(guests, domElements, connectedUsers, greenroomUsers);
        } catch (error) {
            showNotification('Error: Failed to load guests.', 'error');
        }
    });

    socket.on('participant_left', async (data) => {
        console.log('Participant left:', data);
        if (leaveTimeouts.has(data.userId)) {
            clearTimeout(leaveTimeouts.get(data.userId));
        }
        leaveTimeouts.set(data.userId, setTimeout(async () => {
            leaveTimeouts.delete(data.userId);
            connectedUsers = connectedUsers.filter(u => u.userId !== data.userId);
            const pc = peerConnections.get(data.userId);
            if (pc) {
                pc.close();
                peerConnections.delete(data.userId);
            }
            domElements.remoteVideoWrapper.style.display = 'none';
            domElements.remoteVideo.srcObject = null;
            try {
                const guests = await fetchGuestsByEpisode(episodeId);
                updateParticipantsList(guests, domElements, connectedUsers, greenroomUsers);
            } catch (error) {
                showNotification('Error: Failed to load guests.', 'error');
            }
        }, 3000));
    });

    socket.on('participant_joined', async (data) => {
        console.log('Participant joined:', data);
        if (leaveTimeouts.has(data.userId)) {
            clearTimeout(leaveTimeouts.get(data.userId));
            leaveTimeouts.delete(data.userId);
        }
        if (connectedUsers.some(u => u.userId === data.userId)) {
            connectedUsers = connectedUsers.map(u => u.userId === data.userId ? { ...u, streamId: data.streamId, guestName: data.guestName } : u);
        } else {
            connectedUsers.push({ userId: data.userId, streamId: data.streamId, guestName: data.guestName });
        }
        greenroomUsers = greenroomUsers.filter(u => u.userId !== data.userId);
        addParticipantStream(data.userId, data.streamId, data.guestName, localStream, domElements, connectedUsers, peerConnections, socket, room);
        try {
            const guests = await fetchGuestsByEpisode(episodeId);
            updateParticipantsList(guests, domElements, connectedUsers, greenroomUsers);
        } catch (error) {
            showNotification('Error: Failed to load guests.', 'error');
        }
        domElements.remoteVideoWrapper.style.display = 'block';
    });

    socket.on('join_studio_approved', (data) => {
        console.log('Join studio approved:', data);
        socket.emit('join_studio', {
            room: data.room,
            episodeId: data.episodeId,
            user: { id: guestId, name: data.guestName || 'Guest' },
            isHost: false
        });
        domElements.remoteVideoWrapper.style.display = 'block';
    });

    socket.on('request_join_studio', (data) => {
        if (isHost) {
            showJoinRequest(data.guestId, data.guestName, data.episodeId, data.roomId || data.room || data.episodeId, domElements, socket, greenroomUsers, async () => {
                try {
                    const guests = await fetchGuestsByEpisode(episodeId);
                    updateParticipantsList(guests, domElements, connectedUsers, greenroomUsers);
                } catch (error) {
                    showNotification('Error: Failed to load guests.', 'error');
                }
            });
        }
    });

    socket.on('recording_started', (data) => {
        console.log('Recording started:', data);
        updateRecordingTime(domElements, true, false, data.recordingStartTime || Date.now());
        if (!isHost) {
            showNotification('Recording started by host.', 'success');
            domElements.pauseButton.disabled = true;
            domElements.stopRecordingBtn.disabled = true;
            domElements.saveRecordingBtn.disabled = true;
            domElements.discardRecordingBtn.disabled = true;
        }
    });

    socket.on('recording_paused', (data) => {
        console.log('Recording pause state changed:', data);
        updateRecordingTime(domElements, true, data.isPaused);
        showNotification(data.isPaused ? 'Recording paused by host' : 'Recording resumed by host.', 'success');
    });

    socket.on('recording_stopped', (data) => {
        console.log('Recording stopped by host:', data);
        updateRecordingTime(domElements, false, false);
        showNotification('Recording stopped by host.', 'success');
        if (!isHost) {
            domElements.pauseButton.disabled = true;
            domElements.stopRecordingBtn.disabled = true;
            domElements.saveRecordingBtn.disabled = true;
            domElements.discardRecordingBtn.disabled = true;
        }
    });

    socket.on('error', (data) => {
        console.error('Server error:', data);
        showNotification(`Error: ${data.message}`, 'error');
    });

    return () => {
        socket.off('connect');
        socket.off('reconnect_attempt');
        socket.off('connect_error');
        socket.off('studio_joined');
        socket.off('participant_left');
        socket.off('participant_joined');
        socket.off('join_studio_approved');
        socket.off('request_join_studio');
        socket.off('recording_started');
        socket.off('recording_paused');
        socket.off('recording_stopped');
        socket.off('error');
        leaveTimeouts.forEach(timeout => clearTimeout(timeout));
        leaveTimeouts.clear();
    };
}