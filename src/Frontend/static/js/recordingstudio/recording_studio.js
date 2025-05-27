import { showNotification } from '../components/notifications.js';
import { fetchEpisode, updateEpisode } from '../../../static/requests/episodeRequest.js';
import { fetchGuestsByEpisode } from '../../../static/requests/guestRequests.js';

// Initialize Socket.IO with reconnection
const socket = io({
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000
});

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const participantsContainer = document.getElementById('participantsContainer');
    const startRecordingBtn = document.getElementById('startRecordingBtn');
    const pauseButton = document.getElementById('pauseButton');
    const stopRecordingBtn = document.getElementById('stopRecordingBtn');
    const saveRecordingBtn = document.getElementById('saveRecording');
    const discardRecordingBtn = document.getElementById('discardRecording');
    const cameraSelect = document.getElementById('cameraSelect');
    const microphoneSelect = document.getElementById('microphoneSelect');
    const speakerSelect = document.getElementById('speakerSelect');
    const videoQualitySelect = document.getElementById('videoQuality');
    const videoPreview = document.getElementById('videoPreview');
    const remoteVideo = document.getElementById('remoteVideo');
    const remoteVideoWrapper = document.getElementById('remoteVideoWrapper');
    const joinRequestModal = document.getElementById('joinRequestModal');
    const toggleCameraBtn = document.getElementById('toggle-camera');
    const toggleMicBtn = document.getElementById('toggle-mic');
    const hostControls = document.getElementById('hostControls');
    const recordingTime = document.getElementById('recordingTime');
    const videoIndicator = document.getElementById('videoIndicator');
    const audioIndicator = document.getElementById('audioIndicator');

    // Variables
    let localStream = null;
    let episode = null;
    let isRecording = false;
    let isPaused = false;
    let connectedUsers = [];
    let greenroomUsers = [];
    let isCameraActive = false;
    let isMicActive = false;
    let peerConnections = new Map();
    let recordingStartTime = null;
    let timerInterval = null;
    const maxMicRetries = 5;
    let micRetryCount = 0;
    const micRetryDelay = 10000; // 10 seconds
    let currentJoinRequest = null;
    let pauseStartTime = null;
    let totalPausedTime = 0;
    let mediaRecorder = null;
    let recordedChunks = [];

    // Get URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const podcastId = urlParams.get('podcastId');
    const episodeId = urlParams.get('episodeId');
    const guestId = urlParams.get('guestId');
    const token = urlParams.get('token');
    let room = urlParams.get('room');
    const isHost = !guestId || !token;

    console.log('Studio initialized with params:', { podcastId, episodeId, room, guestId, token, isHost });
    console.log('Client role:', isHost ? 'Host' : 'Guest');

    // Validate DOM elements
    const missingElements = [];
    if (!participantsContainer) missingElements.push('participantsContainer');
    if (!joinRequestModal) missingElements.push('joinRequestModal');
    if (!videoPreview) missingElements.push('videoPreview');
    if (!remoteVideo) missingElements.push('remoteVideo');
    if (!remoteVideoWrapper) missingElements.push('remoteVideoWrapper');
    if (!toggleCameraBtn) missingElements.push('toggleCameraBtn');
    if (!toggleMicBtn) missingElements.push('toggleMicBtn');
    if (!recordingTime) missingElements.push('recordingTime');
    if (!videoIndicator) missingElements.push('videoIndicator');
    if (!audioIndicator) missingElements.push('audioIndicator');
    if (missingElements.length > 0) {
        console.error('Missing required DOM elements:', missingElements);
        showNotification(`Error: Missing interface elements: ${missingElements.join(', ')}.`, 'error');
        return;
    }

    // Show/hide controls based on role
if (isHost) {
    if (hostControls) hostControls.style.display = 'flex'; // Host-specific controls
} else {
    // Ensure guest has access to device controls
    if (cameraSelect) cameraSelect.style.display = 'block';
    if (microphoneSelect) microphoneSelect.style.display = 'block';
    if (speakerSelect) speakerSelect.style.display = 'block';
    if (toggleCameraBtn) toggleCameraBtn.style.display = 'block';
    if (toggleMicBtn) toggleMicBtn.style.display = 'block';
}

    // Validate URL parameters
    if (!episodeId || (guestId && !token)) {
        console.error('Missing required URL parameters:', { episodeId, guestId, token });
        showNotification('Error: Missing required parameters.', 'error');
        return;
    }

    // Wait for socket connection
    function waitForSocketConnection() {
        return new Promise(resolve => {
            if (socket.connected) {
                console.log('Socket.IO already connected:', socket.id);
                resolve();
            } else {
                socket.once('connect', () => {
                    console.log('Socket.IO connected:', socket.id);
                    resolve();
                });
            }
        });
    }

    // Update recording time
