// src/Frontend/static/js/recordingstudio/recording_studio.js
import { showNotification } from '../components/notifications.js';
import { fetchEpisode, updateEpisode } from '../../../static/requests/episodeRequest.js';
import { fetchGuestsByEpisode } from '../../../static/requests/guestRequests.js';
import { initializeDevices, tryInitializeMicrophone, startCamera, toggleCamera, toggleMicrophone } from './device_manager.js';
import { setupWebRTC, addParticipantStream } from './webrtc_manager.js';
import { initializeSocket } from './socket_manager.js';
import { setupUI, updateIndicators, updateLocalControls, updateParticipantsList, showJoinRequest } from './ui_manager.js';
import { startRecording, pauseRecording, stopRecording, saveRecording, discardRecording } from './recording_manager.js';

document.addEventListener('DOMContentLoaded', async () => {
    // DOM Elements
    const domElements = {
        participantsContainer: document.getElementById('participantsContainer'),
        startRecordingBtn: document.getElementById('startRecordingBtn'),
        pauseButton: document.getElementById('pauseButton'),
        stopRecordingBtn: document.getElementById('stopRecordingBtn'),
        saveRecordingBtn: document.getElementById('saveRecording'),
        discardRecordingBtn: document.getElementById('discardRecording'),
        cameraSelect: document.getElementById('cameraSelect'),
        microphoneSelect: document.getElementById('microphoneSelect'),
        speakerSelect: document.getElementById('speakerSelect'),
        videoQualitySelect: document.getElementById('videoQuality'),
        videoPreview: document.getElementById('videoPreview'),
        remoteVideo: document.getElementById('remoteVideo'),
        remoteVideoWrapper: document.getElementById('remoteVideoWrapper'),
        joinRequestModal: document.getElementById('joinRequestModal'),
        toggleCameraBtn: document.getElementById('toggle-camera'),
        toggleMicBtn: document.getElementById('toggle-mic'),
        hostControls: document.getElementById('hostControls'),
        recordingTime: document.getElementById('recordingTime'),
        videoIndicator: document.getElementById('videoIndicator'),
        audioIndicator: document.getElementById('audioIndicator')
    };

    // Validate DOM elements
    const missingElements = Object.entries(domElements)
        .filter(([key, value]) => !value)
        .map(([key]) => key);
    if (missingElements.length > 0) {
        console.error('Missing required DOM elements:', missingElements);
        showNotification(`Error: Missing interface elements: ${missingElements.join(', ')}.`, 'error');
        return;
    }

    // URL Parameters
    const urlParams = new URLSearchParams(window.location.search);
    const podcastId = urlParams.get('podcastId');
    const episodeId = urlParams.get('episodeId');
    const guestId = urlParams.get('guestId');
    const token = urlParams.get('token');
    let room = urlParams.get('room');
    const isHost = !guestId || !token;

    console.log('Studio initialized with params:', { podcastId, episodeId, room, guestId, token, isHost });

    // Validate URL parameters
    if (!episodeId || (guestId && !token)) {
        console.error('Missing required URL parameters:', { episodeId, guestId, token });
        showNotification('Error: Missing required parameters.', 'error');
        return;
    }

    // Initialize Socket.IO
    const socket = io({ reconnection: true, reconnectionAttempts: 5, reconnectionDelay: 1000 });

    // State
    let localStream = null;
    let episode = null;
    let connectedUsers = [];
    let greenroomUsers = [];
    let isCameraActive = false;
    let isMicActive = false;
    let peerConnections = new Map();
    let recordedChunks = [];
    let mediaRecorder = null;
    let timerInterval = null;
    let isPaused = false;
    let pauseStartTime = null;
    let totalPausedTime = 0;
    let recordingStartTime = null;

    // Initialize Devices
    const deviceSuccess = await initializeDevices(domElements, isHost, async (deviceId) => {
        localStream = await tryInitializeMicrophone(deviceId);
        isMicActive = !!localStream;
        updateIndicators(domElements, isCameraActive, isMicActive);
        updateLocalControls(domElements, isCameraActive, isMicActive);
    });

    if (!deviceSuccess) {
        showNotification('Failed to initialize devices. Please check microphone and camera.', 'error');
        return;
    }

    // Initialize WebRTC
    setupWebRTC(socket, room, localStream, domElements, connectedUsers, peerConnections, addParticipantStream);

    // Initialize Socket
    const cleanupSocket = initializeSocket({
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
        fetchGuestsByEpisode
    });

    // Setup UI Event Listeners
    setupUI({
        domElements,
        isHost,
        guestId, // Pass guestId
        startCamera,
        toggleCamera,
        toggleMicrophone,
        startRecording: () => {
            const result = startRecording(localStream, domElements, socket, room);
            if (result) {
                ({ mediaRecorder, recordedChunks, timerInterval, recordingStartTime } = result);
            }
        },
        pauseRecording: () => {
            const result = pauseRecording(domElements, socket, room, mediaRecorder, isPaused, pauseStartTime, totalPausedTime);
            if (result) {
                ({ isPaused, pauseStartTime, totalPausedTime } = result);
            }
        },
        stopRecording: () => {
            stopRecording(domElements, socket, room, mediaRecorder, timerInterval);
            mediaRecorder = null;
            timerInterval = null;
            isPaused = false;
            pauseStartTime = null;
            totalPausedTime = 0;
            recordingStartTime = null;
        },
        saveRecording: () => {
            saveRecording(recordedChunks, episodeId, socket, room);
            recordedChunks = [];
        },
        discardRecording: () => {
            discardRecording(recordedChunks, episodeId, socket, room);
            recordedChunks = [];
        },
        localStream,
        tryInitializeMicrophone, // Pass tryInitializeMicrophone
        episodeId,
        room,
        socket,
        isCameraActive,
        isMicActive,
        setCameraActive: (value) => {
            isCameraActive = value;
            updateIndicators(domElements, isCameraActive, isMicActive);
            updateLocalControls(domElements, isCameraActive, isMicActive);
        },
        setMicActive: (value) => {
            isMicActive = value;
            updateIndicators(domElements, isCameraActive, isMicActive);
            updateLocalControls(domElements, isCameraActive, isMicActive);
        },
        updateIndicators,
        updateLocalControls
    });

    // Initialize based on role
    if (isHost) {
        try {
            episode = await fetchEpisode(episodeId);
            if (!episode || !episode._id) throw new Error('No episode data returned');
            if (!room) room = episodeId;
            socket.emit('join_studio', { room, episodeId, isHost: true, user: { id: 'host', name: 'Host' } });
        } catch (error) {
            console.error('Error loading episode:', error);
            showNotification(`Error loading episode: ${error.message}`, 'error');
        }
    } else {
        let guestName = 'Guest';
        try {
            const guests = await fetchGuestsByEpisode(episodeId);
            const guest = guests.find(g => g.id === guestId);
            guestName = guest?.name || 'Guest';
        } catch (error) {
            console.error('Error fetching guest name:', error);
        }
        window.guestName = guestName;
        socket.emit('join_studio', { room: room || episodeId, episodeId, isHost: false, user: { id: guestId, name: guestName }, token });
    }
});