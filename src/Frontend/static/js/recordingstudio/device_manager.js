// src/Frontend/static/js/recordingstudio/device_manager.js
import { showNotification } from '../components/notifications.js';

// Constants
const RETRY_CONFIG = {
    MAX_MIC_RETRIES: 5,
    RETRY_DELAY: 10000,
    DEVICE_CHECK_INTERVAL: 5000
};

const VIDEO_QUALITY_PRESETS = {
    '480p': { width: 640, height: 480 },
    '720p': { width: 1280, height: 720 },
    '1080p': { width: 1920, height: 1080 }
};

// Device state management
class DeviceState {
    constructor() {
        this.devices = {
            video: [],
            audio: [],
            audioOutput: []
        };
        this.selectedDevices = {
            camera: null,
            microphone: null,
            speaker: null
        };
        this.streamState = {
            isCameraActive: false,
            isMicActive: false
        };
        this.localStream = null;
        this.retryCount = 0;
    }

    updateDevices(devices) {
        this.devices.video = devices.filter(d => d.kind === 'videoinput');
        this.devices.audio = devices.filter(d => d.kind === 'audioinput');
        this.devices.audioOutput = devices.filter(d => d.kind === 'audiooutput');
    }

    setSelectedDevice(type, deviceId) {
        if (this.selectedDevices.hasOwnProperty(type)) {
            this.selectedDevices[type] = deviceId;
        }
    }

    getSelectedDevice(type) {
        return this.selectedDevices[type];
    }

    updateStreamState(updates) {
        Object.assign(this.streamState, updates);
    }
}

// Global device state
const deviceState = new DeviceState();

/**
 * Validates DOM elements and throws error if required elements are missing
 */
function validateDOMElements(domElements) {
    const required = ['cameraSelect', 'microphoneSelect', 'speakerSelect', 'videoPreview'];
    const missing = required.filter(key => !domElements[key]);
    
    if (missing.length > 0) {
        throw new Error(`Missing required DOM elements: ${missing.join(', ')}`);
    }
}

/**
 * Checks if MediaDevices API is supported
 */
function checkMediaDevicesSupport() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
        throw new Error('MediaDevices API not supported in this browser');
    }
    
    if (!navigator.mediaDevices.getUserMedia) {
        throw new Error('getUserMedia not supported in this browser');
    }
}

/**
 * Checks if HTTPS is required and available
 */
function checkSecureContext() {
    if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
        throw new Error('Media access requires HTTPS or localhost');
    }
}

/**
 * Populates a select element with device options
 */
function populateDeviceSelect(selectElement, devices, deviceType, defaultLabel) {
    if (!selectElement) return;
    
    selectElement.innerHTML = `<option value="">${defaultLabel}</option>`;
    
    if (devices.length === 0) {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = `No ${deviceType} detected`;
        option.disabled = true;
        selectElement.appendChild(option);
        return;
    }
    
    devices.forEach((device, index) => {
        const option = document.createElement('option');
        option.value = device.deviceId;
        option.textContent = device.label || `${deviceType} ${index + 1}`;
        selectElement.appendChild(option);
    });
}

/**
 * Sets up device change event listeners
 */
function setupDeviceChangeListeners(domElements, isHost, onMicrophoneInitialized) {
    if (!navigator.mediaDevices.addEventListener) return;
    
    navigator.mediaDevices.addEventListener('devicechange', async () => {
        console.log('Device change detected, refreshing device list...');
        try {
            await refreshDeviceList(domElements, isHost, onMicrophoneInitialized);
            showNotification('Device list updated', 'info');
        } catch (error) {
            console.error('Error refreshing device list:', error);
        }
    });
}


