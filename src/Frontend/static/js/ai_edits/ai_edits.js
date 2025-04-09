function showTab(tabName) {
    const content = document.getElementById('content');
    content.innerHTML = ''; // Clear existing content

    if (tabName === 'transcription') {
        content.innerHTML = `
            <h2>🎙 AI-Powered Transcription</h2>
            <input type="file" id="fileUploader" accept="audio/*,video/*">
            <button onclick="transcribe()">Transcribe</button>
            <div id="transcriptionResult"></div>
        `;
    } else if (tabName === 'audio') {
        content.innerHTML = `
            <h2>🎵 AI Audio Enhancement</h2>
            <input type="file" id="audioUploader" accept="audio/*">
            <button onclick="enhanceAudio()">Enhance Audio</button>
            <div id="audioResult"></div>
        `;
    } else if (tabName === 'video') {
        content.innerHTML = `
            <h2>📹 AI Video Enhancement</h2>
            <input type="file" id="videoUploader" accept="video/*">
            <button onclick="enhanceVideo()">Enhance Video</button>
            <div id="videoResult"></div>
        `;
    }
}

async function transcribe() {
    const fileInput = document.getElementById('fileUploader');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please upload a file.');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/transcribe', {
        method: 'POST',
        body: formData,
    });

    const result = await response.json();
    document.getElementById('transcriptionResult').innerText = JSON.stringify(result, null, 2);
}

async function enhanceAudio() {
    const fileInput = document.getElementById('audioUploader');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please upload an audio file.');
        return;
    }

    const formData = new FormData();
    formData.append('audio', file);

    const response = await fetch('/audio/enhancement', {
        method: 'POST',
        body: formData,
    });

    const result = await response.json();
    document.getElementById('audioResult').innerText = JSON.stringify(result, null, 2);
}

async function enhanceVideo() {
    const fileInput = document.getElementById('videoUploader');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please upload a video file.');
        return;
    }

    const formData = new FormData();
    formData.append('video', file);

    const response = await fetch('/ai_videoenhance', {
        method: 'POST',
        body: formData,
    });

    const result = await response.json();
    document.getElementById('videoResult').innerText = JSON.stringify(result, null, 2);
}
