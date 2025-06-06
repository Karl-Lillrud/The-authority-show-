import { showNotification } from '../components/notifications.js';
import { fetchGuestsByEpisode } from '../../../static/requests/guestRequests.js';

export function setupUI({
    domElements,
    isHost,
    guestId,
    startCamera,
    toggleCamera,
    toggleMicrophone,
    startRecording,
    pauseRecording,
    stopRecording,
    saveRecording,
    discardRecording,
    localStream,
    tryInitializeMicrophone,
    episodeId,
    room,
    socket,
    isCameraActive,
    isMicActive,
    setCameraActive,
    setMicActive,
    updateIndicators,
    updateLocalControls
}) {
    const {
        startRecordingBtn,
        pauseButton,
        stopRecordingBtn,
        saveRecordingBtn,
        discardRecordingBtn,
        cameraSelect,
        microphoneSelect,
        speakerSelect,
        videoQualitySelect,
        toggleCameraBtn,
        toggleMicBtn,
        hostControls,
        remoteVideo
    } = domElements;

    if (isHost) {
        hostControls.style.display = 'flex';
    } else {
        cameraSelect.style.display = 'block';
        microphoneSelect.style.display = 'block';
        speakerSelect.style.display = 'block';
        toggleCameraBtn.style.display = 'block';
        toggleMicBtn.style.display = 'block';
    }

    startRecordingBtn?.addEventListener('click', startRecording);
    pauseButton?.addEventListener('click', pauseRecording);
    stopRecordingBtn?.addEventListener('click', stopRecording);
    saveRecordingBtn?.addEventListener('click', saveRecording);
    discardRecordingBtn?.addEventListener('click', discardRecording);

    cameraSelect?.addEventListener('change', (e) => {
        if (isCameraActive) startCamera(e.target.value, domElements, isHost);
    });

    microphoneSelect?.addEventListener('change', (e) => {
        if (isMicActive) tryInitializeMicrophone(e.target.value);
    });

    speakerSelect?.addEventListener('change', (e) => {
        if (remoteVideo && typeof remoteVideo.setSinkId === 'function') {
            remoteVideo.setSinkId(e.target.value)
                .then(() => {
                    showNotification('Speaker set successfully.');
                })
                .catch(error => {
                    console.error('Error setting audio output device:', error);
                    showNotification('Failed to set speaker: Not supported by browser.');
                });
        } else {
            showNotification('Failed to set speaker: Browser does not support speaker selection.');
        }
    });

    if (isHost) {
        videoQualitySelect?.addEventListener('change', () => {
            if (isCameraActive) startCamera(cameraSelect?.value, domElements, isHost);
        });
    }

    toggleCameraBtn?.addEventListener('click', () => {
        const newCameraActive = toggleCamera(localStream, domElements, isCameraActive, socket, room, guestId);
        setCameraActive(newCameraActive);
    });

    toggleMicBtn?.addEventListener('click', () => {
        const newMicActive = toggleMicrophone(localStream, domElements, isMicActive, socket, room, guestId);
        setMicActive(newMicActive);
    });
}

export function updateIndicators(domElements, isCameraActive, isMicActive) {
    const { videoIndicator, audioIndicator } = domElements;
    if (videoIndicator) videoIndicator.className = `indicator video-indicator ${isCameraActive ? 'active' : ''}`;
    if (audioIndicator) audioIndicator.className = `indicator audio-indicator ${isMicActive ? 'active' : ''}`;
}

export function updateLocalControls(domElements, isCameraActive, isMicActive) {
    const { toggleCameraBtn, toggleMicBtn } = domElements;
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

export function updateParticipantsList(guests, domElements, connectedUsers, greenroomUsers) {
    if (!domElements.participantsContainer) {
        showNotification('Error: Guest list container not found.', 'error');
        return;
    }
    domElements.participantsContainer.innerHTML = '';

    if (!guests.length) {
        domElements.participantsContainer.innerHTML = '<p>No guests found for this episode.</p>';
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
            domElements.participantsContainer.appendChild(card);

            const video = document.getElementById(`video-${guest._id}`);
            const indicator = card.querySelector('.audio-indicator');
            if (video && indicator) {
                const checkStream = setInterval(() => {
                    if (video.srcObject) {
                        clearInterval(checkStream);
                        setupAudioLevelMeter(video.srcObject, indicator);
                    }
                }, 500);
            }
        }
    });

    domElements.participantsContainer.style.display = connectedUsers.length > 1 ? 'block' : 'none';
}