async function refreshDeviceList(domElements, isHost, onMicrophoneInitialized) {
    try {
        // Säkerställ åtkomst så att enheter kan enumreras korrekt
        await navigator.mediaDevices.getUserMedia({ audio: true });

        const devices = await navigator.mediaDevices.enumerateDevices();
        console.log('Refreshed devices:', devices.map(d => ({ kind: d.kind, label: d.label, deviceId: d.deviceId })));

        deviceState.updateDevices(devices);

        if (devices.length === 0) {
            showNotification("No media devices found. Please check your browser or device settings.", "warning");
        }

        populateDeviceSelect(domElements.cameraSelect, deviceState.devices.video, 'Camera', 'Select Camera');
        populateDeviceSelect(domElements.microphoneSelect, deviceState.devices.audio, 'Microphone', 'Select Microphone');
        populateDeviceSelect(domElements.speakerSelect, deviceState.devices.audioOutput, 'Speaker', 'Select Speaker');

        validateSelectedDevices();

        // Auto-select camera if none selected
        if (!deviceState.selectedDevices.camera && deviceState.devices.video.length > 0) {
            const defaultCamera = deviceState.devices.video[0].deviceId;
            deviceState.setSelectedDevice('camera', defaultCamera);
            domElements.cameraSelect.value = defaultCamera;
        }

        // Auto-select microphone if none selected
        if (!deviceState.selectedDevices.microphone && deviceState.devices.audio.length > 0) {
            const defaultMic = deviceState.devices.audio[0].deviceId;
            deviceState.setSelectedDevice('microphone', defaultMic);
            domElements.microphoneSelect.value = defaultMic;

            if (onMicrophoneInitialized) {
                await onMicrophoneInitialized(defaultMic);
            }
        }

        // Auto-select speaker if none selected
        if (!deviceState.selectedDevices.speaker && deviceState.devices.audioOutput.length > 0) {
            const defaultSpeaker = deviceState.devices.audioOutput[0].deviceId;
            deviceState.setSelectedDevice('speaker', defaultSpeaker);
            domElements.speakerSelect.value = defaultSpeaker;
        }

    } catch (error) {
        console.error('Error refreshing device list:', error);
        showNotification(`Could not refresh devices: ${error.message}`, 'error');
        throw error;
    }
}

function validateSelectedDevices() {
    const { camera, microphone, speaker } = deviceState.selectedDevices;

    const lostDevice = (type, selectedId, availableDevices) => {
        if (selectedId && !availableDevices.find(d => d.deviceId === selectedId)) {
            deviceState.setSelectedDevice(type, null);
            showNotification(`Previously selected ${type} is no longer available.`, 'warning');
            console.warn(`Lost ${type}: ${selectedId}`);

            // Try to fall back to first available device
            if (availableDevices.length > 0) {
                const fallback = availableDevices[0].deviceId;
                deviceState.setSelectedDevice(type, fallback);
                showNotification(`Switched to available ${type}: ${availableDevices[0].label}`, 'info');
                console.info(`Switched ${type} to fallback: ${fallback}`);
            }
        }
    };

    lostDevice('camera', camera, deviceState.devices.video);
    lostDevice('microphone', microphone, deviceState.devices.audio);
    lostDevice('speaker', speaker, deviceState.devices.audioOutput);
}


