// Fixed WebRTC Manager - Consolidated and improved
import { showNotification } from '../components/notifications.js';

const candidateQueue = new Map();
const pendingAnswers = new Map();

export function setupWebRTC(socket, config) {
    const {
        room,
        localStream,
        domElements,
        connectedUsers,
        peerConnections,
        addParticipantStream,
        guestId,
        isHost
    } = config;

    // Consistent user ID handling
    const selfId = isHost ? 'host' : guestId;
    console.log(`🔧 Setting up WebRTC for ${selfId} in room ${room}`);

    // Validate required parameters
    if (!room || !socket) {
        console.error('❌ Missing required WebRTC setup parameters');
        return null;
    }

    // Enhanced offer handler with better validation
    socket.on('webrtc_offer', async (data) => {
        console.log('📥 Received WebRTC offer:', {
            from: data.fromUserId,
            to: data.targetUserId,
            room: data.room,
            selfId: selfId
        });

        // Comprehensive validation
        if (!isValidSignalingMessage(data, 'offer')) {
            return;
        }

        // Check if this offer is for us
        if (data.targetUserId !== selfId) {
            console.log('⏭️ Offer not for us, ignoring');
            return;
        }

        if (data.fromUserId === selfId) {
            console.warn('⛔ Ignoring offer from self');
            return;
        }

        console.log(`✅ Processing offer from ${data.fromUserId} to ${selfId}`);

        const pc = peerConnections.get(data.fromUserId);
        if (!pc) {
            console.error(`❌ No peer connection found for ${data.fromUserId}`);
            return;
        }

        try {
            // Check if we already have a remote description
            if (pc.signalingState !== 'stable' && pc.signalingState !== 'have-local-offer') {
                console.warn(`⚠️ Unexpected signaling state: ${pc.signalingState}, resetting connection`);
                await resetPeerConnection(data.fromUserId, pc, peerConnections);
                return;
            }

            console.log(`🔄 Setting remote description for ${data.fromUserId}`);
            await pc.setRemoteDescription(new RTCSessionDescription(data.offer));
            console.log(`✅ Remote description set for ${data.fromUserId}`);

            // Process queued ICE candidates after setting remote description
            await processQueuedCandidates(data.fromUserId, pc);

            console.log(`🔄 Creating answer for ${data.fromUserId}`);
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);
            console.log(`✅ Local description set, sending answer to ${data.fromUserId}`);
            
            socket.emit('webrtc_answer', {
                room,
                targetUserId: data.fromUserId,
                fromUserId: selfId,
                answer: pc.localDescription
            });
            console.log(`📤 Sent answer to: ${data.fromUserId}`);
        } catch (error) {
            console.error('❌ Error handling WebRTC offer:', error);
            showNotification('WebRTC connection error. Retrying...', 'warning');
            // Attempt to recover
            await handleConnectionError(data.fromUserId, pc, peerConnections);
        }
    });

    // Enhanced answer handler
    socket.on('webrtc_answer', async (data) => {
        console.log('📥 Received WebRTC answer:', {
            from: data.fromUserId,
            to: data.targetUserId,
            room: data.room,
            selfId: selfId
        });

        if (!isValidSignalingMessage(data, 'answer')) {
            return;
        }

        // Check if this answer is for us
        if (data.targetUserId !== selfId) {
            console.log('⏭️ Answer not for us, ignoring');
            return;
        }

        console.log(`✅ Processing answer from ${data.fromUserId} to ${selfId}`);

        const pc = peerConnections.get(data.fromUserId);
        if (!pc) {
            console.error(`❌ No peer connection found for ${data.fromUserId}`);
            return;
        }

        console.log(`🔍 Signaling state for ${data.fromUserId}:`, pc.signalingState);

        if (pc.signalingState === 'have-local-offer') {
            try {
                console.log(`🔄 Setting remote description (answer) for ${data.fromUserId}`);
                await pc.setRemoteDescription(new RTCSessionDescription(data.answer));
                console.log(`✅ Remote description set for ${data.fromUserId}`);

                // Process queued ICE candidates
                await processQueuedCandidates(data.fromUserId, pc);
            } catch (error) {
                console.error('❌ Error handling WebRTC answer:', error);
                await handleConnectionError(data.fromUserId, pc, peerConnections);
            }
        } else {
            console.warn(`💤 Storing answer for later from: ${data.fromUserId} (state: ${pc.signalingState})`);
            pendingAnswers.set(data.fromUserId, data.answer);
        }
    });

    // Consolidated ICE candidate handler (removing duplicate from socket_manager)
    socket.on('ice_candidate', async (data) => {
        console.log('📥 Received ICE candidate:', {
            from: data.fromUserId,
            to: data.targetUserId,
            room: data.room,
            selfId: selfId
        });

        if (!isValidSignalingMessage(data, 'ice_candidate')) {
            return;
        }

        // Check if this ICE candidate is for us
        if (data.targetUserId !== selfId) {
            console.log('⏭️ ICE candidate not for us, ignoring');
            return;
        }

        console.log(`✅ Processing ICE candidate from ${data.fromUserId} to ${selfId}`);

        const pc = peerConnections.get(data.fromUserId);
        if (!pc) {
            console.warn(`❌ No peer connection found for ${data.fromUserId}, queuing candidate`);
            queueCandidate(data.fromUserId, data.candidate);
            return;
        }

        if (pc.remoteDescription && pc.remoteDescription.type) {
            try {
                console.log(`🔄 Adding ICE candidate from ${data.fromUserId}`);
                await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
                console.log(`✅ Added ICE candidate from: ${data.fromUserId}`);
            } catch (error) {
                console.error('❌ Error handling ICE candidate:', error);
                // Don't show notification for ICE candidate errors as they're common
            }
        } else {
            console.log(`💾 Queuing ICE candidate from: ${data.fromUserId} (remote desc not ready)`);
            queueCandidate(data.fromUserId, data.candidate);
        }
    });

    // Helper functions
    function isValidSignalingMessage(data, type) {
        if (!data.room || !data.targetUserId || !data.fromUserId) {
            console.error(`❌ Invalid ${type} data:`, data);
            showNotification(`Error: Invalid WebRTC ${type} received.`, 'error');
            return false;
        }

        if (type === 'offer' && !data.offer) {
            console.error('❌ Missing offer in offer message');
            return false;
        }

        if (type === 'answer' && !data.answer) {
            console.error('❌ Missing answer in answer message');
            return false;
        }

        if (type === 'ice_candidate' && !data.candidate) {
            console.error('❌ Missing candidate in ICE message');
            return false;
        }

        return true;
    }

    function queueCandidate(userId, candidate) {
        if (!candidateQueue.has(userId)) {
            candidateQueue.set(userId, []);
        }
        candidateQueue.get(userId).push(candidate);
    }

    async function processQueuedCandidates(userId, pc) {
        const queued = candidateQueue.get(userId) || [];
        console.log(`📦 Processing ${queued.length} queued ICE candidates for ${userId}`);
        
        for (const candidate of queued) {
            try {
                await pc.addIceCandidate(new RTCIceCandidate(candidate));
                console.log(`✅ Added queued ICE candidate from ${userId}`);
            } catch (error) {
                console.error('❌ Error adding queued ICE candidate:', error);
            }
        }
        candidateQueue.delete(userId);
    }

    async function resetPeerConnection(userId, pc, peerConnections) {
        console.log(`🔄 Resetting peer connection for ${userId}`);
        
        // Close old connection
        pc.close();
        peerConnections.delete(userId);
        
        // Clear queues
        candidateQueue.delete(userId);
        pendingAnswers.delete(userId);
        
        console.log(`✅ Peer connection reset for ${userId}`);
    }

    async function handleConnectionError(userId, pc, peerConnections) {
        console.log(`🔄 Handling connection error for ${userId}`);
        
        // Wait a bit before retry
        setTimeout(async () => {
            if (pc.connectionState === 'failed' || pc.iceConnectionState === 'failed') {
                console.log(`🔄 Attempting to restart ICE for ${userId}`);
                try {
                    await pc.restartIce();
                } catch (error) {
                    console.error(`❌ Failed to restart ICE for ${userId}:`, error);
                    await resetPeerConnection(userId, pc, peerConnections);
                }
            }
        }, 2000);
    }

    // Return cleanup function
    return () => {
        console.log('🧹 Cleaning up WebRTC event listeners');
        socket.off('webrtc_offer');
        socket.off('webrtc_answer');
        socket.off('ice_candidate');
        candidateQueue.clear();
        pendingAnswers.clear();
    };
}

