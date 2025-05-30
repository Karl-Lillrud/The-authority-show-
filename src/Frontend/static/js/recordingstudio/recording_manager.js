// src/Frontend/static/js/recordingstudio/recording_manager.js
import { showNotification } from '../components/notifications.js';
import { updateEpisode } from '../../../static/requests/episodeRequest.js';

export function updateRecordingTime(domElements, isRecording, isPaused, recordingStartTime, totalPausedTime = 0) {
    const { recordingTime } = domElements;
    if (!recordingTime) {
        console.error('recordingTime DOM element not found');
        return;
    }
    if (isRecording && !isPaused && recordingStartTime) {
        const elapsed = Date.now() - recordingStartTime - totalPausedTime;
        const hours = Math.floor(elapsed / 3600000);
        const minutes = Math.floor((elapsed % 3600000) / 60000);
        const seconds = Math.floor((elapsed % 60000) / 1000);
        recordingTime.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    } else {
        // Reset timer display when not recording
        recordingTime.textContent = '00:00:00';
    }
}


export function startRecording(localStream, domElements, socket, room, isHost = true, guestId = null) {
    const { pauseButton, stopRecordingBtn, saveRecordingBtn, discardRecordingBtn } = domElements;

    if (!localStream) {
        showNotification('Cannot start recording: No stream available.', 'error');
        return null;
    }

    const hasAudio = localStream.getAudioTracks().length > 0;
    const hasVideo = localStream.getVideoTracks().length > 0;

    if (!hasAudio && !hasVideo) {
        showNotification('Stream has no audio or video tracks. Cannot record.', 'error');
        return null;
    }

    // Välj MIME-typ beroende på innehåll
    const mimeOptions = [
        { type: 'video/webm;codecs=vp8,opus', requires: hasAudio && hasVideo },
        { type: 'audio/webm;codecs=opus', requires: hasAudio && !hasVideo },
        { type: 'video/webm;codecs=vp8', requires: hasVideo && !hasAudio },
        { type: 'video/webm', requires: hasVideo },
        { type: 'audio/webm', requires: hasAudio }
    ];

    const selectedMimeType = mimeOptions.find(opt =>
        opt.requires && MediaRecorder.isTypeSupported(opt.type)
    )?.type;

    if (!selectedMimeType) {
        showNotification('No supported MIME type found for recording.', 'error');
        return null;
    }

    let mediaRecorder;
    const recordedChunks = [];

    try {
        mediaRecorder = new MediaRecorder(localStream, { mimeType: selectedMimeType });
    } catch (err) {
        console.error('Failed to initialize MediaRecorder:', err);
        showNotification('Could not start recording: ' + err.message, 'error');
        return null;
    }

    mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) recordedChunks.push(e.data);
    };

    try {
        mediaRecorder.start(1000); // Capture in 1s chunks
    } catch (err) {
        console.error('Failed to start MediaRecorder:', err);
        showNotification('Could not start MediaRecorder: ' + err.message, 'error');
        return null;
    }

    const recordingStartTime = Date.now();
    const timerInterval = setInterval(() => {
        updateRecordingTime(domElements, true, false, recordingStartTime);
    }, 1000);

    if (socket && typeof socket.emit === 'function') {
        socket.emit('recording_started', {
            room,
            user: { id: isHost ? 'host' : guestId },
            recordingStartTime
        });
    } else {
        console.warn('Socket is undefined or not ready – skipping recording_started emit.');
    }

    showNotification('Recording started successfully.', 'success');

    pauseButton.disabled = false;
    stopRecordingBtn.disabled = false;
    saveRecordingBtn.disabled = true;
    discardRecordingBtn.disabled = true;

    return { mediaRecorder, recordedChunks, timerInterval, recordingStartTime };
}



