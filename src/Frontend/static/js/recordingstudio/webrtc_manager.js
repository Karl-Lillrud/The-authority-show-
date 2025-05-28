// src/Frontend/static/js/recordingstudio/webrtc_manager.js
import { showNotification } from '../components/notifications.js';

export function setupWebRTC(socket, room, localStream, domElements, connectedUsers, peerConnections, addParticipantStream) {
    const { remoteVideo, remoteVideoWrapper } = domElements;
    const pendingAnswers = new Map();

    socket.on('offer', async (data) => {
        const { userId, offer } = data;
        const pc = peerConnections.get(userId);
        if (pc) {
            try {
                await pc.setRemoteDescription(new RTCSessionDescription(offer));
                const answer = await pc.createAnswer();
                await pc.setLocalDescription(answer);
                socket.emit('answer', { room, userId, answer: pc.localDescription });
            } catch (error) {
                console.error('Error handling WebRTC offer:', error);
                showNotification('WebRTC signaling error.', 'error');
            }
        }
    });

    socket.on('answer', async (data) => {
        const { userId, answer } = data;
        const pc = peerConnections.get(userId);
        if (pc) {
            if (pc.signalingState === 'have-local-offer') {
                try {
                    await pc.setRemoteDescription(new RTCSessionDescription(answer));
                } catch (error) {
                    console.error('Error handling WebRTC answer:', error);
                }
            } else {
                pendingAnswers.set(userId, answer);
            }
        }
    });

    socket.on('ice_candidate', async (data) => {
        const { userId, candidate } = data;
        const pc = peerConnections.get(userId);
        if (pc) {
            try {
                await pc.addIceCandidate(new RTCIceCandidate(candidate));
            } catch (error) {
                console.error('Error handling ICE candidate:', error);
                showNotification('WebRTC ICE candidate error.', 'error');
            }
        }
    });
}

export async function addParticipantStream(userId, streamId, guestName, localStream, domElements, connectedUsers, peerConnections, socket, room) {
    const { remoteVideo, remoteVideoWrapper } = domElements;
    if (!localStream) {
        showNotification('Local stream not ready. Please ensure microphone is initialized.', 'warning');
        await new Promise(resolve => {
            const checkStream = setInterval(() => {
                if (localStream) {
                    clearInterval(checkStream);
                    resolve();
                }
            }, 1000);
        });
    }

    const pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] });
    peerConnections.set(userId, pc);

    pc.ontrack = (event) => {
        if (event.streams[0]) {
            const videoElement = connectedUsers.length <= 1 ? remoteVideo : document.getElementById(`video-${userId}`);
            if (videoElement) videoElement.srcObject = event.streams[0];
            if (connectedUsers.length <= 1) remoteVideoWrapper.style.display = 'block';
        }
    };

    pc.onicecandidate = (event) => {
        if (event.candidate) {
            socket.emit('ice_candidate', { room, userId, candidate: event.candidate });
        }
    };

    localStream.getTracks().forEach(track => pc.addTrack(track, localStream));
    try {
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        socket.emit('offer', { room, userId, offer: pc.localDescription });
    } catch (error) {
        console.error('Error creating WebRTC offer:', error);
        showNotification('Failed to establish WebRTC connection.', 'error');
    }
}