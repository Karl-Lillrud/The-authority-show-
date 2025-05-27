
import { fetchGuestsByEpisode } from '../../../static/requests/guestRequests.js';

// Initialize Socket.IO
const socket = io();

// DOM Elements
const cameraSelect = document.getElementById('cameraSelect');
const microphoneSelect = document.getElementById('microphoneSelect');
const speakerSelect = document.getElementById('speakerSelect');
const cameraPreview = document.getElementById('cameraPreview');
const audioMeter = document.querySelector('.audio-meter');
const testSpeakerButton = document.getElementById('testSpeaker');
const notificationArea = document.getElementById('notification-area');
const participantsContainer = document.getElementById('participantsContainer');
const roomStatus = document.getElementById('roomStatus');

// Variables
let localStream = null;
let audioContext = null;
let audioAnalyser = null;
let currentRoom = null;
let isConnected = false;

// Get URL parameters
const urlParams = new URLSearchParams(window.location.search);
const episodeId = urlParams.get('episodeId');
const guestId = urlParams.get('guestId');
const token = urlParams.get('token');

// Initialize devices
async function initializeDevices() {
    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        
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
            showNotification('No cameras detected. Connect a camera or proceed without video.', 'info');
        }
    } catch (error) {
        console.error('Error initializing devices:', error);
        showNotification('Error initializing devices. Check permissions or devices.', 'error');
    }
}

async function loadGuestsForEpisode(episodeId) {
    try {
        const guests = await fetchGuestsByEpisode(episodeId);
        updateParticipantsList(guests, []);
    } catch (err) {
        console.error('Failed to load guests:', err);
        participantsContainer.innerHTML = '<p>Error loading guests.</p>';
        showNotification('Error loading guests', 'error');
    }
}

// Update participant list
function updateParticipantsList(guests, connectedUsers) {
    participantsContainer.innerHTML = '';

    if (!guests.length) {
        participantsContainer.innerHTML = '<p>No guests found for this episode.</p>';
        return;
    }

    guests.forEach(guest => {
        const isConnected = connectedUsers.some(u => u.userId === guest.id);
        const card = document.createElement('div');
        card.className = 'guest-card p-3 border rounded m-2';

        if (guest.id === guestId) {
            card.classList.add('bg-light', 'border-success');
            card.innerHTML = `
                <h5>${guest.name}</h5>
                <p><strong>Email:</strong> ${guest.email || 'N/A'}</p>
                <p><strong>Status:</strong> ${isConnected ? 'In Greenroom' : 'Not Connected'}</p>
                <button class="btn btn-primary join-studio-btn" data-guest-id="${guest.id}">Request to Join Studio</button>
            `;
        } else {
            card.innerHTML = `
                <h5>${guest.name}</h5>
                <p><strong>Email:</strong> ${guest.email || 'N/A'}</p>
                <p><strong>Status:</strong> ${isConnected ? 'In Greenroom' : 'Not Connected'}</p>
            `;
        }
        participantsContainer.appendChild(card);
    });

    document.querySelectorAll('.join-studio-btn').forEach(button => {
        button.addEventListener('click', () => {
            const guestId = button.getAttribute('data-guest-id');
            if (!currentRoom) {
                showNotification('Cannot send request: Room ID missing', 'error');
                return;
            }
            socket.emit('request_join_studio', {
                room: currentRoom,
                episodeId,
                guestId,
                guestName: guests.find(g => g.id === guestId)?.name || 'Guest',
                token
            });
            console.log('Sending request_join_studio:', { room: currentRoom, episodeId, guestId, token });
            button.disabled = true;
            button.textContent = 'Request Sent';
            showNotification('Join request sent to host', 'success');
        }, { once: true });
    });
}

// Start camera
async function startCamera(deviceId) {
    try {
        if (!deviceId) {
            showNotification('No camera available. Please connect a camera.', 'error');
            return;
        }
        if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
            showNotification('Camera access requires HTTPS.', 'error');
            return;
        }
        if (localStream) {
            localStream.getTracks().forEach(track => track.stop());
        }
        localStream = await navigator.mediaDevices.getUserMedia({
            video: { deviceId: deviceId ? { exact: deviceId } : undefined },
            audio: false
        });
        cameraPreview.srcObject = localStream;
    } catch (error) {
        console.error('Error starting camera:', error.name, error.message);
        if (error.name === 'NotAllowedError') {
            showNotification('Camera permission denied. Please allow camera access in your browser settings.', 'error');
        } else if (error.name === 'NotFoundError') {
            showNotification('No camera found. Please connect a camera.', 'error');
        } else {
            showNotification(`Camera error: ${error.message}`, 'error');
        }
    }
}