function updateRecordingTime() {
    if (!recordingTime) {
        console.error(`[${isHost ? 'Host' : 'Guest'}] recordingTime DOM element not found in updateRecordingTime`);
        return;
    }
    if (isRecording && !isPaused && recordingStartTime) {
        const elapsed = Date.now() - recordingStartTime - totalPausedTime;
        const hours = Math.floor(elapsed / 3600000);
        const minutes = Math.floor((elapsed % 3600000) / 60000);
        const seconds = Math.floor((elapsed % 60000) / 1000);
        recordingTime.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        console.log(`[${isHost ? 'Host' : 'Guest'}] Updated recordingTime: ${recordingTime.textContent}`);
    } else {
        console.warn(`[${isHost ? 'Host' : 'Guest'}] Skipped timer update: isRecording=${isRecording}, isPaused=${isPaused}, recordingStartTime=${recordingStartTime}`);
    }
}

    async function initializeDevices() {
    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
            throw new Error('MediaDevices API not supported');
        }
        const devices = await navigator.mediaDevices.enumerateDevices();
        console.log('Available devices:', devices.map(d => ({ kind: d.kind, label: d.label, deviceId: d.deviceId })));

        // Populate camera select
        const videoDevices = devices.filter(device => device.kind === 'videoinput');
        cameraSelect.innerHTML = '<option value="">Select Camera</option>';
        if (videoDevices.length > 0) {
            cameraSelect.innerHTML += videoDevices.map(device => 
                `<option value="${device.deviceId}">${device.label || `Camera ${videoDevices.indexOf(device) + 1}`}</option>`
            ).join('');
        } else {
            cameraSelect.innerHTML += '<option value="" disabled>No cameras detected</option>';
            showNotification('No camera detected. Video features will be limited.', 'warning');
        }

        // Populate microphone select
        const audioDevices = devices.filter(device => device.kind === 'audioinput');
        microphoneSelect.innerHTML = '<option value="">Select Microphone</option>';
        if (audioDevices.length > 0) {
            microphoneSelect.innerHTML += audioDevices.map(device => 
                `<option value="${device.deviceId}">${device.label || `Microphone ${audioDevices.indexOf(device) + 1}`}</option>`
            ).join('');
        } else {
            microphoneSelect.innerHTML += '<option value="" disabled>No microphones detected</option>';
            showNotification('No microphone detected. Please connect a microphone.', 'error');
        }

        // Populate speaker select (for both host and guest)
        const speakerDevices = devices.filter(device => device.kind === 'audiooutput');
        speakerSelect.innerHTML = '<option value="">Select Speaker</option>';
        if (speakerDevices.length > 0) {
            speakerDevices.forEach(device => {
                speakerSelect.innerHTML += `<option value="${device.deviceId}">${device.label || `Speaker ${speakerDevices.indexOf(device) + 1}`}</option>`;
            });
        } else {
            speakerSelect.innerHTML += '<option value="" disabled>No speakers detected</option>';
            showNotification('No speakers detected. Audio output may be limited.', 'warning');
        }

        // Try to initialize microphone and camera if available
        if (audioDevices.length > 0) {
            await tryInitializeMicrophone(audioDevices[0].deviceId);
            if (videoDevices.length > 0) {
                await startCamera(videoDevices[0].deviceId); // Automatically start camera
                isCameraActive = true;
            }
            return true;
        } else {
            await retryMicrophoneInitialization();
            return localStream !== null;
        }
    } catch (error) {
        console.error('Error initializing devices:', error);
        showNotification(`Failed to initialize devices: ${error.message}`, 'error');
        await retryMicrophoneInitialization();
        return localStream !== null;
    }
}

    // Retry microphone initialization
    async function retryMicrophoneInitialization() {
        if (micRetryCount >= maxMicRetries) {
            showNotification('Max microphone initialization attempts reached. Please select a microphone manually.', 'error');
            return false;
        }
        micRetryCount++;
        showNotification(`Microphone not found. Retrying in ${micRetryDelay / 1000} seconds (Attempt ${micRetryCount}/${maxMicRetries}).`, 'info');
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const audioDevices = devices.filter(device => device.kind === 'audioinput');
            if (audioDevices.length > 0) {
                await tryInitializeMicrophone(audioDevices[0].deviceId);
                return true;
            } else {
                setTimeout(retryMicrophoneInitialization, 1000);
                return false;
            }
        } catch (error) {
            console.error('Retry failed:', error);
            setTimeout(retryMicrophoneInitialization, 1000);
            return false;
        }
    }

    // Initialize microphone
   async function tryInitializeMicrophone(deviceId) {
    try {
        const audioStream = await navigator.mediaDevices.getUserMedia({
            audio: { deviceId: deviceId ? { exact: deviceId } : undefined }
        });
        localStream = audioStream;
        console.log('[Microphone] Initialized stream with tracks:', audioStream.getTracks().map(t => ({ kind: t.kind, enabled: t.enabled })));
        isMicActive = true;
        videoPreview.srcObject = null;
        const userId = guestId || 'host';
        socket.emit('update_stream_state', { room, userId, isMicActive: true, isCameraActive });
        updateIndicators();
        updateLocalControls();
        micRetryCount = 0;
        showNotification('Microphone initialized successfully.', 'success');
    } catch (error) {
        console.error('[Microphone] Error initializing microphone:', error);
        localStream = null;
        showNotification(`Microphone error: ${error.message}. Retrying...`, 'error');
        await retryMicrophone();
    }
}

    // Start camera
    async function startCamera(deviceId) {
        try {
            if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
                throw new Error('Camera access requires HTTPS');
            }
            if (localStream) {
                localStream.getTracks().filter(track => track.kind === 'video').forEach(track => track.stop());
            }
            const constraints = {
                video: { deviceId: deviceId ? { exact: deviceId } : undefined },
                audio: isMicActive ? { deviceId: microphoneSelect?.value || undefined } : false
            };
            if (isHost && videoQualitySelect?.value) {
                const quality = videoQualitySelect.value;
                constraints.video.width = quality === '1080p' ? 1920 : quality === '720p' ? 1280 : 640;
                constraints.video.height = quality === '1080p' ? 1080 : quality === '720p' ? 720 : 480;
            }
            const videoStream = await navigator.mediaDevices.getUserMedia(constraints);
            if (!localStream) {
                localStream = videoStream;
            } else {
                videoStream.getTracks().forEach(track => localStream.addTrack(track));
            }
            videoPreview.srcObject = localStream;
            socket.emit('update_stream_state', { room, userId: guestId || 'host', isCameraActive: true });
            updateIndicators();
            updateLocalControls();
            showNotification('Camera started successfully.', 'success');
        } catch (error) {
            console.error('Error starting camera:', error);
            showNotification(`Camera error: ${error.message}`, 'error');
            isCameraActive = false;
            updateIndicators();
            updateLocalControls();
        }
    }

    // Toggle camera
    async function toggleCamera() {
        if (isCameraActive) {
            // Turn off camera
            if (localStream) {
                const videoTrack = localStream.getVideoTracks()[0];
                if (videoTrack) {
                    videoTrack.stop();
                    localStream.removeTrack(videoTrack);
                    videoPreview.srcObject = localStream;
                    isCameraActive = false;
                    socket.emit('update_stream_state', { room, userId: guestId || 'host', isCameraActive });
                    updateIndicators();
                    updateLocalControls();
                }
            }
        } else {
            // Turn on camera
            const deviceId = cameraSelect?.value || null;
            if (deviceId) {
                await startCamera(deviceId);
                isCameraActive = true;
            } else {
                showNotification('Please select a camera to enable video.', 'warning');
            }
        }
    }

    // Toggle microphone
    function toggleMicrophone() {
        if (localStream) {
            const audioTrack = localStream.getAudioTracks()[0];
            if (audioTrack) {
                isMicActive = !isMicActive;
                audioTrack.enabled = isMicActive;
                socket.emit('update_stream_state', { room, userId: guestId || 'host', isMicActive });
                updateIndicators();
                updateLocalControls();
            } else if (!isMicActive && microphoneSelect?.value) {
                tryInitializeMicrophone(microphoneSelect.value);
            }
        } else {
            showNotification('No audio stream available. Please select a microphone.', 'error');
        }
    }

    // Update status indicators
    function updateIndicators() {
        if (videoIndicator) {
            videoIndicator.className = `indicator video-indicator ${isCameraActive ? 'active' : ''}`;
        }
        if (audioIndicator) {
            audioIndicator.className = `indicator audio-indicator ${isMicActive ? 'active' : ''}`;
        }
    }

    // Update local control buttons
    function updateLocalControls() {
        if (toggleCameraBtn) {
            toggleCameraBtn.innerHTML = `<i class="fas fa-video${isCameraActive ? '' : '-slash'}"></i>`;
            toggleCameraBtn.className = `control-button toggle-camera ${isCameraActive ? '' : 'off'}`;
            toggleCameraBtn.title = isCameraActive ? 'Turn off camera' : 'Turn on camera';
        }

        if (toggleMicBtn) {
            toggleMicBtn.innerHTML = `<i class="fas fa-microphone${isMicActive ? '' : '-slash'}"></i>`;
            toggleMicBtn.className = `control-button toggle-mic ${isMicActive ? '' : 'off'}`;
            toggleMicBtn.title = isMicActive ? 'Mute microphone' : 'Unmute microphone';
        }
    }

    // Initialize guest
