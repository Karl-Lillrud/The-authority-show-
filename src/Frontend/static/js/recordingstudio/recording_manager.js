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
    }
}

export function startRecording(localStream, domElements, socket, room) {
    const { pauseButton, stopRecordingBtn, saveRecordingBtn, discardRecordingBtn } = domElements;
    if (!localStream) {
        showNotification('Cannot start recording: No audio stream available.', 'error');
        return null;
    }
    const recordedChunks = [];
    const supportedMimeTypes = ['audio/webm;codecs=opus', 'audio/ogg;codecs=opus', 'audio/mp4', 'audio/webm', 'audio/ogg'];
    const selectedMimeType = supportedMimeTypes.find(mimeType => MediaRecorder.isTypeSupported(mimeType));
    if (!selectedMimeType) {
        showNotification('No supported audio MIME type found.', 'error');
        return null;
    }
    const mediaRecorder = new MediaRecorder(localStream, { mimeType: selectedMimeType });
    mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) recordedChunks.push(e.data);
    };
    mediaRecorder.start(1000);
    const recordingStartTime = Date.now();
    const timerInterval = setInterval(() => updateRecordingTime(domElements, true, false, recordingStartTime), 1000);
    socket.emit('recording_started', { room, user: { id: 'host' }, recordingStartTime });
    showNotification('Recording started successfully.', 'success');
    pauseButton.disabled = false;
    stopRecordingBtn.disabled = false;
    saveRecordingBtn.disabled = true;
    discardRecordingBtn.disabled = true;
    return { mediaRecorder, recordedChunks, timerInterval, recordingStartTime };
}

export function pauseRecording(domElements, socket, room, mediaRecorder, isPaused, pauseStartTime, totalPausedTime) {
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
    socket.emit('recording_paused', { room, isPaused, user: { id: 'host' } });
    showNotification(isPaused ? 'Recording paused' : 'Recording resumed.', 'success');
    return { isPaused, pauseStartTime, totalPausedTime };
}

export function stopRecording(domElements, socket, room, mediaRecorder, timerInterval) {
    const { pauseButton, stopRecordingBtn, saveRecordingBtn, discardRecordingBtn, recordingTime } = domElements;
    if (!mediaRecorder) {
        showNotification('Cannot stop: No active recording.', 'error');
        return;
    }
    mediaRecorder.stop();
    clearInterval(timerInterval);
    recordingTime.textContent = '00:00:00';
    socket.emit('recording_stopped', { room, user: { id: 'host' } });
    showNotification('Recording stopped successfully.', 'success');
    pauseButton.disabled = true;
    stopRecordingBtn.disabled = true;
    saveRecordingBtn.disabled = false;
    discardRecordingBtn.disabled = false;
}

export async function saveRecording(recordedChunks, episodeId, socket, room) {
    if (recordedChunks.length === 0) {
        showNotification('No recorded audio available', 'error');
        return;
    }
    const mimeType = recordedChunks[0].type || 'audio/webm';
    const audioBlob = new Blob(recordedChunks, { type: mimeType });
    const formData = new FormData();
    formData.append('audioFile', audioBlob, `recording.${mimeType.split('/')[1] || 'webm'}`);
    formData.append('status', 'Recorded');
    try {
        const response = await updateEpisode(episodeId, formData);
        if (response && !response.error) {
            socket.emit('save_recording', { room, episodeId });
            showNotification('Recording saved successfully.', 'success');
        } else {
            showNotification(`Failed to save recording: ${response?.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        showNotification(`Failed to save recording: ${error.message}`, 'error');
    }
}

export function discardRecording(recordedChunks, episodeId, socket, room) {
    socket.emit('discard_recording', { room, episodeId });
    showNotification('Recording discarded successfully.', 'success');
}