// Audio analysis
function setupAudioAnalysis(stream) {
    if (audioContext) {
        audioContext.close();
    }
    audioContext = new AudioContext();
    const source = audioContext.createMediaStreamSource(stream);
    audioAnalyser = audioContext.createAnalyser();
    audioAnalyser.fftSize = 256;
    source.connect(audioAnalyser);

    const bufferLength = audioAnalyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    function updateAudioMeter() {
        audioAnalyser.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / bufferLength;
        const level = (average / 255) * 100;
        audioMeter.style.width = `${level}%`;
        requestAnimationFrame(updateAudioMeter);
    }
    updateAudioMeter();
}

// Event Listeners
cameraSelect.addEventListener('change', async (e) => {
    await startCamera(e.target.value);
});

microphoneSelect.addEventListener('change', async (e) => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: { deviceId: e.target.value ? { exact: e.target.value } : undefined }
        });
        setupAudioAnalysis(stream);
    } catch (error) {
        console.error('Error setting up microphone:', error);
        showNotification('Error setting up microphone', 'error');
    }
});

speakerSelect.addEventListener('change', (e) => {
    if (cameraPreview.srcObject) {
        cameraPreview.setSinkId(e.target.value);
    }
});

testSpeakerButton.addEventListener('click', async () => {
    try {
        const audioContext = new AudioContext();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(440, audioContext.currentTime);
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        
        oscillator.start();
        
        setTimeout(() => {
            oscillator.stop();
            audioContext.close();
        }, 1000);
    } catch (error) {
        console.error('Error testing speaker:', error);
        showNotification('Error testing speaker', 'error');
    }
});

// Socket.IO events
socket.on('connect', () => {
    if (isConnected) return;
    isConnected = true;
    console.log('Connected to server');
    currentRoom = urlParams.get('room') || episodeId;
    if (currentRoom) {
        socket.emit('join_greenroom', { 
            room: currentRoom, 
            user: { id: guestId, socketId: socket.id, name: 'Guest' }
        });
        console.log('Emitted join_greenroom:', currentRoom);
    } else {
        showNotification('Error: Room or Episode ID missing', 'error');
    }
});

socket.on('greenroom_joined', async (data) => {
    console.log('Greenroom joined:', data);
    try {
        const guests = await fetchGuestsByEpisode(episodeId);
        updateParticipantsList(guests, data.users);
    } catch (err) {
        console.error('Error fetching guests:', err);
        showNotification('Error updating participants', 'error');
    }
});

socket.on('participant_update', async (data) => {
    console.log('Participant update:', data);
    try {
        const guests = await fetchGuestsByEpisode(episodeId);
        updateParticipantsList(guests, data.users);
    } catch (err) {
        console.error('Error updating participants:', err);
        showNotification('Error updating participants', 'error');
    }
});

socket.on('host_ready', (data) => {
    roomStatus.querySelector('.status-text').textContent = 'Host is ready';
    roomStatus.querySelector('.status-indicator').classList.add('active');
});

socket.on('join_studio_approved', (data) => {
    showNotification('Join request approved! Joining studio...', 'success');
    window.location.href = `/studio?podcastId=4782487e-0305-439e-812e-879f91ac1f1b&episodeId=${data.episodeId}&room=${data.room}&guestId=${guestId}`;
});

socket.on('join_studio_denied', (data) => {
    showNotification(`Join request denied: ${data.reason || 'No reason provided'}`, 'error');
    document.querySelectorAll('.join-studio-btn').forEach(button => {
        button.disabled = false;
        button.textContent = 'Request to Join Studio';
    });
});

socket.on('request_join_studio_failed', (data) => {
    showNotification(`Request failed: ${data.reason}`, 'error');
    document.querySelectorAll('.join-studio-btn').forEach(button => {
        button.disabled = false;
        button.textContent = 'Request to Join Studio';
    });
});

socket.on('disconnect', () => {
    isConnected = false;
    console.log('Disconnected from server');
});

// Helpers
function showNotification(message, type = 'info') {
    console.log(`${type}: ${message}`);
    if (notificationArea) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.padding = '10px';
        notification.style.margin = '5px';
        notification.style.borderRadius = '4px';
        notification.style.backgroundColor = type === 'error' ? '#fee2e2' : type === 'success' ? '#d1fae5' : '#e0f2fe';
        notificationArea.appendChild(notification);
        setTimeout(() => notification.remove(), 5000);
    }
}

// Initialize
initializeDevices();
if (episodeId) {
    loadGuestsForEpisode(episodeId);
}