// Enhanced addParticipantStream with better error handling and recovery
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
    guestId,
    isHost = false
) {
    const selfId = isHost ? 'host' : guestId;
    console.log(`🔄 Adding participant stream: ${userId} (self: ${selfId})`);

    if (userId === selfId) {
        console.warn(`⛔ Skipping WebRTC connection to self (${userId})`);
        return;
    }

    const { remoteVideo, remoteVideoWrapper } = domElements;
    
    // Validate prerequisites
    if (!localStream) {
        console.error('❌ Local stream not ready');
        showNotification('Local stream not ready. Please ensure microphone is initialized.', 'warning');
        return;
    }

    if (!socket || !room) {
        console.error('❌ Missing socket or room for WebRTC setup');
        return;
    }

    // Don't create duplicate connections
    if (peerConnections.has(userId)) {
        console.warn(`⚠️ Peer connection already exists for ${userId}, cleaning up first`);
        const existingPc = peerConnections.get(userId);
        existingPc.close();
        peerConnections.delete(userId);
    }

    console.log(`✅ Creating new peer connection for ${userId}`);

    const pc = new RTCPeerConnection({
        iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' },
            {
                urls: 'turn:openrelay.metered.ca:80',
                username: 'openrelayproject',
                credential: 'openrelayproject'
            },
            {
                urls: 'turn:openrelay.metered.ca:443',
                username: 'openrelayproject',
                credential: 'openrelayproject'
            }
        ],
        iceCandidatePoolSize: 10
    });

    peerConnections.set(userId, pc);
    console.log(`📝 Stored peer connection for ${userId}`);

    // Enhanced connection monitoring with recovery
    pc.onconnectionstatechange = () => {
        console.log(`🔄 Connection state for ${userId}:`, pc.connectionState);
        
        switch (pc.connectionState) {
            case 'connected':
                console.log(`✅ WebRTC connection established with ${userId}`);
                showNotification(`Connected to ${guestName}`, 'success');
                break;
            case 'failed':
                console.error(`❌ WebRTC connection failed with ${userId}`);
                showNotification(`Connection failed with ${guestName}. Retrying...`, 'warning');
                // Attempt recovery
                setTimeout(() => {
                    if (pc.connectionState === 'failed') {
                        console.log(`🔄 Attempting connection recovery for ${userId}`);
                        pc.restartIce().catch(err => {
                            console.error(`Failed to restart ICE for ${userId}:`, err);
                        });
                    }
                }, 3000);
                break;
            case 'disconnected':
                console.warn(`⚠️ WebRTC connection disconnected with ${userId}`);
                showNotification(`Connection unstable with ${guestName}`, 'warning');
                break;
            case 'closed':
                console.log(`🔒 WebRTC connection closed with ${userId}`);
                break;
        }
    };

    pc.oniceconnectionstatechange = () => {
        console.log(`🧊 ICE connection state for ${userId}:`, pc.iceConnectionState);
        
        if (pc.iceConnectionState === 'failed') {
            console.error(`❌ ICE connection failed for ${userId}`);
            // Attempt ICE restart
            setTimeout(() => {
                if (pc.iceConnectionState === 'failed') {
                    pc.restartIce().catch(err => {
                        console.error(`Failed to restart ICE for ${userId}:`, err);
                    });
                }
            }, 1000);
        }
    };

    pc.onsignalingstatechange = () => {
        console.log(`📡 Signaling state for ${userId}:`, pc.signalingState);
    };

    pc.ontrack = (event) => {
        console.log(`🎵 Received track from ${userId}:`, {
            kind: event.track.kind,
            streams: event.streams.length
        });
        
        if (event.streams[0]) {
            const videoElement = connectedUsers.length <= 1
                ? remoteVideo
                : document.getElementById(`video-${userId}`);

            if (videoElement) {
                console.log(`📺 Setting srcObject for ${userId}`);
                videoElement.srcObject = event.streams[0];
                
                // Enable audio tracks
                event.streams[0].getAudioTracks().forEach(track => {
                    track.enabled = true;
                    console.log(`✅ Remote audio track enabled for ${userId}:`, track.label);
                });

                // Handle track ended
                event.track.onended = () => {
                    console.log(`🔚 Track ended for ${userId}:`, event.track.kind);
                };
            } else {
                console.warn(`⚠️ No video element found for ${userId}`);
            }

            if (connectedUsers.length <= 1 && remoteVideoWrapper) {
                remoteVideoWrapper.style.display = 'block';
                console.log('📺 Remote video wrapper displayed');
            }
        }
    };

    pc.onicecandidate = (event) => {
        if (event.candidate) {
            console.log(`📤 Emitting ICE candidate to ${userId}`);
            socket.emit('ice_candidate', {
                room,
                targetUserId: userId,
                fromUserId: selfId,
                candidate: event.candidate
            });
        } else {
            console.log(`🏁 ICE gathering complete for ${userId}`);
        }
    };

    // Add local stream tracks to peer connection
    console.log(`🎙️ Adding local tracks to peer connection for ${userId}`);
    try {
        localStream.getTracks().forEach(track => {
            pc.addTrack(track, localStream);
            if (track.kind === 'audio') {
                track.enabled = true;
                console.log(`🎙️ Local audio track enabled for ${userId}:`, track.label);
            }
        });
    } catch (error) {
        console.error(`❌ Error adding tracks for ${userId}:`, error);
        showNotification('Failed to add media tracks.', 'error');
        peerConnections.delete(userId);
        pc.close();
        return;
    }

    try {
        console.log(`🔄 Creating offer for ${userId}`);
        const offer = await pc.createOffer({
            offerToReceiveAudio: true,
            offerToReceiveVideo: false
        });
        await pc.setLocalDescription(offer);
        console.log(`✅ Local description set, sending offer to ${userId}`);
        
        socket.emit('webrtc_offer', {
            room,
            targetUserId: userId,
            fromUserId: selfId,
            offer: pc.localDescription
        });
        console.log(`📤 Sent WebRTC offer to: ${userId}`);
    } catch (error) {
        console.error(`❌ Error creating WebRTC offer for ${userId}:`, error);
        showNotification('Failed to establish WebRTC connection.', 'error');
        // Clean up failed connection
        peerConnections.delete(userId);
        pc.close();
        return;
    }

    // Process any queued ICE candidates
    const queuedCandidates = candidateQueue.get(userId);
    if (queuedCandidates && queuedCandidates.length > 0) {
        console.log(`📦 Processing ${queuedCandidates.length} queued candidates for ${userId}`);
        for (const candidate of queuedCandidates) {
            try {
                await pc.addIceCandidate(new RTCIceCandidate(candidate));
                console.log(`✅ Added queued ICE candidate from: ${userId}`);
            } catch (err) {
                console.error(`❌ Error adding queued ICE candidate from ${userId}:`, err);
            }
        }
        candidateQueue.delete(userId);
    }
}