async function initializeGuest() {
    console.log('Guest initializing devices...');
    if (!room) {
        room = episodeId;
        console.warn('Guest: No room parameter, using episodeId:', room);
    }
    let guestName = 'Guest';
    try {
        const guests = await fetchGuestsByEpisode(episodeId);
        const guest = guests.find(g => g.id === guestId);
        guestName = guest?.name || 'Guest';
    } catch (error) {
        console.error('Error fetching guest name:', error);
    }
    window.guestName = guestName;
    const success = await initializeDevices();
    if (success) {
        const joinPayload = { room, episodeId, isHost: false, user: { id: guestId, name: guestName }, token };
        console.log('Emitting join_studio with payload:', joinPayload);
        socket.emit('join_studio', joinPayload);
        showNotification('Devices initialized successfully. Joined studio.', 'success');
        updateIndicators();
        updateLocalControls();
    } else {
        showNotification('Failed to initialize devices for guest. Please check microphone and camera.', 'error');
    }
}

    // Load episode details
    async function loadEpisodeDetails() {
        try {
            const response = await fetchEpisode(episodeId);
            if (!response || !response._id) {
                throw new Error('No episode data returned');
            }
            episode = response;
            if (!room) {
                room = episodeId;
                console.warn('No room parameter in URL, using episodeId:', room);
                showNotification('Room parameter missing, using episode ID.', 'warning');
            }
            console.log('Host room:', room);
            initializeSocket(); // Set up listeners early
            await waitForSocketConnection();
            const success = await initializeDevices();
            if (success) {
                const joinPayload = { room, episodeId, isHost: true, user: { id: 'host', name: 'Host' } };
                console.log('Emitted join_studio:', joinPayload);
                socket.emit('join_studio', joinPayload);
            } else {
                showNotification('Failed to initialize devices for host. Please check microphone.', 'error');
            }
        } catch (error) {
            console.error('Error loading episode:', error);
            showNotification(`Error loading episode: ${error.message}`, 'error');
        }
    }

