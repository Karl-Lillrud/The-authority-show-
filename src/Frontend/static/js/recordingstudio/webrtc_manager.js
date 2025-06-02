import { showNotification } from '../components/notifications.js';

const candidateQueue = new Map();

export function setupWebRTC(socket, config) {
    const {
        room,
        localStream,
        domElements,
        connectedUsers,
        peerConnections,
        addParticipantStream,
        guestId
    } = config;
    const { remoteVideo, remoteVideoWrapper } = domElements;
    const pendingAnswers = new Map();

    socket.on('offer', async (data) => {
        console.log('Received offer:', data);
        if (!data.room || !data.targetUserId || !data.fromUserId || !data.offer) {
            console.error('Invalid offer data:', data);
            showNotification('Error: Invalid WebRTC offer received.', 'error');
            return;
        }
        if (data.targetUserId === (guestId || 'host')) {
            const pc = peerConnections.get(data.fromUserId);
            if (pc) {
                try {
                    await pc.setRemoteDescription(new RTCSessionDescription(data.offer));
                    const queued = candidateQueue.get(data.fromUserId) || [];
                    for (const c of queued) {
                        try {
                            await pc.addIceCandidate(new RTCIceCandidate(c));
                        } catch (error) {
                            console.error('Error adding queued ICE candidate:', error);
                        }
                    }
                    candidateQueue.delete(data.fromUserId);
                    const answer = await pc.createAnswer();
                    await pc.setLocalDescription(answer);
                    socket.emit('answer', {
                        room,
                        targetUserId: data.fromUserId,
                        fromUserId: guestId || 'host',
                        answer: pc.localDescription
                    });
                    console.log('Sent answer to:', data.fromUserId);
                } catch (error) {
                    console.error('Error handling WebRTC offer:', error);
                    showNotification('WebRTC signaling error.', 'error');
                }
            }
        }
    });

    socket.on('answer', async (data) => {
        console.log('Received answer:', data);
        if (!data.room || !data.targetUserId || !data.fromUserId || !data.answer) {
            console.error('Invalid answer data:', data);
            showNotification('Error: Invalid WebRTC answer received.', 'error');
            return;
        }
        if (data.targetUserId === (guestId || 'host')) {
            const pc = peerConnections.get(data.fromUserId);
            if (pc) {
                if (pc.signalingState === 'have-local-offer') {
                    try {
                        await pc.setRemoteDescription(new RTCSessionDescription(data.answer));
                        const queued = candidateQueue.get(data.fromUserId) || [];
                        for (const c of queued) {
                            try {
                                await pc.addIceCandidate(new RTCIceCandidate(c));
                            } catch (error) {
                                console.error('Error adding queued ICE candidate:', error);
                            }
                        }
                        candidateQueue.delete(data.fromUserId);
                    } catch (error) {
                        console.error('Error handling WebRTC answer:', error);
                    }
                } else {
                    pendingAnswers.set(data.fromUserId, data.answer);
                }
            }
        }
    });

    socket.on('ice_candidate', async (data) => {
        console.log('Received ICE candidate:', data);
        if (!data.room || !data.targetUserId || !data.fromUserId || !data.candidate) {
            console.error('Invalid ICE data:', data);
            showNotification('Error: Invalid ICE candidate received.', 'error');
            return;
        }
        if (data.targetUserId === (guestId || 'host')) {
            const pc = peerConnections.get(data.fromUserId);
            if (pc) {
                if (pc.remoteDescription && pc.remoteDescription.type) {
                    try {
                        await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
                    } catch (error) {
                        console.error('Error handling ICE candidate:', error);
                        showNotification('WebRTC ICE candidate error.', 'error');
                    }
                } else {
                    if (!candidateQueue.has(data.fromUserId)) {
                        candidateQueue.set(data.fromUserId, []);
                    }
                    candidateQueue.get(data.fromUserId).push(data.candidate);
                }
            }
        }
    });
}

// In webrtc_manager.js
export async function addParticipantStream(
    userId,
    streamId,
    guestName,
    localStream,
    domElements,
    connectedUsers,
    peerConnections,
    socket,
    room,
    guestId
) {
    const { remoteVideo, remoteVideoWrapper } = domElements;
    if (!localStream) {
        showNotification('Local stream not ready. Please ensure microphone is initialized.', 'warning');
        return;
    }

    const pc = new RTCPeerConnection({
        iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            {
                urls: 'turn:openrelay.metered.ca:80',
                username: 'openrelayproject',
                credential: 'openrelayproject'
            }
        ]
    });

    peerConnections.set(userId, pc);

    pc.ontrack = (event) => {
        if (event.streams[0]) {
            const videoElement = connectedUsers.length <= 1
                ? remoteVideo
                : document.getElementById(`video-${userId}`);
            if (videoElement) {
                videoElement.srcObject = event.streams[0];
                event.streams[0].getAudioTracks().forEach(track => {
                    track.enabled = true;
                    console.log('Remote audio track enabled:', track);
                });
            }
            if (connectedUsers.length <= 1) remoteVideoWrapper.style.display = 'block';
        }
    };

    pc.onicecandidate = (event) => {
        if (event.candidate) {
            console.log('Emitting ICE candidate:', {
                room,
                targetUserId: userId,
                fromUserId: guestId || 'host',
                candidate: event.candidate
            });
            socket.emit('ice_candidate', {
                room,
                targetUserId: userId,
                fromUserId: guestId || 'host',
                candidate: event.candidate
            });
        }
    };

    localStream.getTracks().forEach(track => {
        pc.addTrack(track, localStream);
        if (track.kind === 'audio') {
            track.enabled = true;
            console.log('Local audio track enabled:', track);
        }
    });

    try {
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        socket.emit('offer', {
            room,
            targetUserId: userId,
            fromUserId: guestId || 'host',
            offer: pc.localDescription
        });
        console.log('Sent offer to:', userId);
    } catch (error) {
        console.error('Error creating WebRTC offer:', error);
        showNotification('Failed to establish WebRTC connection.', 'error');
    }

    if (candidateQueue.has(userId)) {
    const queuedCandidates = candidateQueue.get(userId);
    for (const candidate of queuedCandidates) {
        try {
            await pc.addIceCandidate(new RTCIceCandidate(candidate));
            console.log('✅ Added queued ICE candidate from:', userId);
        } catch (err) {
            console.error('❌ Error adding queued ICE candidate:', err);
        }
    }
    candidateQueue.delete(userId);
}
}
