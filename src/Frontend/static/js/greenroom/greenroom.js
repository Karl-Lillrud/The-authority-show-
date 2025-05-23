// Initialize Socket.IO connection
const socket = io();

// DOM Elements
const cameraSelect = document.getElementById('cameraSelect');
const microphoneSelect = document.getElementById('microphoneSelect');
const speakerSelect = document.getElementById('speakerSelect');
const cameraPreview = document.getElementById('cameraPreview');
const audioMeter = document.querySelector('.audio-meter');
const testSpeakerButton = document.getElementById('testSpeaker');
const readyButton = document.getElementById('readyButton');
const leaveButton = document.getElementById('leaveButton');
const participantsContainer = document.getElementById('participantsContainer');
const roomStatus = document.getElementById('roomStatus');

// State
let localStream = null;
let audioContext = null;
let audioAnalyser = null;
let isHost = false;
let isReady = false;
let currentRoom = null;

// Initialize device settings
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

        // Set up initial camera preview
        if (videoDevices.length > 0) {
            await startCamera(videoDevices[0].deviceId);
        }
    } catch (error) {
        console.error('Error initializing devices:', error);
    }
}

// Start camera preview
async function startCamera(deviceId) {
    try {
        if (localStream) {
            localStream.getTracks().forEach(track => track.stop());
        }

        localStream = await navigator.mediaDevices.getUserMedia({
            video: { deviceId: deviceId ? { exact: deviceId } : undefined },
            audio: false
        });

        cameraPreview.srcObject = localStream;
    } catch (error) {
        console.error('Error starting camera:', error);
    }
}

// Set up audio analysis
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
        
        oscillator.start();
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        
        setTimeout(() => {
            oscillator.stop();
            audioContext.close();
        }, 1000);
    } catch (error) {
        console.error('Error testing speaker:', error);
    }
});

readyButton.addEventListener('click', () => {
    isReady = !isReady;
    readyButton.textContent = isReady ? 'Not Ready' : 'I\'m Ready';
    readyButton.classList.toggle('btn-success');
    readyButton.classList.toggle('btn-primary');
    
    socket.emit('participant_ready', {
        room: currentRoom,
        user: {
            id: socket.id,
            isReady: isReady
        }
    });
});

leaveButton.addEventListener('click', () => {
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
    }
    if (audioContext) {
        audioContext.close();
    }
    window.location.href = '/';
});

// Socket.IO Event Handlers
socket.on('connect', () => {
    console.log('Connected to server');
    currentRoom = new URLSearchParams(window.location.search).get('room');
    if (currentRoom) {
        socket.emit('join_greenroom', { room: currentRoom });
    }
});

socket.on('greenroom_joined', (data) => {
    console.log('Joined greenroom:', data);
    updateParticipantsList(data.users);
});

socket.on('participant_ready', (data) => {
    updateParticipantStatus(data.user);
});

socket.on('host_ready', (data) => {
    roomStatus.querySelector('.status-text').textContent = 'Host is ready';
    roomStatus.querySelector('.status-indicator').classList.add('active');
});

socket.on('move_to_studio', (data) => {
    window.location.href = `/studio?room=${currentRoom}`;
});

// Helper Functions
function updateParticipantsList(users) {
    participantsContainer.innerHTML = '';
    users.forEach(user => {
        const participantCard = document.createElement('div');
        participantCard.className = 'participant-card';
        participantCard.innerHTML = `
            <div class="participant-video">
                <video autoplay muted playsinline></video>
            </div>
            <div class="participant-name">${user.name || 'Anonymous'}</div>
            <div class="participant-status">${user.isReady ? 'Ready' : 'Not Ready'}</div>
        `;
        participantsContainer.appendChild(participantCard);
    });
}

function updateParticipantStatus(user) {
    const participantCards = participantsContainer.querySelectorAll('.participant-card');
    participantCards.forEach(card => {
        const nameElement = card.querySelector('.participant-name');
        if (nameElement.textContent === (user.name || 'Anonymous')) {
            const statusElement = card.querySelector('.participant-status');
            statusElement.textContent = user.isReady ? 'Ready' : 'Not Ready';
        }
    });
}

// Initialize
initializeDevices();