export async function initializeDevices(domElements, isHost, onMicrophoneInitialized) {
    try {
        // Steg 1: Kontrollera säker kontext
        checkSecureContext();

        // Steg 2: Försök hämta tillstånd direkt
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });

        // Steg 3: DOM-validering och stöd
        validateDOMElements(domElements);
        checkMediaDevicesSupport();

        deviceState.retryCount = 0;

        // Steg 4: Hämta alla enheter efter tillstånd beviljats
        const devices = await navigator.mediaDevices.enumerateDevices();
        console.log('Available devices:', devices.map(d => ({ kind: d.kind, label: d.label, deviceId: d.deviceId })));
        deviceState.updateDevices(devices);

        populateDeviceSelect(domElements.cameraSelect, deviceState.devices.video, 'Camera', 'Select Camera');
        populateDeviceSelect(domElements.microphoneSelect, deviceState.devices.audio, 'Microphone', 'Select Microphone');
        populateDeviceSelect(domElements.speakerSelect, deviceState.devices.audioOutput, 'Speaker', 'Select Speaker');

        if (deviceState.devices.video.length === 0) {
            showNotification('No camera detected. Video features will be limited.', 'warning');
        }
        if (deviceState.devices.audioOutput.length === 0) {
            showNotification('No speaker devices detected. Audio output features may be limited.', 'warning');
        }

        setupDeviceChangeListeners(domElements, isHost, onMicrophoneInitialized);

        // Steg 5: Initiera mikrofon (och kamera)
        const defaultMic = deviceState.devices.audio[0]?.deviceId;
        if (defaultMic) {
            deviceState.setSelectedDevice('microphone', defaultMic);
            if (onMicrophoneInitialized) {
                await onMicrophoneInitialized(defaultMic);
            }

            const defaultCamera = deviceState.devices.video[0]?.deviceId;
            if (defaultCamera) {
                deviceState.setSelectedDevice('camera', defaultCamera);
                await startCamera(defaultCamera, domElements, isHost);
            }

            return true;
        } else {
            showNotification('No valid microphone detected. Please check permissions or connect a device.', 'error');
            return await retryMicrophoneInitialization(domElements, isHost, onMicrophoneInitialized);
        }
    } catch (error) {
        console.error('Error initializing devices:', error);

        // Tydligare hantering av tillståndsproblem
        if (error.name === 'NotAllowedError' || error.name === 'SecurityError') {
            showNotification('Mikrofon- eller kameraåtkomst nekades. Kontrollera webbläsartillstånd.', 'error');
        } else {
            showNotification(`Failed to initialize devices: ${error.message}`, 'error');
        }

        return await retryMicrophoneInitialization(domElements, isHost, onMicrophoneInitialized);
    }
}


async function retryMicrophoneInitialization(domElements, isHost, onMicrophoneInitialized) {
    while (deviceState.retryCount < RETRY_CONFIG.MAX_MIC_RETRIES) {
        deviceState.retryCount++;

        const delay = RETRY_CONFIG.RETRY_DELAY * deviceState.retryCount;
        showNotification(
            `Microphone not found. Retrying in ${delay / 1000} seconds (Attempt ${deviceState.retryCount}/${RETRY_CONFIG.MAX_MIC_RETRIES}).`,
            'info'
        );

        await new Promise(resolve => setTimeout(resolve, delay));

        try {
            // Försök att begära tillstånd på nytt
            await navigator.mediaDevices.getUserMedia({ audio: true });

            // Uppdatera enhetslistan
            await refreshDeviceList(domElements, isHost, onMicrophoneInitialized);

            if (deviceState.devices.audio.length > 0) {
                const defaultMic = deviceState.devices.audio[0].deviceId;
                deviceState.setSelectedDevice('microphone', defaultMic);

                if (onMicrophoneInitialized) {
                    await onMicrophoneInitialized(defaultMic);
                }

                showNotification('Microphone detected and initialized successfully.', 'success');
                return true;
            }
        } catch (error) {
            console.warn(`Retry #${deviceState.retryCount} failed:`, error);

            if (error.name === 'NotAllowedError' || error.name === 'SecurityError') {
                showNotification(
                    'Microphone access is blocked. Please allow access in your browser settings and retry.',
                    'error'
                );
                break; // Avsluta om tillstånd nekas – användaren måste agera
            }
        }
    }

    showNotification(
        'Maximum microphone initialization attempts reached. Please check your microphone connection and permissions.',
        'error'
    );
    return false;
}


/**
 * Initialize microphone with better error handling
 */
