// src/Frontend/static/js/recordingstudio/device_manager.js
import { showNotification } from '../components/notifications.js';

export async function initializeDevices(domElements, isHost, onMicrophoneInitialized) {
    const { cameraSelect, microphoneSelect, speakerSelect, videoQualitySelect, videoPreview } = domElements;
    const maxMicRetries = 5;
    let micRetryCount = 0;

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
            showNotification('No camera detected. Video features will be limited.', 'warning');
        }

        // Populate microphone select
        const audioDevices = devices.filter(device => device.kind === 'audioinput');
        microphoneSelect.innerHTML = '<option value="">Select Microphone</option>';
        if (audioDevices.length > 0) {
            microphoneSelect.innerHTML += audioDevices.map(device =>
                `<option value="${device.deviceId}">${device.label || `Microphone ${audioDevices.indexOf(device) + 1}`}</option>`
            ).join('');
            await onMicrophoneInitialized(audioDevices[0].deviceId);
            if (videoDevices.length > 0) {
                await startCamera(videoDevices[0].deviceId, domElements, isHost);
            }

            // Populate speaker select
            const audioOutputDevices = devices.filter(device => device.kind === 'audiooutput');
            speakerSelect.innerHTML = '<option value="">Select Speaker</option>';
            if (audioOutputDevices.length > 0) {
                speakerSelect.innerHTML += audioOutputDevices.map(device =>
                    `<option value="${device.deviceId}">${device.label || `Speaker ${audioOutputDevices.indexOf(device) + 1}`}</option>`
                ).join('');
            } else {
                showNotification('No speaker devices detected. Audio output features may be limited.', 'warning');
            }

            return true;
        } else {
            showNotification('No microphone detected. Please connect a microphone.', 'error');
            return await retryMicrophoneInitialization(onMicrophoneInitialized);
        }
    } catch (error) {
        console.error('Error initializing devices:', error);
        showNotification(`Failed to initialize devices: ${error.message}`, 'error');
        return await retryMicrophoneInitialization(onMicrophoneInitialized);
    }
}

async function retryMicrophoneInitialization(onMicrophoneInitialized) {
    const maxMicRetries = 5;
    let micRetryCount = 0;
    const micRetryDelay = 10000;

    while (micRetryCount < maxMicRetries) {
        micRetryCount++;
        showNotification(`Microphone not found. Retrying in ${micRetryDelay / 1000} seconds (Attempt ${micRetryCount}/${maxMicRetries}).`, 'info');
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const audioDevices = devices.filter(device => device.kind === 'audioinput');
            if (audioDevices.length > 0) {
                await onMicrophoneInitialized(audioDevices[0].deviceId);
                return true;
            }
            await new Promise(resolve => setTimeout(resolve, micRetryDelay));
        } catch (error) {
            console.error('Retry failed:', error);
        }
    }
    showNotification('Max microphone initialization attempts reached.', 'error');
    return false;
}

export async function tryInitializeMicrophone(deviceId) {
    try {
        const audioStream = await navigator.mediaDevices.getUserMedia({
            audio: { deviceId: deviceId ? { exact: deviceId } : undefined }
        });
        console.log('Microphone initialized:', audioStream.getTracks());
        return audioStream;
    } catch (error) {
        console.error('Error initializing microphone:', error);
        showNotification(`Microphone error: ${error.message}`, 'error');
        return null;
    }
}

export async function startCamera(deviceId, domElements, isHost) {
    const { videoPreview, microphoneSelect, videoQualitySelect } = domElements;
    let localStream = videoPreview.srcObject;
    try {
        if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
            throw new Error('Camera access requires HTTPS');
        }
        if (localStream) {
            localStream.getTracks().filter(track => track.kind === 'video').forEach(track => track.stop());
        }
        const constraints = {
            video: { deviceId: deviceId ? { exact: deviceId } : undefined },
            audio: microphoneSelect?.value ? { deviceId: microphoneSelect.value } : false
        };
        if (isHost && videoQualitySelect?.value) {
            const quality = videoQualitySelect.value;
            constraints.video.width = quality === '1080p' ? 1920 : quality === '720p' ? 1280 : 640;
            constraints.video.height = quality === '1080p' ? 1080 : quality === '720p' ? 720 : 480;
        }
        const videoStream = await navigator.mediaDevices.getUserMedia(constraints);
        localStream = localStream || videoStream;
        videoStream.getTracks().forEach(track => localStream.addTrack(track));
        videoPreview.srcObject = localStream;
        showNotification('Camera started successfully.', 'success');
        return localStream;
    } catch (error) {
        console.error('Error starting camera:', error);
        showNotification(`Camera error: ${error.message}`, 'error');
        return localStream;
    }
}

export async function toggleCamera(localStream, domElements, isCameraActive, socket, room, guestId) {
    const { videoPreview, cameraSelect } = domElements;
    if (isCameraActive) {
        const videoTrack = localStream.getVideoTracks()[0];
        if (videoTrack) {
            videoTrack.stop();
            localStream.removeTrack(videoTrack);
            videoPreview.srcObject = localStream;
            socket.emit('update_stream_state', { room, userId: guestId || 'host', isCameraActive: false });
            return false;
        }
    } else {
        const deviceId = cameraSelect?.value || null;
        if (deviceId) {
            await startCamera(deviceId, domElements, false);
            socket.emit('update_stream_state', { room, userId: guestId || 'host', isCameraActive: true });
            return true;
        } else {
            showNotification('Please select a camera to enable video.', 'warning');
            return false;
        }
    }
}

export async function setAudioOutput(deviceId, audioElement) {
    if (!audioElement.setSinkId) {
        showNotification('Your browser does not support selecting audio output device.', 'error');
        return;
    }
    try {
        await audioElement.setSinkId(deviceId);
        showNotification('Audio output device set successfully.', 'success');
    } catch (error) {
        console.error('Error setting audio output device:', error);
        showNotification('Failed to set audio output device.', 'error');
    }
}

export function toggleMicrophone(localStream, domElements, isMicActive, socket, room) {
    const { microphoneSelect } = domElements;
    if (localStream) {
        const audioTrack = localStream.getAudioTracks()[0];
        if (audioTrack) {
            isMicActive = !isMicActive;
            audioTrack.enabled = isMicActive;
            socket.emit('update_stream_state', { room, userId: guestId || 'host', isMicActive });
            return isMicActive;
        } else if (!isMicActive && microphoneSelect?.value) {
            tryInitializeMicrophone(microphoneSelect.value);
        }
    } else {
        showNotification('No audio stream available. Please select a microphone.', 'error');
    }
    return isMicActive;
}