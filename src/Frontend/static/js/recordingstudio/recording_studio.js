import { showNotification } from '../components/notifications.js';
import { fetchEpisode } from '../../../static/requests/episodeRequest.js';
import { fetchGuestsByEpisode } from '../../../static/requests/guestRequests.js';

// Initialize Socket.IO with reconnection
const socket = io({
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000
});

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
    const participantsContainer = document.getElementById('participantsContainer');
    const startRecordingBtn = document.getElementById('startRecordingBtn');
    const stopRecordingBtn = document.getElementById('stopRecordingBtn');
    const cameraSelect = document.getElementById('cameraSelect');
    const microphoneSelect = document.getElementById('microphoneSelect');
    const speakerSelect = document.getElementById('speakerSelect');
    const videoPreview = document.getElementById('videoPreview');
    const joinRequestModal = document.getElementById('joinRequestModal');

    let localStream = null;
    let episode = null;
    let isRecording = false;
    let connectedUsers = []; // Track studio participants
    let greenroomUsers = []; // Track greenroom join requests

    // Get URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const podcastId = urlParams.get('podcastId');
    const episodeId = urlParams.get('episodeId');
    let room = urlParams.get('room');

    console.log('Studio initialized with params:', { podcastId, episodeId, room });

    // Validate DOM elements
    if (!participantsContainer) {
        console.error('participantsContainer element not found in DOM');
        showNotification('Error: Guest list container not found.', 'error');
    }
    if (!joinRequestModal) {
        console.error('joinRequestModal element not found in DOM');
        showNotification('Error: Join request modal not found.', 'error');
    }

    // Initialize devices
    async function initializeDevices() {
        try {
            if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
                throw new Error('Media devices API not supported in this browser');
            }
            const devices = await navigator.mediaDevices.enumerateDevices();
            console.log('Available devices:', devices.map(d => ({ kind: d.kind, label: d.label, deviceId: d.deviceId })));

            // Populate camera options
            const videoDevices = devices.filter(device => device.kind === 'videoinput');
            cameraSelect.innerHTML = '<option value="">Select Camera</option>' +
                videoDevices.map(device => `<option value="${device.deviceId}">${device.label || `Camera ${videoDevices.indexOf(device) + 1}`}</option>`).join('');

            // Populate microphone options
            const audioDevices = devices.filter(device => device.kind === 'audioinput');
            microphoneSelect.innerHTML = '<option value="">Select Microphone</option>' +
                audioDevices.map(device => `<option value="${device.deviceId}">${device.label || `Microphone ${audioDevices.indexOf(device) + 1}`}</option>`).join('');

            // Populate speaker options
            const speakerDevices = devices.filter(device => device.kind === 'audiooutput');
            speakerSelect.innerHTML = '<option value="">Select Speaker</option>' +
                speakerDevices.map(device => `<option value="${device.deviceId}">${device.label || `Speaker ${speakerDevices.indexOf(device) + 1}`}</option>`).join('');

            if (videoDevices.length > 0) {
                await startCamera(videoDevices[0].deviceId);
            } else {
                console.warn('No cameras detected');
                showNotification('No cameras detected. You can still host the studio.', 'info');
            }
        } catch (error) {
            console.error('Error initializing devices:', error.name, error.message);
            showNotification(`Failed to initialize devices: ${error.message}. Please grant camera/microphone permissions or connect a device.`, 'error');
        }
    }

    async function startCamera(deviceId) {
        try {
            if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
                throw new Error('Camera access requires HTTPS');
            }
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
            }
            localStream = await navigator.mediaDevices.getUserMedia({
                video: { deviceId: deviceId ? { exact: deviceId } : undefined },
                audio: false
            });
            videoPreview.srcObject = localStream;
            socket.emit('participant_stream', {
                room,
                userId: 'host',
                streamId: 'stream-host',
                guestName: 'Host'
            });
        } catch (error) {
            console.error('Error starting camera:', error.name, error.message);
            showNotification(`Camera error: ${error.message}. Please allow camera access.`, 'error');
        }
    }

    async function loadEpisodeDetails() {
        try {
            console.log('Fetching episode details for:', episodeId);
            const response = await fetchEpisode(episodeId);
            console.log('fetchEpisode response:', response);
            if (!response || !response._id) {
                throw new Error('No episode data returned');
            }
            episode = response;

            if (!room) {
                room = episodeId; // Fallback to episodeId
                console.warn('No room parameter in URL, using episodeId:', room);
                showNotification('Room parameter missing, using episode ID.', 'warning');
            }

            // Wait for socket connection
            const waitForSocketConnection = () => {
                return new Promise((resolve) => {
                    if (socket.connected) {
                        resolve();
                    } else {
                        console.warn('Socket not connected, waiting for connect event');
                        socket.once('connect', () => {
                            console.log(`Socket.IO connected: ${socket.id}`);
                            resolve();
                        });
                    }
                });
            };

            await waitForSocketConnection();

            // Emit join_studio as host
            const joinPayload = {
                room,
                episodeId,
                isHost: true,
                user: {
                    id: 'host',
                    name: 'Host'
                }
            };
            socket.emit('join_studio', joinPayload);
            console.log('Emitted join_studio:', joinPayload);

            // Initialize socket listeners
            initializeSocket();
        } catch (error) {
            console.error('Error loading episode:', error.name, error.message);
            showNotification(`Error loading episode details: ${error.message}`, 'error');
        }
    }

    async function loadGuestsForEpisode() {
        try {
            const guests = await fetchGuestsByEpisode(episodeId);
            updateParticipantsList(guests, connectedUsers, greenroomUsers);
        } catch (error) {
            console.error('Failed to load guests:', error.name, error.message);
            if (participantsContainer) {
                participantsContainer.innerHTML = '<p>Error loading guests. Please try again.</p>';
            } else {
                console.error('participantsContainer is null, cannot display error message');
                showNotification('Error: Guest list container not found.', 'error');
            }
        }
    }

    function updateParticipantsList(guests, connectedUsers, greenroomUsers) {
        if (!participantsContainer) {
            console.error('participantsContainer is null, cannot update guest list');
            showNotification('Error: Guest list container not found.', 'error');
            return;
        }
        participantsContainer.innerHTML = '';

        if (!guests.length) {
            participantsContainer.innerHTML = '<p>No guests found for this episode.</p>';
            return;
        }

        guests.forEach(guest => {
            const isConnected = connectedUsers.some(u => u.userId === guest.id);
            const isInGreenroom = greenroomUsers.some(u => u.userId === guest.id);
            const card = document.createElement('div');
            card.className = 'participant-card';
            card.innerHTML = `
                <h5>${guest.name}</h5>
                <p>Status: ${isConnected ? 'In Studio' : isInGreenroom ? 'Awaiting Approval' : 'Not Connected'}</p>
                <div id="video-${guest.id}" class="video-placeholder"></div>
            `;
            participantsContainer.appendChild(card);
        });
    }

    function addParticipantStream(userId, streamId, guestName) {
        const videoElement = document.getElementById(`video-${userId}`);
        if (videoElement) {
            videoElement.innerHTML = `<p>${guestName}'s Video (Stream ID: ${streamId})</p>`;
        }
    }

    function showJoinRequest(guestId, guestName, episodeId, room) {
        greenroomUsers = greenroomUsers.filter(u => u.userId !== guestId);
        greenroomUsers.push({ userId: guestId, guestName });
        loadGuestsForEpisode(); // Refresh participant list

        if (!joinRequestModal) {
            console.error('joinRequestModal is null, cannot display join request');
            showNotification(`Join request from ${guestName} received, but modal is unavailable.`, 'error');
            return;
        }

        const modalContent = joinRequestModal.querySelector('.modal-content');
        if (!modalContent) {
            console.error('modal-content element not found in joinRequestModal');
            showNotification(`Join request from ${guestName} received, but modal content is missing.`, 'error');
            return;
        }

        modalContent.innerHTML = `
            <h3>Join Request</h3>
            <p>Guest: ${guestName}</p>
            <button id="acceptJoinBtn" class="btn btn-success">Accept</button>
            <button id="denyJoinBtn" class="btn btn-danger">Deny</button>
        `;

        joinRequestModal.style.display = 'block';

        const acceptBtn = document.getElementById('acceptJoinBtn');
        const denyBtn = document.getElementById('denyJoinBtn');

        const handleAccept = () => {
            socket.emit('approve_join_studio', { guestId, episodeId, room });
            joinRequestModal.style.display = 'none';
            greenroomUsers = greenroomUsers.filter(u => u.userId !== guestId);
            showNotification(`Approved join for ${guestName}`, 'success');
            acceptBtn.removeEventListener('click', handleAccept);
            denyBtn.removeEventListener('click', handleDeny);
        };

        const handleDeny = () => {
            socket.emit('deny_join_studio', { guestId, reason: 'Denied by host', room });
            joinRequestModal.style.display = 'none';
            greenroomUsers = greenroomUsers.filter(u => u.userId !== guestId);
            showNotification(`Denied join for ${guestName}`, 'info');
            acceptBtn.removeEventListener('click', handleAccept);
            denyBtn.removeEventListener('click', handleDeny);
        };

        acceptBtn.addEventListener('click', handleAccept);
        denyBtn.addEventListener('click', handleDeny);
    }

    function initializeSocket() {
        console.log('Initializing Socket.IO listeners');

        socket.on('connect', () => {
            console.log('Socket.IO connected:', socket.id);
        });

        socket.on('reconnect_attempt', (attempt) => {
            console.log(`Socket.IO reconnect attempt ${attempt}`);
        });

        socket.on('connect_error', (error) => {
            console.error('Socket.IO connection error:', error);
            showNotification('Failed to connect to server.', 'error');
        });

        socket.on('studio_joined', (data) => {
            console.log('Joined studio room:', data);
            showNotification(`Joined studio for episode ${data.episodeId}`, 'success');
            loadGuestsForEpisode();
        });

        socket.on('participant_joined', (data) => {
            console.log('Participant joined:', data);
            connectedUsers = connectedUsers.filter(u => u.userId !== data.userId);
            connectedUsers.push({ userId: data.userId, streamId: data.streamId, guestName: data.guestName });
            greenroomUsers = greenroomUsers.filter(u => u.userId !== data.userId);
            addParticipantStream(data.userId, data.streamId, data.guestName);
            loadGuestsForEpisode();
        });

        socket.on('participant_left', (data) => {
            console.log('Participant left:', data);
            connectedUsers = connectedUsers.filter(u => u.userId !== data.userId);
            loadGuestsForEpisode();
        });

        socket.on('participant_stream', (data) => {
            console.log('Received participant stream:', data);
            addParticipantStream(data.userId, data.streamId, data.guestName);
        });

        socket.on('request_join_studio', (data) => {
            console.log('Join request received:', data);
            showJoinRequest(data.guestId, data.guestName, data.episodeId, data.room);
        });

        socket.on('error', (data) => {
            console.error('Server error:', data);
            showNotification(`Error: ${data.message}`, 'error');
        });
    }

    // Event Listeners
    startRecordingBtn?.addEventListener('click', () => {
        isRecording = true;
        socket.emit('recording_started', { room, user: { id: 'host' } });
        showNotification('Recording started.', 'success');
    });

    stopRecordingBtn?.addEventListener('click', () => {
        isRecording = false;
        socket.emit('recording_stopped', { room, user: { id: 'host' } });
        showNotification('Recording stopped.', 'success');
    });

    cameraSelect?.addEventListener('change', (e) => {
        startCamera(e.target.value);
    });

    // Initialize
    if (episodeId) {
        console.log('Starting studio initialization');
        initializeDevices();
        loadEpisodeDetails();
    } else {
        console.error('No episodeId provided in URL');
        showNotification('Error: No episode specified.', 'error');
    }
});