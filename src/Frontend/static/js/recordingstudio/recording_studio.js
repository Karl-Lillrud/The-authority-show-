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
        if (hostControls) hostControls.style.display = 'flex';
    } else {
        if (hostControls) hostControls.style.display = 'none';
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
        if (isRecording && !isPaused && recordingStartTime) {
            const elapsed = Date.now() - recordingStartTime;
            const hours = Math.floor(elapsed / 3600000);
            const minutes = Math.floor((elapsed % 3600000) / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            recordingTime.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
    }

    async function initializeDevices() {
        try {
            if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
                throw new Error('MediaDevices API not supported');
            }
            const devices = await navigator.mediaDevices.enumerateDevices();
            console.log('Available devices:', devices.map(d => ({ kind: d.kind, label: d.label, deviceId: d.deviceId })));

            // Populate device selects
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

            // Only populate speakerSelect for host
            if (isHost) {
                const speakerDevices = devices.filter(device => device.kind === 'audiooutput');
                speakerSelect.innerHTML = '<option value="">Select Speaker</option>';
                if (speakerDevices.length > 0) {
                    speakerSelect.innerHTML += speakerDevices.map(device => 
                        `<option value="${device.deviceId}">${device.label || `Speaker ${speakerDevices.indexOf(device) + 1}`}</option>`
                    ).join('');
                } else {
                    speakerSelect.innerHTML += '<option value="" disabled>No speakers detected</option>';
                    showNotification('No speakers detected. Audio output may be limited.', 'warning');
                }
            }

            // Try to initialize microphone if available
            if (audioDevices.length > 0) {
                await tryInitializeMicrophone(audioDevices[0].deviceId);
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
                setTimeout(retryMicrophoneInitialization, micRetryDelay);
                return false;
            }
        } catch (error) {
            console.error('Retry failed:', error);
            setTimeout(retryMicrophoneInitialization, micRetryDelay);
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
            isMicActive = true;
            videoPreview.srcObject = null; // No video initially
            const userId = guestId || 'host';
            const streamId = guestId ? `stream-${userId}` : 'stream-host';
            const guestName = guestId ? 'Guest' : 'Host';
            socket.emit('participant_stream', { room, userId, streamId, guestName });
            updateIndicators();
            updateLocalControls();
            micRetryCount = 0; // Reset retry count on success
            showNotification('Audio devices initialized.', 'success');
        } catch (error) {
            console.error('Error initializing microphone:', error);
            localStream = null;
            showNotification(`Microphone error: ${error.message}. Retrying...`, 'error');
            await retryMicrophoneInitialization();
        }
    }

    // Initialize microphone
    async function tryInitializeMicrophone(deviceId) {
        try {
            const audioStream = await navigator.mediaDevices.getUserMedia({
                audio: { deviceId: deviceId ? { exact: deviceId } : undefined }
            });
            localStream = audioStream;
            isMicActive = true;
            videoPreview.srcObject = null; // No video initially
            const userId = guestId || 'host';
            const streamId = guestId ? `stream-${userId}` : 'stream-host';
            const guestName = guestId ? 'Guest' : 'Host';
            socket.emit('participant_stream', { room, userId, streamId, guestName });
            updateIndicators();
            updateLocalControls();
            micRetryCount = 0; // Reset retry count on success
            showNotification('Audio devices initialized.');
        } catch (error) {
            console.error('Error initializing microphone:', error);
            localStream = null; // Ensure localStream is null on failure
            showNotification(`Microphone error: ${error.message}. Retrying...`, 'error');
            await retryMicrophoneInitialization();
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
            room = episodeId; // Fallback to episodeId
            console.warn('Guest: No room parameter, using episodeId:', room);
        }
        const success = await initializeDevices();
        console.log('Device initialization success:', success);
        if (success) {
            const joinPayload = { room, episodeId, isHost: false, user: { id: guestId, name: 'Guest' }, token };
            console.log('Emitting join_studio with payload:', joinPayload);
            socket.emit('join_studio', joinPayload);
        } else {
            showNotification('Failed to initialize devices for guest. Please check microphone.', 'error');
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
                await pc.setLocalDescription(offer);
                socket.emit('offer', { room, userId, offer: pc.localDescription });
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

    // Update participant list
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

    // Add participant stream
    // Update participants list (only for more than two users)
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

        // Only show participants list if more than two users
        if (connectedUsers.length > 2) {
            guests.forEach(guest => {
                const isConnected = connectedUsers.some(u => u.userId === guest._id);
                const isInGreenroom = greenroomUsers.some(u => u.userId === guest._id);
                if (isConnected) {
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
            participantsContainer.style.display = 'block';
        } else {
            participantsContainer.style.display = 'none';
        }
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

    socket.on('answer', async (data) => {
        const { userId, answer } = data;
        const pc = peerConnections.get(userId);
        if (pc) {
            try {
                await pc.setRemoteDescription(new RTCSessionDescription(answer));
            } catch (error) {
                console.error('Error handling WebRTC answer:', error);
                showNotification('WebRTC signaling error.', 'error');
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
    const closeModal = () => {
        console.log('Closing modal for guest:', guestId);
        try {
            joinRequestModal.style.display = 'none';
            joinRequestModal.classList.remove('visible');
            if (currentJoinRequest) {
                currentJoinRequest.abort();
                currentJoinRequest = null;
            }
            greenroomUsers = greenroomUsers.filter(u => u.userId !== guestId);
            loadGuestsForEpisode();
        } catch (error) {
            console.error('Error closing modal:', error);
        }
    };

    const handleAccept = () => {
        console.log('Accepting join request for guest:', guestId);
        // Use episodeId as fallback if roomId is undefined
        const effectiveRoomId = roomId || episodeId;
        if (!guestId || !episodeId || !effectiveRoomId) {
            console.error('Missing fields in approve_join_studio payload:', { guestId, episodeId, roomId: effectiveRoomId });
            showNotification('Error: Missing required fields for join approval.', 'error');
            closeModal();
            return;
        }
        try {
            const payload = { guestId, episodeId, roomId: effectiveRoomId, room: effectiveRoomId }; // Include both roomId and room
            console.log('Emitting approve_join_studio with payload:', JSON.stringify(payload, null, 2));
            socket.emit('approve_join_studio', payload, (response) => {
                if (response && response.error) {
                    console.error('Server rejected approve_join_studio:', response);
                    showNotification(`Error: ${response.message}`, 'error');
                } else {
                    console.log('Approve join acknowledged by server:', response);
                    showNotification(`Approved join for ${guestName}`, 'success');
                    closeModal();
                }
            });
        } catch (error) {
            console.error('Error accepting join request:', error);
            showNotification('Error processing accept request.', 'error');
        }
    };

    // Handle Deny
    const handleDeny = () => {
        console.log('Denying join request for guest:', guestId);
        try {
            socket.emit('deny_join_studio', { guestId, reason: 'Denied by host', roomId: roomId || episodeId });
            showNotification(`Denied join for ${guestName}`, 'info');
            closeModal();
        } catch (error) {
            console.error('Error denying join request:', error);
            showNotification('Error processing deny request.', 'error');
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
        try {
            if (joinRequestModal.style.display === 'block') {
                joinRequestModal.style.display = 'none';
                joinRequestModal.classList.remove('visible');
            }
        } catch (error) {
            console.error('Error during abort cleanup:', error);
        }
    });

    console.log(`Join request modal shown for guest: ${guestName} (ID: ${guestId})`);
}

    // Helper function to close any open join request modal
    function closeJoinRequestModal() {
        if (currentJoinRequest) {
            console.log('Closing current join request modal');
            currentJoinRequest.abort();
            currentJoinRequest = null;
        }
    }

    // Initialize Socket.IO listeners
    function initializeSocket() {
        socket.on('connect', () => {
            console.log('Socket.IO connected:', socket.id);
            showNotification('Connected to server', 'success');
        });

        socket.on('reconnect_attempt', (attempt) => {
            console.log(`Socket.IO reconnect attempt: ${attempt}`);
        });

        socket.on('connect_error', () => {
            console.error('Socket.IO connection error');
            showNotification('Failed to connect to server.', 'error');
        });

        socket.on('studio_joined', (data) => {
            console.log('Joined studio room:', data);
            loadGuestsForEpisode();
        });

        socket.on('participant_joined', (data) => {
        console.log('Participant joined:', data);
        connectedUsers = connectedUsers.filter(u => u.userId !== data.userId);
        connectedUsers.push({ userId: data.userId, streamId: data.streamId, guestName: data.guestName });
        greenroomUsers = greenroomUsers.filter(u => u.userId !== data.userId);
        addParticipantStream(data.userId, data.streamId, data.guestName);
        loadGuestsForEpisode();
        // Ensure remote video is visible for both host and guest
        remoteVideoWrapper.style.display = 'block';
    });

        // Handle participant left
    socket.on('participant_left', (data) => {
        console.log('Participant left:', data);
        connectedUsers = connectedUsers.filter(u => u.userId !== data.userId);
        const pc = peerConnections.get(data.userId);
        if (pc) {
            pc.close();
            peerConnections.delete(data.userId);
        }
        remoteVideoWrapper.style.display = 'none'; // Hide remote video if no other participants
        remoteVideo.srcObject = null;
        loadGuestsForEpisode();
    });


    socket.on('join_studio_approved', (data) => {
        console.log('Join studio approved:', data);
        room = data.room;
        episodeId = data.episodeId;
        // Initialize guest stream and join the room
        socket.emit('participant_stream', {
            room,
            userId: guestId,
            streamId: `stream-${guestId}`,
            guestName: 'Guest'
        });
        remoteVideoWrapper.style.display = 'block'; // Ensure guest sees host's video
    });

        socket.on('participant_stream', (data) => {
            console.log('Received participant stream:', data);
            addParticipantStream(data.userId, data.streamId, data.guestName);
        });

        socket.on('join_studio', (data) => {
            console.log('Join studio request:', data);
            socket.join(data.room);
            if (!data.isHost) {
                socket.to(data.room).emit('request_join_studio', {
                    guestId: data.user.id,
                    guestName: data.user.name,
                    episodeId: data.episodeId,
                    roomId: data.room
                });
            } else {
                socket.emit('studio_joined', { episodeId: data.episodeId, room: data.room });
            }
        });

        socket.on('request_join_studio', (data) => {
            console.log('Received request_join_studio with data:', JSON.stringify(data, null, 2));
            if (isHost) {
                console.log('Host processing join request for:', data.guestName);
                // Fallback to episodeId if roomId is missing
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
        });

        socket.on('error', (data) => {
            console.error('Server error:', data);
            showNotification(`Error: ${data.message}`, 'error');
        });
    }

    // Event Listeners
    startRecordingBtn?.addEventListener('click', () => {
        if (!localStream) {
            showNotification('Cannot start recording: No audio stream available.', 'error');
            return;
        }
        isRecording = true;
        recordingStartTime = Date.now();
        timerInterval = setInterval(updateRecordingTime, 1000);
        socket.emit('recording_started', { room, user: { id: 'host' } });
        showNotification('Recording started successfully.', 'success');
        pauseButton.disabled = false;
        stopRecordingBtn.disabled = false;
        saveRecordingBtn.disabled = true;
        discardRecordingBtn.disabled = true;
    });

    pauseButton?.addEventListener('click', () => {
    isPaused = !isPaused;

    if (isPaused) {
        pauseStartTime = Date.now();
    } else {
        // Add the paused duration to totalPausedTime
        totalPausedTime += Date.now() - pauseStartTime;
        pauseStartTime = null;
    }

    pauseButton.innerHTML = `<i class="fas fa-${isPaused ? 'play' : 'pause'}"></i> ${isPaused ? 'Resume' : 'Pause'}`;
    socket.emit('recording_paused', { room, isPaused, user: { id: 'host' } });
    showNotification(isPaused ? 'Recording paused' : 'Recording resumed.', 'success');
});

    stopRecordingBtn?.addEventListener('click', () => {
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

    saveRecordingBtn?.addEventListener('click', () => {
        socket.emit('save_recording', { room, episodeId });
        showNotification('Recording saved successfully.', 'success');
        saveRecordingBtn.disabled = true;
        discardRecordingBtn.disabled = true;
    });

    discardRecordingBtn?.addEventListener('click', () => {
        socket.emit('discard_recording', { room, episodeId });
        showNotification('Recording discarded successfully.', 'info');
        saveRecordingBtn.disabled = true;
        discardRecordingBtn.disabled = true;
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
            // Implement speaker change if supported by browser
            showNotification('Speaker selection changed. Note: Browser support for speaker selection may be limited.', 'info');
        });

        videoQualitySelect?.addEventListener('change', () => {
            if (isCameraActive) {
                startCamera(cameraSelect?.value);
            }
        });
    }

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