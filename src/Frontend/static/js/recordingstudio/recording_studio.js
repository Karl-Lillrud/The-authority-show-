class RecordingStudio {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.videoChunks = [];
        this.isRecording = false;
        this.isPaused = false;
        this.startTime = 0;
        this.timerInterval = null;
        this.audioContext = null;
        this.analyser = null;
        this.videoStream = null;
        this.audioStream = null;
        this.visualizerCanvas = document.getElementById('audio-visualizer');
        this.visualizerContext = this.visualizerCanvas.getContext('2d');
        this.videoPreview = document.getElementById('video-preview');
        
        this.initializeElements();
        this.initializeEventListeners();
        this.loadDevices();
    }

    initializeElements() {
        this.recordButton = document.getElementById('recordButton');
        this.pauseButton = document.getElementById('pauseButton');
        this.stopButton = document.getElementById('stopButton');
        this.saveButton = document.getElementById('saveRecording');
        this.discardButton = document.getElementById('discardRecording');
        this.timerDisplay = document.getElementById('recordingTime');
        this.levelBar = document.querySelector('.level-bar');
        this.levelValue = document.querySelector('.level-value');
        this.statusIndicator = document.querySelector('.status-indicator');
        this.statusText = document.querySelector('.status-text');
        this.inputDeviceSelect = document.getElementById('inputDevice');
        this.outputDeviceSelect = document.getElementById('outputDevice');
        this.videoDeviceSelect = document.getElementById('videoDevice');
        this.videoQualitySelect = document.getElementById('videoQuality');
        this.recordingIndicator = document.querySelector('.recording-indicator');
        this.resolutionDisplay = document.getElementById('resolution');
        this.fpsDisplay = document.getElementById('fps');
        this.bitrateDisplay = document.getElementById('bitrate');
    }

    initializeEventListeners() {
        this.recordButton.addEventListener('click', () => this.toggleRecording());
        this.pauseButton.addEventListener('click', () => this.togglePause());
        this.stopButton.addEventListener('click', () => this.stopRecording());
        this.saveButton.addEventListener('click', () => this.saveRecording());
        this.discardButton.addEventListener('click', () => this.discardRecording());
        this.videoDeviceSelect.addEventListener('change', () => this.updateVideoStream());
        this.videoQualitySelect.addEventListener('change', () => this.updateVideoStream());
    }

    async loadDevices() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const audioInputs = devices.filter(device => device.kind === 'audioinput');
            const audioOutputs = devices.filter(device => device.kind === 'audiooutput');
            const videoInputs = devices.filter(device => device.kind === 'videoinput');

            this.inputDeviceSelect.innerHTML = audioInputs
                .map(device => `<option value="${device.deviceId}">${device.label || `Microphone ${audioInputs.indexOf(device) + 1}`}</option>`)
                .join('');

            this.outputDeviceSelect.innerHTML = audioOutputs
                .map(device => `<option value="${device.deviceId}">${device.label || `Speaker ${audioOutputs.indexOf(device) + 1}`}</option>`)
                .join('');

            this.videoDeviceSelect.innerHTML = videoInputs
                .map(device => `<option value="${device.deviceId}">${device.label || `Camera ${videoInputs.indexOf(device) + 1}`}</option>`)
                .join('');

            // Initialize video stream with default device
            if (videoInputs.length > 0) {
                await this.updateVideoStream();
            }
        } catch (error) {
            console.error('Error loading devices:', error);
            this.showNotification('Error loading devices', 'error');
        }
    }

    async updateVideoStream() {
        try {
            // Stop existing stream if any
            if (this.videoStream) {
                this.videoStream.getTracks().forEach(track => track.stop());
            }

            const videoConstraints = {
                deviceId: this.videoDeviceSelect.value,
                width: { ideal: this.getVideoResolution().width },
                height: { ideal: this.getVideoResolution().height },
                frameRate: { ideal: 30 }
            };

            this.videoStream = await navigator.mediaDevices.getUserMedia({
                video: videoConstraints
            });

            this.videoPreview.srcObject = this.videoStream;
            this.updateVideoStats();
        } catch (error) {
            console.error('Error updating video stream:', error);
            this.showNotification('Error accessing camera', 'error');
        }
    }

    getVideoResolution() {
        const quality = this.videoQualitySelect.value;
        switch (quality) {
            case '1080p':
                return { width: 1920, height: 1080 };
            case '720p':
                return { width: 1280, height: 720 };
            case '480p':
                return { width: 854, height: 480 };
            default:
                return { width: 1280, height: 720 };
        }
    }

    updateVideoStats() {
        if (this.videoStream) {
            const videoTrack = this.videoStream.getVideoTracks()[0];
            const settings = videoTrack.getSettings();
            
            this.resolutionDisplay.textContent = `${settings.width}x${settings.height}`;
            this.fpsDisplay.textContent = `${settings.frameRate || 30} fps`;
            this.bitrateDisplay.textContent = `${Math.round(settings.width * settings.height * (settings.frameRate || 30) * 0.1 / 1000)} kbps`;
        }
    }

    async toggleRecording() {
        if (!this.isRecording) {
            await this.startRecording();
        } else {
            this.stopRecording();
        }
    }

    async startRecording() {
        try {
            // Get audio stream
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    deviceId: this.inputDeviceSelect.value
                }
            });

            // Combine audio and video streams
            const combinedStream = new MediaStream([
                ...this.audioStream.getTracks(),
                ...this.videoStream.getTracks()
            ]);

            // Set up audio visualization
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            const source = this.audioContext.createMediaStreamSource(this.audioStream);
            source.connect(this.analyser);
            
            this.analyser.fftSize = 2048;
            const bufferLength = this.analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);

            const drawVisualizer = () => {
                if (!this.isRecording) return;

                requestAnimationFrame(drawVisualizer);
                this.analyser.getByteFrequencyData(dataArray);

                this.visualizerContext.fillStyle = '#1f2937';
                this.visualizerContext.fillRect(0, 0, this.visualizerCanvas.width, this.visualizerCanvas.height);

                const barWidth = (this.visualizerCanvas.width / bufferLength) * 2.5;
                let barHeight;
                let x = 0;

                for (let i = 0; i < bufferLength; i++) {
                    barHeight = dataArray[i] / 2;
                    this.visualizerContext.fillStyle = `rgb(16, 185, 129)`;
                    this.visualizerContext.fillRect(x, this.visualizerCanvas.height - barHeight, barWidth, barHeight);
                    x += barWidth + 1;
                }
            };

            // Set up media recorder
            this.mediaRecorder = new MediaRecorder(combinedStream, {
                mimeType: 'video/webm;codecs=vp9,opus',
                videoBitsPerSecond: 2500000 // 2.5 Mbps
            });

            this.audioChunks = [];
            this.videoChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.videoChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                this.updateRecordingStatus('stopped');
                this.saveButton.disabled = false;
                this.discardButton.disabled = false;
                this.recordingIndicator.classList.remove('active');
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            this.startTime = Date.now();
            this.updateTimer();
            this.updateRecordingStatus('recording');
            this.updateButtonStates();
            this.recordingIndicator.classList.add('active');
            drawVisualizer();

        } catch (error) {
            console.error('Error starting recording:', error);
            this.showNotification('Error starting recording', 'error');
        }
    }

    togglePause() {
        if (!this.isPaused) {
            this.mediaRecorder.pause();
            this.isPaused = true;
            this.pauseButton.innerHTML = '<i class="fas fa-play"></i><span>Resume</span>';
            this.updateRecordingStatus('paused');
            this.recordingIndicator.classList.remove('active');
        } else {
            this.mediaRecorder.resume();
            this.isPaused = false;
            this.pauseButton.innerHTML = '<i class="fas fa-pause"></i><span>Pause</span>';
            this.updateRecordingStatus('recording');
            this.recordingIndicator.classList.add('active');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.isPaused = false;
            clearInterval(this.timerInterval);
            this.updateButtonStates();
            this.recordingIndicator.classList.remove('active');
        }
    }

    updateButtonStates() {
        this.recordButton.disabled = this.isRecording;
        this.pauseButton.disabled = !this.isRecording;
        this.stopButton.disabled = !this.isRecording;
    }

    updateTimer() {
        this.timerInterval = setInterval(() => {
            const elapsed = Date.now() - this.startTime;
            const hours = Math.floor(elapsed / 3600000);
            const minutes = Math.floor((elapsed % 3600000) / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            
            this.timerDisplay.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    updateRecordingStatus(status) {
        const statusColors = {
            'ready': '#10b981',
            'recording': '#ef4444',
            'paused': '#f59e0b',
            'stopped': '#6b7280'
        };

        const statusTexts = {
            'ready': 'Ready to Record',
            'recording': 'Recording...',
            'paused': 'Paused',
            'stopped': 'Recording Stopped'
        };

        this.statusIndicator.style.backgroundColor = statusColors[status];
        this.statusText.textContent = statusTexts[status];
    }

    async saveRecording() {
        if (this.videoChunks.length === 0) {
            this.showNotification('No recording to save', 'error');
            return;
        }

        const videoBlob = new Blob(this.videoChunks, { type: 'video/webm' });
        const formData = new FormData();
        formData.append('video', videoBlob);
        formData.append('episode_id', document.getElementById('episode-id-display').textContent);

        try {
            const response = await fetch('/api/recordings/save', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                this.showNotification('Recording saved successfully', 'success');
                this.resetRecording();
            } else {
                throw new Error('Failed to save recording');
            }
        } catch (error) {
            console.error('Error saving recording:', error);
            this.showNotification('Error saving recording', 'error');
        }
    }

    discardRecording() {
        if (confirm('Are you sure you want to discard this recording?')) {
            this.resetRecording();
            this.showNotification('Recording discarded', 'info');
        }
    }

    resetRecording() {
        this.videoChunks = [];
        this.isRecording = false;
        this.isPaused = false;
        clearInterval(this.timerInterval);
        this.timerDisplay.textContent = '00:00:00';
        this.updateRecordingStatus('ready');
        this.updateButtonStates();
        this.saveButton.disabled = true;
        this.discardButton.disabled = true;
        this.visualizerContext.clearRect(0, 0, this.visualizerCanvas.width, this.visualizerCanvas.height);
        this.recordingIndicator.classList.remove('active');
    }

    showNotification(message, type = 'info') {
        // Implement notification system here
        console.log(`${type}: ${message}`);
    }
}

// Initialize the recording studio when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new RecordingStudio();
});
