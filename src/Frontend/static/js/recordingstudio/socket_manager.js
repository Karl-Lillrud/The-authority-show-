// src/Frontend/static/js/recordingstudio/socket_manager.js
import { showNotification } from '../components/notifications.js';
import { updateRecordingTime } from './recording_manager.js';
import { fetchGuestsByEpisode } from '../../../static/requests/guestRequests.js';

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
    fetchGuestsByEpisode: fetchGuests // Avoid naming conflict
}) {
    const leaveTimeouts = new Map();

    socket.on('connect', () => {
        console.log('Socket.IO connected:', socket.id);
        showNotification('Connected to server', 'success');
        socket.emit('log_connection', { userId: guestId, socketId: socket.id, role: isHost ? 'host' : 'guest' });
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
            const guests = await fetchGuests(episodeId);
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
            connectedUsers.splice(0, connectedUsers.length, ...connectedUsers.filter(u => u.userId !== data.userId));
            const pc = peerConnections.get(data.userId);
            if (pc) {
                pc.close();
                peerConnections.delete(data.userId);
            }
            domElements.remoteVideoWrapper.style.display = 'none';
            domElements.remoteVideo.srcObject = null;
            try {
                const guests = await fetchGuests(episodeId);
                updateParticipantsList(guests, domElements, connectedUsers, greenroomUsers);
            } catch (error) {
                showNotification('Error: Failed to load guests.', 'error');
            }
        }, 6000));
    });

    socket.on('participant_joined', async (data) => {
        console.log('Participant joined:', data);
        if (leaveTimeouts.has(data.userId)) {
            clearTimeout(leaveTimeouts.get(data.userId));
            leaveTimeouts.delete(data.userId);
        }
        const existingUser = connectedUsers.find(u => u.userId === data.userId);
        if (existingUser) {
            connectedUsers = connectedUsers.map(u =>
                u.userId === data.userId
                    ? { ...u, streamId: data.streamId, guestName: data.guestName }
                    : u
            );
        } else {
            connectedUsers.push({
                userId: data.userId,
                streamId: data.streamId,
                guestName: data.guestName
            });
        }

        for (let i = greenroomUsers.length - 1; i >= 0; i--) {
        if (greenroomUsers[i].userId === data.userId) {
            greenroomUsers.splice(i, 1);
            }
        }

        addParticipantStream(
            data.userId,
            data.streamId,
            data.guestName,
            localStream,
            domElements,
            connectedUsers,
            peerConnections,
            socket,
            room
        );
        try {
            const guests = await fetchGuests(episodeId);
            updateParticipantsList(guests, domElements, connectedUsers, greenroomUsers);
        } catch (error) {
            showNotification('Error: Failed to load guests.', 'error');
        }
        domElements.remoteVideoWrapper.style.display = 'block';
    });

    socket.on('join_studio_approved', async (data) => {
        console.log('Join studio approved:', data);
        let effectiveEpisodeId = data.episodeId || episodeId;
        let effectiveGuestId = data.guestId || guestId;
        let guestName = data.guestName || window.guestName || 'Guest';

        // Fetch guest data if needed
        if (!effectiveGuestId || !effectiveEpisodeId || guestName === 'Host') {
            try {
                const guests = await fetchGuestsByEpisode(episodeId || data.episodeId);
                const guest = guests.find(g => g.id === (data.guestId || guestId));
                effectiveGuestId = guest?.id || effectiveGuestId;
                effectiveEpisodeId = episodeId || data.episodeId;
                guestName = guest?.name || guestName || 'Guest';
            } catch (error) {
                console.error('Failed to fetch guest data:', error);
                showNotification('Warning: Could not fetch guest data.', 'warning');
            }
        }

        // Set room to episodeId
        const effectiveRoom = effectiveEpisodeId;

        if (!effectiveRoom || !effectiveEpisodeId || !effectiveGuestId) {
            console.error('Missing required fields in join_studio_approved:', {
                room: effectiveRoom,
                episodeId: effectiveEpisodeId,
                guestId: effectiveGuestId
            });
            showNotification('Error: Invalid join approval data.', 'error');
            return;
        }

        const joinData = {
            room: effectiveRoom,
            episodeId: effectiveEpisodeId,
            user: { id: effectiveGuestId, name: guestName },
            isHost: false,
            token: data.token || null
        };
        console.log('Emitting join_studio:', joinData);
        socket.emit('join_studio', joinData);
        domElements.remoteVideoWrapper.style.display = 'block';
    });

    socket.on('request_join_studio', (data) => {
        if (!isHost) return;
        if (!data.guestId || !data.episodeId) {
            console.error('Invalid join request:', data);
            showNotification('Error: Invalid join request received.', 'error');
            return;
        }
        showJoinRequest(
            data.guestId,
            data.guestName || 'Guest',
            data.episodeId,
            data.roomId || data.room || data.episodeId,
            domElements,
            socket,
            greenroomUsers,
            async () => {
                try {
                    const guests = await fetchGuests(data.episodeId);
                    updateParticipantsList(guests, domElements, connectedUsers, greenroomUsers);
                } catch (error) {
                    showNotification('Error: Failed to load guests.', 'error');
                }
            }
        );
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

        // Add timer ticking for guest here
        if (window.guestRecordingTimer) clearInterval(window.guestRecordingTimer);
        window.guestRecordingTimer = setInterval(() => {
            updateRecordingTime(domElements, true, false, data.recordingStartTime || Date.now());
        }, 1000);
    }
});



   socket.on('recording_stopped', (data) => {
    console.log('Recording stopped by host:', data);
    updateRecordingTime(domElements, false, false);

    if (!isHost) {
        showNotification('Recording stopped by host.', 'success');
        domElements.pauseButton.disabled = true;
        domElements.stopRecordingBtn.disabled = true;
        domElements.saveRecordingBtn.disabled = true;
        domElements.discardRecordingBtn.disabled = true;

        // Clear guest timer on stop
        if (window.guestRecordingTimer) {
            clearInterval(window.guestRecordingTimer);
            window.guestRecordingTimer = null;
        }

        // Reset timer UI
        if (domElements.recordingTime) {
            domElements.recordingTime.textContent = '00:00:00';
        }
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