function setupAudioLevelMeter(stream, indicatorElement) {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(stream);
    source.connect(analyser);

    analyser.fftSize = 256;
    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    function updateVolume() {
        analyser.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
        const volume = Math.min(100, Math.max(0, average)); // Clamp between 0-100
        indicatorElement.style.width = `${volume}%`; // E.g. width on bar, or update a class
        requestAnimationFrame(updateVolume);
    }

    updateVolume();
}


export async function showJoinRequest(guestId, guestName, episodeId, roomId, domElements, socket, greenroomUsers, updateCallback) {
    if (!domElements.joinRequestModal) {
        console.error('joinRequestModal is null');
        showNotification(`Join request from ${guestName} received, but modal is unavailable.`, 'error');
        return;
    }

    // Fetch guest name and ID
    let effectiveGuestName = guestName;
    let effectiveGuestId = guestId;
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get("token");

        const guests = await fetchGuestsByEpisode(episodeId, token);
        const guest = guests.find(g => g.id === guestId);
        effectiveGuestName = guest?.name || guestName || 'Guest';
        effectiveGuestId = guest?.id || guestId;
    } catch (error) {
        console.error('Error fetching guest name:', error);
        showNotification('Warning: Could not fetch guest name.', 'warning');
    }

    let currentJoinRequest = new AbortController();
    const signal = currentJoinRequest.signal;

    greenroomUsers = greenroomUsers.filter(u => u.userId !== effectiveGuestId);
    greenroomUsers.push({ userId: effectiveGuestId, guestName: effectiveGuestName });
    try {
        await updateCallback();
    } catch (error) {
        console.error('Error updating participants:', error);
        showNotification('Error updating participants.', 'error');
    }

    const modalContent = domElements.joinRequestModal.querySelector('.modal-content');
    if (!modalContent) {
        console.error('modal-content element not found');
        showNotification(`Join request from ${effectiveGuestName} received, but modal content is missing.`, 'error');
        return;
    }

    modalContent.innerHTML = `
        <div class="modal-header">
            <h3>Join Request</h3>
            <button class="modal-close" style="float: right; background: none; border: none; font-size: 16px; cursor: pointer; color: var(--text-primary);" aria-label="Close">×</button>
        </div>
        <div class="modal-body">
            <p><strong>Guest:</strong> ${effectiveGuestName}</p>
            <p><strong>Episode ID:</strong> ${episodeId}</p>
            <p><strong>Room:</strong> ${roomId || episodeId}</p>
        </div>
        <div class="modal-footer">
            <button id="acceptJoinBtn" class="btn btn-success">Accept</button>
            <button id="denyJoinBtn" class="btn btn-danger">Deny</button>
        </div>
    `;

    domElements.joinRequestModal.style.display = 'block';

    const acceptBtn = modalContent.querySelector('#acceptJoinBtn');
    const denyBtn = modalContent.querySelector('#denyJoinBtn');
    const closeBtn = modalContent.querySelector('.modal-close');

    const closeModal = () => {
        domElements.joinRequestModal.style.display = 'none';
        currentJoinRequest.abort();
        currentJoinRequest = null;
    };

    const handleAccept = () => {
        const effectiveRoom = roomId || episodeId;
        socket.emit('approve_join_studio', {
            guestId: effectiveGuestId,
            episodeId,
            room: effectiveRoom, // ✅ Fixed: renamed from roomId to room
            guestName: effectiveGuestName
        }, (response) => {
            if (response && response.error) {
                showNotification(`Error: ${response.message}`, 'error');
            } else {
                showNotification(`Approved join for ${effectiveGuestName}`, 'success');
                closeModal();
            }
        });
    };

    const handleDeny = () => {
        socket.emit('deny_join_studio', {
            guestId: effectiveGuestId,
            reason: 'Denied by host',
            room: roomId || episodeId // ✅ Also changed to "room" for consistency
        });
        showNotification(`Denied join for ${effectiveGuestName}`, 'info');
        closeModal();
    };

    acceptBtn.addEventListener('click', handleAccept, { signal });
    denyBtn.addEventListener('click', handleDeny, { signal });
    closeBtn.addEventListener('click', handleDeny, { signal });

    signal.addEventListener('abort', () => {
        greenroomUsers = greenroomUsers.filter(u => u.userId !== effectiveGuestId);
        updateCallback();
    });
}