async function addParticipantStream(userId, streamId, guestName) {
    if (!localStream) {
        console.warn('Local stream not initialized. Delaying participant stream setup for user:', userId);
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

    const effectiveGuestName = userId === guestId ? (window.guestName || guestName) : guestName;
    console.log(`Adding participant stream for user: ${userId}, name: ${effectiveGuestName}`);

    if (connectedUsers.length <= 1) {
        if (remoteVideo) {
            const pc = new RTCPeerConnection({
                iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
            });
            peerConnections.set(userId, pc);

            pc.ontrack = (event) => {
                if (event.streams[0]) {
                    remoteVideo.srcObject = event.streams[0];
                    remoteVideoWrapper.style.display = 'block';
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
                console.log(`Setting local description for ${userId}, signalingState: ${pc.signalingState}`);
                await pc.setLocalDescription(offer);
                console.log(`Local description set for ${userId}, signalingState: ${pc.signalingState}`);

                socket.emit('offer', { room, userId, offer: pc.localDescription });

                if (pendingAnswers.has(userId)) {
                    try {
                        console.log(`Setting deferred remote answer for ${userId}, signalingState: ${pc.signalingState}`);
                        await pc.setRemoteDescription(new RTCSessionDescription(pendingAnswers.get(userId)));
                        console.log(`Deferred remote answer set for ${userId}, signalingState: ${pc.signalingState}`);
                        pendingAnswers.delete(userId);
                    } catch (e) {
                        console.error('Error setting deferred remote answer:', e);
                    }
                }
            } catch (error) {
                console.error('Error creating WebRTC offer:', error);
                showNotification('Failed to establish WebRTC connection.', 'error');
            }
        }
    } else {
        const videoElement = document.getElementById(`video-${userId}`);
        if (videoElement) {
            const pc = new RTCPeerConnection({
                iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
            });
            peerConnections.set(userId, pc);

            pc.ontrack = (event) => {
                if (event.streams[0]) {
                    videoElement.srcObject = event.streams[0];
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
                console.error('Error creating WebRTC offer for participant:', error);
                showNotification('Failed to establish WebRTC connection.', 'error');
            }
        }
    }
}

    // Load guests for episode
    async function loadGuestsForEpisode() {
        try {
            const guests = await fetchGuestsByEpisode(episodeId);
            updateParticipantsList(guests);
        } catch (error) {
            console.error('Failed to load guests:', error);
            participantsContainer.innerHTML = '<p>Error loading guests.</p>';
            showNotification('Error: Failed to load guests.', 'error');
        }
    }

    // Update participants list
    function updateParticipantsList(guests) {
        if (!participantsContainer) {
            showNotification('Error: Guest list container not found.', 'error');
            return;
        }
        participantsContainer.innerHTML = '';

        if (!guests.length) {
            participantsContainer.innerHTML = '<p>No guests found for this episode.</p>';
            return;
        }

        guests.forEach(guest => {
            const isConnected = connectedUsers.some(u => u.userId === guest._id);
            const isInGreenroom = greenroomUsers.some(u => u.userId === guest._id);
            if (connectedUsers.length > 1 && isConnected) {
                const card = document.createElement('div');
                card.className = 'participant-card';
                card.innerHTML = `
                    <h5>${guest.name}</h5>
                    <p>Status: ${isConnected ? 'In Studio' : isInGreenroom ? 'Awaiting Approval' : 'Not Connected'}</p>
                    <video id="video-${guest._id}" class="participant-video" autoplay playsinline></video>
                    <div class="audio-controls">
                        <input type="range" class="volume-slider" data-user-id="${guest._id}" min="0" max="1" step="0.1" value="1">
                        <span class="audio-indicator"></span>
                    </div>
                `;
                participantsContainer.appendChild(card);
            }
        });

        participantsContainer.style.display = connectedUsers.length > 1 ? 'block' : 'none';
    }

    // Handle WebRTC signaling
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

   const pendingAnswers = new Map();

    socket.on('answer', async (data) => {
    const { userId, answer } = data;
    const pc = peerConnections.get(userId);
    if (pc) {
        console.log(`Received answer for ${userId}, signalingState: ${pc.signalingState}`);
        if (pc.signalingState === 'have-local-offer') {
            try {
                await pc.setRemoteDescription(new RTCSessionDescription(answer));
                console.log(`setRemoteDescription(answer) succeeded for ${userId}`);
            } catch (error) {
                console.error('Error handling WebRTC answer:', error);
            }
        } else {
            // Store for later because signaling state is not ready
            console.log(`Deferring setRemoteDescription for answer from ${userId}`);
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

    socket.on('update_stream_state', (data) => {
        const { userId, isCameraActive, isMicActive } = data;
        const videoElement = document.getElementById(`video-${userId}`) || remoteVideo;
        if (videoElement) {
            videoElement.style.opacity = isCameraActive ? '1' : '0.5';
            const audioIndicator = videoElement.parentElement?.querySelector('.audio-indicator');
            if (audioIndicator) {
                audioIndicator.style.backgroundColor = isMicActive ? '#28a745' : '#dc3545';
            }
        }
    });

    // Show join request modal with proper cleanup
   // Show join request modal with proper cleanup
function showJoinRequest(guestId, guestName, episodeId, roomId) {
    console.log('Showing join request for:', { guestId, guestName, episodeId, roomId });
    if (!joinRequestModal) {
        console.error('joinRequestModal is null');
        showNotification(`Join request from ${guestName} received, but modal is unavailable.`, 'error');
        return;
    }

    // Only abort previous request if it’s for a different guest
    if (currentJoinRequest && currentJoinRequest.guestId !== guestId) {
        console.log('Cancelling previous join request for guest:', currentJoinRequest.guestId);
        currentJoinRequest.abort();
        currentJoinRequest = null;
    }

    // Create new AbortController
    currentJoinRequest = new AbortController();
    currentJoinRequest.guestId = guestId;
    const signal = currentJoinRequest.signal;
    let isApproved = false; // Track approval state

    // Update greenroom users
    greenroomUsers = greenroomUsers.filter(u => u.userId !== guestId);
    greenroomUsers.push({ userId: guestId, guestName });
    loadGuestsForEpisode();

    const modalContent = joinRequestModal.querySelector('.modal-content');
    if (!modalContent) {
        console.error('modal-content element not found');
        showNotification(`Join request from ${guestName} received, but modal content is missing.`, 'error');
        return;
    }

    // Create modal content
    modalContent.innerHTML = `
        <div class="modal-header">
            <h3>Join Request</h3>
            <button class="modal-close" style="float: right; background: none; border: none; font-size: 16px; cursor: pointer; color: var(--text-primary);" aria-label="Close">×</button>
        </div>
        <div class="modal-body">
            <p><strong>Guest:</strong> ${guestName}</p>
            <p><strong>Episode ID:</strong> ${episodeId}</p>
            <p><strong>Room:</strong> ${roomId}</p>
        </div>
        <div class="modal-footer">
            <button id="acceptJoinBtn" class="btn btn-success">Accept</button>
            <button id="denyJoinBtn" class="btn btn-danger">Deny</button>
        </div>
    `;

    // Force modal display
    console.log('Modal display before:', joinRequestModal.style.display);
    joinRequestModal.style.cssText = 'display: block !important; opacity: 1 !important; visibility: visible !important;';
    joinRequestModal.classList.add('visible');
    setTimeout(() => {
        if (joinRequestModal.style.display !== 'block') {
            console.warn('Modal display reset to none, reapplying');
            showNotification('Modal display issue detected, retrying.', 'warning');
            joinRequestModal.style.cssText = 'display: block !important; opacity: 1 !important; visibility: visible !important;';
            joinRequestModal.classList.add('visible');
        }
        console.log('Modal display after timeout:', joinRequestModal.style.display);
    }, 100);

    // Get button elements
    const acceptBtn = document.getElementById('acceptJoinBtn');
    const denyBtn = document.getElementById('denyJoinBtn');
    const closeBtn = modalContent.querySelector('.modal-close');

    if (!acceptBtn || !denyBtn || !closeBtn) {
        console.error('Modal buttons not found after creation');
        showNotification('Error: Modal buttons not available.', 'error');
        joinRequestModal.style.display = 'none';
        joinRequestModal.classList.remove('visible');
        return;
    }

    // Close modal function
    const closeModal = (isApproved = false) => {
        console.log('Closing modal for guest:', guestId);
        try {
            joinRequestModal.style.display = 'none';
            joinRequestModal.classList.remove('visible');
            if (!isApproved && currentJoinRequest) {
                currentJoinRequest.abort(); // Only abort if not approved
                currentJoinRequest = null;
            }
        } catch (error) {
            console.error('Error closing modal:', error);
        }
    };

    // Handle Accept
    const handleAccept = () => {
        console.log('Accepting join request for guest:', guestId);
        isApproved = true; // Set approval state

        // Use episodeId as fallback if roomId is undefined
        const effectiveRoomId = roomId || episodeId;

        // Defensive check for required fields
        if (!guestId || !episodeId || !effectiveRoomId) {
            console.error('Missing fields in approve_join_studio payload:', { guestId, episodeId, roomId: effectiveRoomId });
            showNotification('Error: Missing required fields for join approval.', 'error');
            closeModal(false);
            return;
        }

        try {
            const payload = {
                guestId,
                episodeId,
                roomId: effectiveRoomId,
                room: effectiveRoomId // Redundant key for legacy compatibility
            };

            console.log('Emitting approve_join_studio with payload:', JSON.stringify(payload, null, 2));

            socket.emit('approve_join_studio', payload, (response) => {
                if (response && response.error) {
                    console.error('Server rejected approve_join_studio:', response);
                    showNotification(`Error: ${response.message}`, 'error');
                    isApproved = false;
                    closeModal(false);
                } else if (response && !response.error) {
                    console.log('Approve join acknowledged by server:', response);
                    showNotification(`Approved join for ${guestName}`, 'success');
                    closeModal(true); // Pass isApproved=true
                } else {
                    console.warn('No acknowledgment received for approve_join_studio:', response);
                    showNotification('Warning: No acknowledgment from server for join approval.', 'warning');
                    closeModal(true); // Assume approval to avoid hanging modal
                }
            });
        } catch (error) {
            console.error('Error accepting join request:', error);
            showNotification('Error processing accept request.', 'error');
            isApproved = false;
            closeModal(false);
        }
    };

    // Handle Deny
    const handleDeny = () => {
        console.log('Denying join request for guest:', guestId);
        try {
            socket.emit('deny_join_studio', { guestId, reason: 'Denied by host', roomId: roomId || episodeId });
            showNotification(`Denied join for ${guestName}`, 'info');
            closeModal(false); // Pass isApproved=false
        } catch (error) {
            console.error('Error denying join request:', error);
            showNotification('Error processing deny request.', 'error');
            closeModal(false);
        }
    };

    // Add event listeners with AbortController
    acceptBtn.addEventListener('click', handleAccept, { signal });
    denyBtn.addEventListener('click', handleDeny, { signal });
    closeBtn.addEventListener('click', handleDeny, { signal });

    // Handle escape key
    const handleEscape = (e) => {
        if (e.key === 'Escape') {
            console.log('Escape key pressed, closing modal');
            handleDeny();
        }
    };
    document.addEventListener('keydown', handleEscape, { signal });

    // Handle click outside modal
    const handleClickOutside = (e) => {
        if (e.target === joinRequestModal) {
            console.log('Clicked outside modal, closing');
            handleDeny();
        }
    };
    joinRequestModal.addEventListener('click', handleClickOutside, { signal });

    // Handle abort
    signal.addEventListener('abort', () => {
        console.log('Join request aborted for guest:', guestId);
        if (isApproved) {
            console.log('Abort ignored: guest already approved');
            return;
        }
        try {
            if (joinRequestModal.style.display === 'block') {
                joinRequestModal.style.display = 'none';
                joinRequestModal.classList.remove('visible');
            }
            socket.emit('deny_join_studio', { guestId, reason: 'Join request cancelled or timed out', roomId: roomId || episodeId });
            greenroomUsers = greenroomUsers.filter(u => u.userId !== guestId);
            loadGuestsForEpisode();
        } catch (error) {
            console.error('Error during abort cleanup:', error);
        }
    }, { once: true });

    console.log(`Join request modal shown for guest: ${guestName} (ID: ${guestId})`);
}


        function closeJoinRequestModal() {
        if (currentJoinRequest) {
            console.log('Closing current join request modal');
            currentJoinRequest.abort();
            currentJoinRequest = null;
        }
    }

function initializeSocket() {
    // Map to keep track of leave timeouts per user
    const leaveTimeouts = new Map();

    // Event Handlers
    function onConnect() {
    console.log('Socket.IO connected:', socket.id);
    showNotification('Connected to server', 'success');
    socket.emit('log_connection', { userId: guestId || 'host', socketId: socket.id, role: isHost ? 'host' : 'guest' });
}

    function onReconnectAttempt(attempt) {
        console.log(`Socket.IO reconnect attempt: ${attempt}`);
    }

    function onConnectError() {
        console.error('Socket.IO connection error');
        showNotification('Failed to connect to server.', 'error');
    }

    function onStudioJoined(data) {
        console.log('Joined studio room:', data);
        loadGuestsForEpisode();
    }

    function onParticipantLeft(data) {
        console.log('Participant left:', data);

        // Clear existing timeout if any
        if (leaveTimeouts.has(data.userId)) {
            clearTimeout(leaveTimeouts.get(data.userId));
        }

        // Debounce 3 seconds to allow quick reconnects
        leaveTimeouts.set(data.userId, setTimeout(() => {
            leaveTimeouts.delete(data.userId);

            connectedUsers = connectedUsers.filter(u => u.userId !== data.userId);

            const pc = peerConnections.get(data.userId);
            if (pc) {
                pc.close();
                peerConnections.delete(data.userId);
            }

            remoteVideoWrapper.style.display = 'none';
            remoteVideo.srcObject = null;

            loadGuestsForEpisode();
        }, 3000));
    }

        function onParticipantJoined(data) {
        console.log('Participant joined:', JSON.stringify(data));
        if (leaveTimeouts.has(data.userId)) {
            clearTimeout(leaveTimeouts.get(data.userId));
            leaveTimeouts.delete(data.userId);
        }
        if (connectedUsers.some(u => u.userId === data.userId)) {
            console.log(`Participant ${data.userId} already in connectedUsers, updating`);
            connectedUsers = connectedUsers.map(u => u.userId === data.userId ? { userId: data.userId, streamId: data.streamId, guestName: data.guestName } : u);
        } else {
            connectedUsers.push({
                userId: data.userId,
                streamId: data.streamId,
                guestName: data.guestName
            });
        }
        greenroomUsers = greenroomUsers.filter(u => u.userId !== data.userId);
        addParticipantStream(data.userId, data.streamId, data.guestName);
        loadGuestsForEpisode();
        remoteVideoWrapper.style.display = 'block';
    }

   async function onJoinStudioApproved(data) {
    console.log('Join studio approved:', data);
    const room = data.room;
    const episodeId = data.episodeId;
    const guestName = data.guestName || 'Guest';
    socket.emit('join_studio', {
        room,
        episodeId,
        user: { id: guestId, name: guestName },
        isHost: false
    });
    remoteVideoWrapper.style.display = 'block';
}

    function onParticipantStream(data) {
        console.log('Received participant stream:', data);
        addParticipantStream(data.userId, data.streamId, data.guestName);
    }

    function onRequestJoinStudio(data) {
        console.log('Received request_join_studio with data:', JSON.stringify(data, null, 2));
        if (isHost) {
            console.log('Host processing join request for:', data.guestName);

            const roomId = data.roomId || data.room || data.episodeId;
            if (!roomId) {
                console.error('No roomId provided in request_join_studio:', data);
                showNotification('Error: Missing room ID for join request.', 'error');
                return;
            }

            showJoinRequest(data.guestId, data.guestName, data.episodeId, roomId);
        } else {
            console.log('Ignoring request_join_studio: not host');
        }
    }

    function onRecordingStarted(data) {
        console.log('Received recording_started event:', data);

        if (!recordingTime) {
            console.error('recordingTime DOM element not found for guest');
            showNotification('Error: Timer display not available.', 'error');
            return;
        }

        isRecording = true;
        recordingStartTime = data.recordingStartTime || Date.now();
        totalPausedTime = 0;
        isPaused = false;

        if (timerInterval) {
            clearInterval(timerInterval);
        }

        timerInterval = setInterval(() => {
            updateRecordingTime();
        }, 1000);

        if (!isHost) {
            showNotification('Recording started by host.', 'success');
            pauseButton.disabled = true;
            stopRecordingBtn.disabled = true;
            saveRecordingBtn.disabled = true;
            discardRecordingBtn.disabled = true;
        }
    }

    function onRecordingPaused(data) {
        console.log('Recording pause state changed:', data);

        isPaused = data.isPaused;
        if (isPaused) {
            pauseStartTime = Date.now();
        } else if (pauseStartTime) {
            totalPausedTime += Date.now() - pauseStartTime;
            pauseStartTime = null;
        }

        if (pauseButton) {
            pauseButton.innerHTML = `<i class="fas fa-${isPaused ? 'play' : 'pause'}"></i> ${isPaused ? 'Resume' : 'Pause'}`;
        }

        showNotification(isPaused ? 'Recording paused by host' : 'Recording resumed by host.', 'success');
    }

    function onRecordingStopped(data) {
        console.log('Recording stopped by host:', data);

        isRecording = false;
        isPaused = false;

        clearInterval(timerInterval);
        if (recordingTime) {
            recordingTime.textContent = '00:00:00';
        }

        showNotification('Recording stopped by host.', 'success');

        if (!isHost) {
            pauseButton.disabled = true;
            stopRecordingBtn.disabled = true;
            saveRecordingBtn.disabled = true;
            discardRecordingBtn.disabled = true;
        }
    }

    function onError(data) {
        console.error('Server error:', data);
        showNotification(`Error: ${data.message}`, 'error');
    }

    // Helper for leaving green room
   function leaveGreenRoom() {
    return new Promise((resolve) => {
        console.log('Leaving green room...');
        socket.emit('leave_green_room', { userId: guestId, room });

        socket.once('left_green_room', (data) => {
            if (data.userId === guestId) {
                console.log('Confirmed left green room');
                resolve();
            }
        });

        // Fallback timeout
        setTimeout(() => {
            console.warn('No confirmation for leaving green room, continuing anyway');
            resolve();
        }, 2000);
    });
}

    // Attach all event listeners
    socket.on('connect', onConnect);
    socket.on('reconnect_attempt', (attempt) => {
    console.log(`Socket.IO reconnect attempt: ${attempt}`);
    showNotification(`Reconnecting to server (attempt ${attempt})`, 'info');
});
    socket.on('connect_error', onConnectError);
    socket.on('studio_joined', onStudioJoined);
    socket.on('participant_left', onParticipantLeft);
    socket.on('participant_joined', onParticipantJoined);
    socket.on('join_studio_approved', onJoinStudioApproved);
    socket.on('participant_stream', onParticipantStream);
    socket.on('request_join_studio', onRequestJoinStudio);
    socket.on('recording_started', onRecordingStarted);
    socket.on('recording_paused', onRecordingPaused);
    socket.on('recording_stopped', onRecordingStopped);
    socket.on('error', onError);

    // Return cleanup function
    return () => {
        socket.off('connect', onConnect);
        socket.off('reconnect_attempt', onReconnectAttempt);
        socket.off('connect_error', onConnectError);
        socket.off('studio_joined', onStudioJoined);
        socket.off('participant_left', onParticipantLeft);
        socket.off('participant_joined', onParticipantJoined);
        socket.off('join_studio_approved', onJoinStudioApproved);
        socket.off('participant_stream', onParticipantStream);
        socket.off('request_join_studio', onRequestJoinStudio);
        socket.off('recording_started', onRecordingStarted);
        socket.off('recording_paused', onRecordingPaused);
        socket.off('recording_stopped', onRecordingStopped);
        socket.off('error', onError);

        // Clear all leave timeouts
        leaveTimeouts.forEach(timeout => clearTimeout(timeout));
        leaveTimeouts.clear();
    };
}

    // Event Listeners
 startRecordingBtn?.addEventListener('click', () => {
    if (!localStream) {
        showNotification('Cannot start recording: No audio stream available.', 'error');
        return;
    }
    recordedChunks = [];
    try {
        // Define supported MIME types in order of preference
        const supportedMimeTypes = [
            'audio/webm;codecs=opus',
            'audio/ogg;codecs=opus',
            'audio/mp4',
            'audio/webm',
            'audio/ogg'
        ];

        let selectedMimeType = '';
        for (const mimeType of supportedMimeTypes) {
            if (MediaRecorder.isTypeSupported(mimeType)) {
                selectedMimeType = mimeType;
                console.log(`[Host] Selected MIME type: ${mimeType}`);
                break;
            }
        }

        if (!selectedMimeType) {
            throw new Error('No supported audio MIME type found for MediaRecorder.');
        }

        const options = { mimeType: selectedMimeType };
        mediaRecorder = new MediaRecorder(localStream, options);
        mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) {
                recordedChunks.push(e.data);
            }
        };
        mediaRecorder.start(1000); // Collect data every second
        isRecording = true;
        recordingStartTime = Date.now(); // Removed await
        timerInterval = setInterval(updateRecordingTime, 1000);
        socket.emit('recording_started', { 
            room, // Fixed roomId to room as per original code
            user: { id: 'host' }, 
            recordingStartTime
        });
        console.log('[Host] Emitting recording_started event');
        if (isHost) {
            console.log('[Host] Showing host-specific notification');
            showNotification('Recording started successfully.', 'success');
        }
        pauseButton.disabled = false;
        stopRecordingBtn.disabled = false;
        saveRecordingBtn.disabled = true;
        discardRecordingBtn.disabled = true;
    } catch (error) {
        console.error('[Host] Error starting MediaRecorder:', error);
        showNotification(`Failed to start recording: ${error.message}`, 'error');
    }
});

    pauseButton?.addEventListener('click', () => {
        isPaused = !isPaused;
        if (isPaused) {
            pauseStartTime = Date.now();
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.pause();
            }
        } else {
            totalPausedTime += Date.now() - pauseStartTime;
            pauseStartTime = null;
            if (mediaRecorder && mediaRecorder.state === 'paused') {
                mediaRecorder.resume();
            }
        }
        pauseButton.innerHTML = `<i class="fas fa-${isPaused ? 'play' : 'pause'}"></i> ${isPaused ? 'Resume' : 'Pause'}`;
        socket.emit('recording_paused', { room, isPaused, user: { id: 'host' } });
        showNotification(isPaused ? 'Recording paused' : 'Recording resumed.', 'success');
    });

    stopRecordingBtn?.addEventListener('click', () => {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        }
        isRecording = false;
        isPaused = false;
        clearInterval(timerInterval);
        recordingTime.textContent = '00:00:00';
        socket.emit('recording_stopped', { room, user: { id: 'host' } });
        showNotification('Recording stopped successfully.', 'success');
        pauseButton.disabled = true;
        stopRecordingBtn.disabled = true;
        saveRecordingBtn.disabled = false;
        discardRecordingBtn.disabled = false;
    });

saveRecordingBtn?.addEventListener('click', async () => {
    try {
        if (recordedChunks.length === 0) {
            throw new Error('No recorded audio available');
        }

        const mimeType = mediaRecorder.mimeType || 'audio/webm';
        const audioBlob = new Blob(recordedChunks, { type: mimeType });

        const formData = new FormData();
        formData.append('audioFile', audioBlob, `recording.${mimeType.split('/')[1] || 'webm'}`);
        formData.append('status', 'Recorded');

        if (!episodeId) throw new Error('Invalid episode ID');

        const response = await updateEpisode(episodeId, formData);

        if (response && !response.error) {
            socket.emit('save_recording', { room, episodeId });
            showNotification('Recording saved successfully.', 'success');
            saveRecordingBtn.disabled = true;
            discardRecordingBtn.disabled = true;
            recordedChunks = [];
        } else {
            throw new Error(response?.error || 'Failed to update episode');
        }
    } catch (error) {
        console.error('Error saving recording:', error);
        showNotification(`Failed to save recording: ${error.message}`, 'error');
    }
});


    discardRecordingBtn?.addEventListener('click', () => {
        socket.emit('discard_recording', { room, episodeId });
        showNotification('Recording discarded successfully.');
        saveRecordingBtn.disabled = true;
        discardRecordingBtn.disabled = false;
        recordedChunks = []; // Clear chunks
    });

    cameraSelect?.addEventListener('change', (e) => {
        if (isCameraActive) {
            startCamera(e.target.value);
        }
    });

    microphoneSelect?.addEventListener('change', (e) => {
        if (isMicActive) {
            tryInitializeMicrophone(e.target.value);
        }
    });

    if (isHost) {
        speakerSelect?.addEventListener('change', (e) => {
            showNotification('Speaker selection changed. Note: Browser support for speaker selection may be limited.', 'info');
        });

        videoQualitySelect?.addEventListener('change', () => {
            if (isCameraActive) {
                startCamera(cameraSelect?.value);
            }
        });
    }


    speakerSelect?.addEventListener('change', (e) => {
    showNotification('Speaker selection changed. Note: Browser support for speaker selection may be limited.', 'info');
    // Attempt to set audio output (browser support varies)
    if (remoteVideo && typeof remoteVideo.setSinkId === 'function') {
        remoteVideo.setSinkId(e.target.value).catch(error => {
            console.error('Error setting audio output device:', error);
            showNotification('Failed to set speaker: Not supported by browser.', 'warning');
        });
    } else {
        console.warn('Audio output selection not supported by browser.');
    }
});

    toggleCameraBtn?.addEventListener('click', toggleCamera);
    toggleMicBtn?.addEventListener('click', toggleMicrophone);

    // Initialize
    if (episodeId) {
        console.log('Starting studio initialization');
        if (guestId && token) {
            initializeGuest();
        } else {
            loadEpisodeDetails();
        }
    } else {
        console.error('No episodeId provided in URL');
        showNotification('Error: No episode specified.', 'error');
    }
});