export async function tryInitializeMicrophone(deviceId, localStream, socket, room, guestId, peerConnections) {
    try {
        if (!deviceId) {
            throw new Error('No microphone device ID provided');
        }
        
        const constraints = {
            audio: { 
                deviceId: { exact: deviceId },
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        };
        
        const audioStream = await navigator.mediaDevices.getUserMedia(constraints);
        console.log('Microphone initialized:', audioStream.getTracks());
        
        // Update device state
        deviceState.setSelectedDevice('microphone', deviceId);
        deviceState.updateStreamState({ isMicActive: true });
        
        if (localStream) {
            // Stop and remove existing audio tracks
            const existingAudioTracks = localStream.getAudioTracks();
            existingAudioTracks.forEach(track => {
                track.stop();
                localStream.removeTrack(track);
            });
            
            // Add new audio track
            audioStream.getAudioTracks().forEach(track => {
                localStream.addTrack(track);
            });
            
            deviceState.localStream = localStream;
            
            // Notify peers and update connections
            socket.emit('update_stream_state', {
            room,
            userId: isHost ? 'host' : guestId,
            videoEnabled: deviceState.streamState.isCameraActive,
            audioEnabled: deviceState.streamState.isMicActive
        });

            
            if (peerConnections) {
                await updatePeerConnections(localStream, peerConnections, socket, room, guestId);
            }
        } else {
            deviceState.localStream = audioStream;
        }
        
        showNotification('Microphone switched successfully.', 'success');
        return deviceState.localStream;
        
    } catch (error) {
        console.error('Error initializing microphone:', error);
        
        let errorMessage = 'Microphone error: ';
        if (error.name === 'NotFoundError') {
            errorMessage += 'Microphone not found or disconnected';
        } else if (error.name === 'NotAllowedError') {
            errorMessage += 'Microphone access denied. Please grant permission and try again';
        } else if (error.name === 'NotReadableError') {
            errorMessage += 'Microphone is being used by another application';
        } else {
            errorMessage += error.message;
        }
        
        showNotification(errorMessage, 'error');
        deviceState.updateStreamState({ isMicActive: false });
        
        return localStream || null;
    }
}

/**
 * Start camera with improved error handling and constraints
 */
export async function startCamera(deviceId, domElements, isHost, socket, room, guestId, peerConnections) {
    const { videoPreview, microphoneSelect, videoQualitySelect } = domElements;
    let localStream = deviceState.localStream || videoPreview?.srcObject || null;

    try {
        if (!deviceId) {
            throw new Error('No camera device ID provided');
        }

        if (!isHost && !guestId) {
            console.error('Guest is missing guestId');
            showNotification('Fel: Gäst-ID saknas. Kontrollera länken.', 'error');
            return;
        }

        checkSecureContext();

        // Stop existing video tracks
        if (localStream) {
            const existingVideoTracks = localStream.getVideoTracks();
            existingVideoTracks.forEach(track => {
                track.stop();
                localStream.removeTrack(track);
            });
        }

        // Build constraints
        const constraints = {
            video: {
                deviceId: { exact: deviceId },
                facingMode: 'user'
            },
            audio: false // We'll handle audio separately
        };

        // Apply quality settings for hosts
        if (isHost && videoQualitySelect?.value && VIDEO_QUALITY_PRESETS[videoQualitySelect.value]) {
            const quality = VIDEO_QUALITY_PRESETS[videoQualitySelect.value];
            Object.assign(constraints.video, quality);
        }

        // Add audio if microphone is selected
        if (microphoneSelect?.value) {
            constraints.audio = {
                deviceId: { exact: microphoneSelect.value },
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            };
        }

        const videoStream = await navigator.mediaDevices.getUserMedia(constraints);

        // Create or update local stream
        if (!localStream) {
            localStream = videoStream;
        } else {
            // Add new tracks to existing stream
            videoStream.getTracks().forEach(track => {
                localStream.addTrack(track);
            });
        }

        // Update video preview
        if (videoPreview) {
            videoPreview.srcObject = localStream;
        }

        // Update device state
        deviceState.setSelectedDevice('camera', deviceId);
        deviceState.updateStreamState({ isCameraActive: true });
        deviceState.localStream = localStream;

        // Notify peers and update connections
        if (socket && typeof socket.emit === 'function') {
            socket.emit('update_stream_state', {
                room,
                userId: isHost ? 'host' : guestId,
                videoEnabled: deviceState.streamState.isCameraActive,
                audioEnabled: deviceState.streamState.isMicActive
            });
        } else {
            console.warn('Socket is undefined or not ready – skipping update_stream_state emit.');
        }

        if (peerConnections) {
            await updatePeerConnections(localStream, peerConnections, socket, room, guestId);
        }

        showNotification('Camera started successfully.', 'success');
        return localStream;

    } catch (error) {
        console.error('Error starting camera:', error);

        let errorMessage = 'Camera error: ';
        if (error.name === 'NotFoundError') {
            errorMessage += 'Camera not found or disconnected';
        } else if (error.name === 'NotAllowedError') {
            errorMessage += 'Camera access denied. Please grant permission and try again';
        } else if (error.name === 'NotReadableError') {
            errorMessage += 'Camera is being used by another application';
        } else if (error.name === 'OverconstrainedError') {
            errorMessage += 'Camera does not support the requested quality settings';
        } else {
            errorMessage += error.message;
        }

        showNotification(errorMessage, 'error');
        deviceState.updateStreamState({ isCameraActive: false });

        return localStream;
    }
}


/**
 * Toggle camera on/off
 */
export async function toggleCamera(localStream, domElements, isCameraActive, isHost, socket, room, guestId, peerConnections) {
    const { videoPreview, cameraSelect } = domElements;

    try {
        if (isCameraActive) {
            // Turn off camera
            const videoTracks = localStream?.getVideoTracks() || [];
            videoTracks.forEach(track => {
                track.stop();
                if (localStream) {
                    localStream.removeTrack(track);
                }
            });

            if (videoPreview) {
                videoPreview.srcObject = localStream;
            }

            deviceState.updateStreamState({ isCameraActive: false });

            if (socket && typeof socket.emit === 'function') {
                socket.emit('update_stream_state', {
                    room,
                    userId: isHost ? 'host' : guestId,
                    videoEnabled: deviceState.streamState.isCameraActive,
                    audioEnabled: deviceState.streamState.isMicActive
                });
            } else {
                console.warn('Socket is undefined or not ready – skipping update_stream_state emit.');
            }

            if (peerConnections) {
                await updatePeerConnections(localStream, peerConnections, socket, room, guestId);
            }

            showNotification('Camera turned off.', 'info');
            return false;

        } else {
            const deviceId = cameraSelect?.value || deviceState.getSelectedDevice('camera');

            if (!deviceId) {
                showNotification('Please select a camera to enable video.', 'warning');
                return false;
            }

            const newStream = await startCamera(deviceId, domElements, isHost, socket, room, guestId, peerConnections);

            if (newStream && videoPreview) {
                videoPreview.srcObject = newStream;
                showNotification('Camera turned on.', 'success');
                return true;
            }

            return false;
        }
    } catch (error) {
        console.error('Error toggling camera:', error);
        showNotification(`Error toggling camera: ${error.message}`, 'error');
        return isCameraActive; // Return current state on error
    }
}


export async function setAudioOutput(deviceId, audioElement) {
    try {
        if (!audioElement) {
            throw new Error('No audio element provided');
        }
        
        if (!audioElement.setSinkId) {
            throw new Error('Browser does not support speaker selection');
        }
        
        if (!deviceId) {
            throw new Error('No speaker device ID provided');
        }
        
        await audioElement.setSinkId(deviceId);
        deviceState.setSelectedDevice('speaker', deviceId);
        showNotification('Speaker set successfully.', 'success');
        
    } catch (error) {
        console.error('Error setting audio output device:', error);
        
        let errorMessage = 'Failed to set speaker: ';
        if (error.message.includes('support')) {
            errorMessage += 'Browser does not support speaker selection';
        } else {
            errorMessage += error.message;
        }
        
        showNotification(errorMessage, 'error');
    }
}

export async function toggleMicrophone(localStream, domElements, isMicActive, socket, room, guestId, peerConnections) {
    const { microphoneSelect } = domElements;
    
    try {
        if (!localStream) {
            showNotification('No audio stream available. Please select a microphone.', 'error');
            return isMicActive;
        }
        
        if (isMicActive) {

            const audioTracks = localStream.getAudioTracks();
            audioTracks.forEach(track => {
                track.enabled = false;
            });
            
            deviceState.updateStreamState({ isMicActive: false });
            
            socket.emit('update_stream_state', {
            room,
            userId: isHost ? 'host' : guestId,
            videoEnabled: deviceState.streamState.isCameraActive,
            audioEnabled: deviceState.streamState.isMicActive
        });

            
            showNotification('Microphone muted.', 'info');
            return false;
            
        } else {
      
            const audioTracks = localStream.getAudioTracks();
            
            if (audioTracks.length > 0) {
 
                audioTracks.forEach(track => {
                    track.enabled = true;
                });
                
                deviceState.updateStreamState({ isMicActive: true });
                
                socket.emit('update_stream_state', {
                    room,
                    userId: isHost ? 'host' : guestId,
                    videoEnabled: deviceState.streamState.isCameraActive,
                    audioEnabled: deviceState.streamState.isMicActive
                });

                showNotification('Microphone unmuted.', 'success');
                return true;
                
            } else {

                const deviceId = microphoneSelect?.value || deviceState.getSelectedDevice('microphone');
                
                if (!deviceId) {
                    showNotification('Please select a microphone first.', 'warning');
                    return false;
                }
                
                const newStream = await tryInitializeMicrophone(deviceId, localStream, socket, room, guestId, peerConnections);
                
                if (newStream) {
                    return true;
                }
                
                return false;
            }
        }
    } catch (error) {
        console.error('Error toggling microphone:', error);
        showNotification(`Error toggling microphone: ${error.message}`, 'error');
        return isMicActive; 
    }
}

async function updatePeerConnections(localStream, peerConnections, socket, room, guestId) {
    if (!peerConnections || !socket || !room) {
        console.warn('Missing required parameters for updating peer connections');
        return;
    }
    
    try {
        const promises = [];
        
        for (const [userId, pc] of peerConnections) {
            if (pc.signalingState === 'closed') {
                console.warn(`Peer connection for ${userId} is closed, skipping update`);
                continue;
            }
            
            const promise = updateSinglePeerConnection(pc, localStream, socket, room, userId);
            promises.push(promise);
        }
        
        await Promise.allSettled(promises);
        
    } catch (error) {
        console.error('Error updating peer connections:', error);
        showNotification('Failed to update stream for some participants.', 'warning');
    }
}

async function updateSinglePeerConnection(pc, localStream, socket, room, userId) {
    try {
        const senders = pc.getSenders();
        const streamTracks = localStream.getTracks();

        for (const sender of senders) {
            if (sender.track) {
                const newTrack = streamTracks.find(track => track.kind === sender.track.kind);
                if (newTrack && newTrack !== sender.track) {
                    await sender.replaceTrack(newTrack);
                    console.log(`Replaced ${sender.track.kind} track for ${userId}`);
                }
            }
        }
        
        for (const track of streamTracks) {
            const existingSender = senders.find(sender => sender.track && sender.track.kind === track.kind);
            if (!existingSender) {
                pc.addTrack(track, localStream);
                console.log(`Added ${track.kind} track for ${userId}`);
            }
        }

        if (pc.signalingState === 'stable') {
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            socket.emit('offer', { room, userId, offer: pc.localDescription });
            console.log(`Sent new offer to ${userId}`);
        }
        
    } catch (error) {
        console.error(`Error updating peer connection for ${userId}:`, error);
        throw error;
    }
}


export function cleanup() {
    try {
        if (deviceState.localStream) {
            deviceState.localStream.getTracks().forEach(track => {
                track.stop();
            });
            deviceState.localStream = null;
        }
        
        deviceState.updateStreamState({ isCameraActive: false, isMicActive: false });
        deviceState.retryCount = 0;
        
        console.log('Device manager cleanup completed');
        
    } catch (error) {
        console.error('Error during cleanup:', error);
    }
}


export function getDeviceState() {
    return {
        devices: deviceState.devices,
        selectedDevices: deviceState.selectedDevices,
        streamState: deviceState.streamState,
        hasLocalStream: !!deviceState.localStream
    };
}