export function pauseRecording(domElements, socket, room, mediaRecorder, isPaused, pauseStartTime, totalPausedTime, isHost = true, guestId = null) {
    const { pauseButton } = domElements;
    if (!mediaRecorder) {
        showNotification('Cannot pause: No active recording.', 'error');
        return null;
    }
    isPaused = !isPaused;
    if (isPaused) {
        pauseStartTime = Date.now();
        mediaRecorder.pause();
    } else {
        totalPausedTime += Date.now() - pauseStartTime;
        pauseStartTime = null;
        mediaRecorder.resume();
    }

    pauseButton.innerHTML = `<i class="fas fa-${isPaused ? 'play' : 'pause'}"></i> ${isPaused ? 'Resume' : 'Pause'}`;

    if (socket && typeof socket.emit === 'function') {
        socket.emit('recording_paused', {
            room,
            isPaused,
            user: { id: isHost ? 'host' : guestId }
        });
    }

    showNotification(isPaused ? 'Recording paused' : 'Recording resumed.', 'success');
    return { isPaused, pauseStartTime, totalPausedTime };
}


export function stopRecording(domElements, socket, room, mediaRecorder, timerInterval, isHost = true, guestId = null) {
    const { pauseButton, stopRecordingBtn, saveRecordingBtn, discardRecordingBtn, recordingTime } = domElements;

    if (!mediaRecorder || mediaRecorder.state !== 'recording') {
        showNotification('Cannot stop: No active recording.', 'error');
        return;
    }

    try {
        mediaRecorder.stop();
    } catch (err) {
        console.error('Error stopping MediaRecorder:', err);
        showNotification('Error stopping recording: ' + err.message, 'error');
        return;
    }

    clearInterval(timerInterval);
    if (recordingTime) {
        recordingTime.textContent = '00:00:00';
    }

    if (socket && typeof socket.emit === 'function') {
        socket.emit('recording_stopped', {
            room,
            user: { id: isHost ? 'host' : guestId }
        });
    } else {
        console.warn('Socket is undefined or not ready – skipping recording_stopped emit.');
    }

    showNotification('Recording stopped successfully.', 'success');

    pauseButton.disabled = true;
    stopRecordingBtn.disabled = true;
    saveRecordingBtn.disabled = false;
    discardRecordingBtn.disabled = false;
}


export async function saveRecording(recordedChunks, episodeId, socket, room) {
    if (!recordedChunks || recordedChunks.length === 0) {
        showNotification('No recorded media available', 'error');
        return;
    }

    const mimeType = recordedChunks[0]?.type || 'video/webm'; // fallback
    const audioBlob = new Blob(recordedChunks, { type: mimeType });

    const fileSizeMB = (audioBlob.size / (1024 * 1024)).toFixed(2);
    console.log(`Media blob size: ${audioBlob.size} bytes (${fileSizeMB} MB)`);
    showNotification(`Recording size: ${fileSizeMB} MB`, 'info');

    // Dynamisk filändelse baserat på MIME-typ
    const extension = mimeType.includes('webm') ? 'webm'
                    : mimeType.includes('ogg') ? 'ogg'
                    : mimeType.includes('mp4') ? 'mp4'
                    : 'webm';

    const formData = new FormData();
    formData.append('audioFile', audioBlob, `recording.${extension}`);
    formData.append('status', 'Recorded');

    try {
        const response = await updateEpisode(episodeId, formData);
        if (response && !response.error) {
            if (socket && typeof socket.emit === 'function') {
                socket.emit('save_recording', { room, episodeId });
            }
            showNotification('Recording saved successfully.', 'success');
        } else {
            showNotification(`Failed to save recording: ${response?.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        showNotification(`Failed to save recording: ${error.message}`, 'error');
    }
}



export function discardRecording(recordedChunks, episodeId, socket, room, isHost = true, guestId = null) {
    if (socket && typeof socket.emit === 'function') {
        socket.emit('discard_recording', {
            room,
            episodeId,
            user: { id: isHost ? 'host' : guestId }
        });
    }
    showNotification('Recording discarded successfully.', 'success');
}
