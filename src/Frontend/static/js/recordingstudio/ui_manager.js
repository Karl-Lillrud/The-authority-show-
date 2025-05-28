// src/Frontend/static/js/recordingstudio/ui_manager.js
import { showNotification } from '../components/notifications.js';

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
        showNotification('Speaker selection changed. Note: Browser support for speaker selection may be limited.', 'info');
        if (remoteVideo && typeof remoteVideo.setSinkId === 'function') {
            remoteVideo.setSinkId(e.target.value).catch(error => {
                console.error('Error setting audio output device:', error);
                showNotification('Failed to set speaker: Not supported by browser.', 'warning');
            });
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
    const { participantsContainer } = domElements;
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

export function showJoinRequest(guestId, guestName, episodeId, roomId, domElements, socket, greenroomUsers, updateParticipantsList) {
    const { joinRequestModal } = domElements;
    if (!joinRequestModal) {
        showNotification(`Join request from ${guestName} received, but modal is unavailable.`, 'error');
        return;
    }
    greenroomUsers.push({ userId: guestId, guestName });
    updateParticipantsList();

    const modalContent = joinRequestModal.querySelector('.modal-content');
    modalContent.innerHTML = `
        <div class="modal-header">
            <h3>Join Request</h3>
            <button class="modal-close">×</button>
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
    joinRequestModal.style.display = 'block';
    joinRequestModal.classList.add('visible');

    const acceptBtn = document.getElementById('acceptJoinBtn');
    const denyBtn = document.getElementById('denyJoinBtn');
    const closeBtn = modalContent.querySelector('.modal-close');

    const closeModal = () => {
        joinRequestModal.style.display = 'none';
        joinRequestModal.classList.remove('visible');
    };

    const handleAccept = () => {
        socket.emit('approve_join_studio', { guestId, episodeId, roomId: roomId || episodeId }, (response) => {
            if (response && response.error) {
                showNotification(`Error: ${response.message}`, 'error');
            } else {
                showNotification(`Approved join for ${guestName}`, 'success');
                closeModal();
            }
        });
    };

    const handleDeny = () => {
        socket.emit('deny_join_studio', { guestId, reason: 'Denied by host', roomId: roomId || episodeId });
        showNotification(`Denied join for ${guestName}`, 'info');
        closeModal();
    };

    acceptBtn.addEventListener('click', handleAccept);
    denyBtn.addEventListener('click', handleDeny);
    closeBtn.addEventListener('click', handleDeny);
}