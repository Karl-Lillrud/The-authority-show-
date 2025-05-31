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

        let hasJoinedRoom = false;

socket.on('connect', () => {
    console.log('Socket.IO connected:', socket.id);
    showNotification('Connected to server', 'success');

    if (socket && typeof socket.emit === 'function') {
        socket.emit('log_connection', {
            userId: isHost ? 'host' : guestId,
            socketId: socket.id,
            role: isHost ? 'host' : 'guest'
        });
    }

    const waitForStream = setInterval(() => {
        if (localStream && !hasJoinedRoom) {
            clearInterval(waitForStream);
            hasJoinedRoom = true;

            if (socket && typeof socket.emit === 'function') {
                socket.emit('join_room', {
                    room,
                    userId: isHost ? 'host' : guestId,
                    videoEnabled: localStream?.getVideoTracks()?.[0]?.enabled ?? true,
                    audioEnabled: localStream?.getAudioTracks()?.[0]?.enabled ?? true
                });
                console.log('✅ Emitted join_room with all fields');
            }
        }
    }, 200);
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


socket.on('ice_candidate', async (data) => {
    console.log('Received ICE candidate:', data);
    if (!data.room || !data.targetUserId || !data.fromUserId || !data.candidate) {
        console.error('Invalid ICE candidate data:', data);
        showNotification('Error: Invalid ICE candidate received.', 'error');
        return;
    }
    if (data.targetUserId === guestId || (isHost && data.targetUserId === 'host')) {
        const pc = peerConnections.get(data.fromUserId);
        if (pc) {
            try {
                await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
                console.log('Added ICE candidate from:', data.fromUserId);
            } catch (error) {
                console.error('Error adding ICE candidate:', error);
                showNotification('Error: Failed to add ICE candidate.', 'error');
            }
        } else {
            console.warn('No peer connection found for user:', data.fromUserId);
            showNotification('Warning: No peer connection for incoming ICE candidate.', 'warning');
        }
    }
});

   // In socket_manager.js
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
        room,
        guestId // Pass guestId
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

    // FIXED: Recording started event handler
    socket.on('recording_started', (data) => {
        console.log('Recording started:', data);
        
        // Get the recording start time - use server time if available, fallback to current time
        const recordingStartTime = data.recordingStartTime || Date.now();
        
        // Update recording time display immediately for both host and guest
        updateRecordingTime(domElements, true, false, recordingStartTime);

        if (isHost) {
            // Host-specific logic can go here if needed
            console.log('Recording started as host');
        } else {
            // Guest-specific logic
            showNotification('Recording started by host.', 'success');
            
            // Disable guest controls
            if (domElements.pauseButton) domElements.pauseButton.disabled = true;
            if (domElements.stopRecordingBtn) domElements.stopRecordingBtn.disabled = true;
            if (domElements.saveRecordingBtn) domElements.saveRecordingBtn.disabled = true;
            if (domElements.discardRecordingBtn) domElements.discardRecordingBtn.disabled = true;

            // Clear any existing timer
            if (window.guestRecordingTimer) {
                clearInterval(window.guestRecordingTimer);
            }
            
            // Set up guest recording timer with proper start time
            window.guestRecordingTimer = setInterval(() => {
                updateRecordingTime(domElements, true, false, recordingStartTime);
            }, 1000);
            
            console.log('Guest recording timer started with start time:', recordingStartTime);
        }
    });



    // IMPROVED: Recording paused event handler (was missing from cleanup)
    socket.on('recording_paused', (data) => {
        console.log('Recording paused:', data);
        
        // Update recording time display to show paused state
        updateRecordingTime(domElements, true, true, data.recordingStartTime);
        
        if (!isHost) {
            showNotification('Recording paused by host.', 'info');
            
            // Clear guest timer when paused
            if (window.guestRecordingTimer) {
                clearInterval(window.guestRecordingTimer);
                window.guestRecordingTimer = null;
            }
        }
    });

    // IMPROVED: Recording resumed event handler (add this if not handled elsewhere)
    socket.on('recording_resumed', (data) => {
        console.log('Recording resumed:', data);
        
        const recordingStartTime = data.recordingStartTime || Date.now();
        updateRecordingTime(domElements, true, false, recordingStartTime);
        
        if (!isHost) {
            showNotification('Recording resumed by host.', 'success');
            
            // Clear any existing timer
            if (window.guestRecordingTimer) {
                clearInterval(window.guestRecordingTimer);
            }
            
            // Restart guest timer
            window.guestRecordingTimer = setInterval(() => {
                updateRecordingTime(domElements, true, false, recordingStartTime);
            }, 1000);
        }
    });

    socket.on('recording_stopped', (data) => {
        console.log('Recording stopped by host:', data);
        
        // Update recording time display to stopped state
        updateRecordingTime(domElements, false, false);

        if (isHost) {
            // Host-specific logic can go here if needed
            console.log('Recording stopped as host');
        } else {
            showNotification('Recording stopped by host.', 'success');
            
            // Disable guest controls
            if (domElements.pauseButton) domElements.pauseButton.disabled = true;
            if (domElements.stopRecordingBtn) domElements.stopRecordingBtn.disabled = true;
            if (domElements.saveRecordingBtn) domElements.saveRecordingBtn.disabled = true;
            if (domElements.discardRecordingBtn) domElements.discardRecordingBtn.disabled = true;

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

    // IMPROVED: Stream state updates
    socket.on('stream_state_updated', (data) => {
        console.log('Stream state updated:', data);
        
        if (updateIndicators) {
            updateIndicators(data.userId, data);
        }
        
        // Update local controls if this is about the current user
        if (data.userId === guestId && updateLocalControls) {
            updateLocalControls(data);
        }
    });

    // IMPROVED: Better error handling
    socket.on('error', (data) => {
        console.error('Server error:', data);
        
        // Show user-friendly error messages
        let errorMessage = 'An error occurred';
        if (data.message) {
            errorMessage = data.message;
        } else if (typeof data === 'string') {
            errorMessage = data;
        }
        
        showNotification(`Error: ${errorMessage}`, 'error');
        
        // Handle specific error types
        if (data.type === 'recording_error') {
            // Clear any recording timers on recording errors
            if (window.guestRecordingTimer) {
                clearInterval(window.guestRecordingTimer);
                window.guestRecordingTimer = null;
            }
            updateRecordingTime(domElements, false, false);
        }
    });

    // IMPROVED: Connection quality monitoring
    socket.on('connection_quality', (data) => {
        console.log('Connection quality update:', data);
        
        // You can add UI updates here to show connection quality
        if (data.quality === 'poor') {
            showNotification('Poor connection quality detected', 'warning');
        }
    });

    // Cleanup function with improved cleanup
    return () => {
        console.log('Cleaning up socket event listeners');
        
        // Remove all event listeners
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
        socket.off('recording_resumed');
        socket.off('recording_stopped');
        socket.off('stream_state_updated');
        socket.off('connection_quality');
        socket.off('error');
        
        // Clear all timeouts
        leaveTimeouts.forEach(timeout => clearTimeout(timeout));
        leaveTimeouts.clear();
        
        // Clear guest recording timer if it exists
        if (window.guestRecordingTimer) {
            clearInterval(window.guestRecordingTimer);
            window.guestRecordingTimer = null;
        }
        
        console.log('Socket cleanup completed');
    };
}