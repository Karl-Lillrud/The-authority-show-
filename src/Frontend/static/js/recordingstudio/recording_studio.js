class RecordingStudio {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.isPaused = false;
        this.startTime = 0;
        this.timerInterval = null;
        this.audioContext = null;
        this.analyser = null;
        this.visualizerCanvas = document.getElementById('audio-visualizer');
        this.visualizerContext = this.visualizerCanvas.getContext('2d');
        
        this.initializeElements();
        this.initializeEventListeners();
        this.loadAudioDevices();
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
    }

    initializeEventListeners() {
        this.recordButton.addEventListener('click', () => this.toggleRecording());
        this.pauseButton.addEventListener('click', () => this.togglePause());
        this.stopButton.addEventListener('click', () => this.stopRecording());
        this.saveButton.addEventListener('click', () => this.saveRecording());
        this.discardButton.addEventListener('click', () => this.discardRecording());
        this.inputDeviceSelect.addEventListener('change', () => this.updateAudioDevices());
    }

    async loadAudioDevices() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const audioInputs = devices.filter(device => device.kind === 'audioinput');
            const audioOutputs = devices.filter(device => device.kind === 'audiooutput');

            this.inputDeviceSelect.innerHTML = audioInputs
                .map(device => `<option value="${device.deviceId}">${device.label || `Microphone ${audioInputs.indexOf(device) + 1}`}</option>`)
                .join('');

            this.outputDeviceSelect.innerHTML = audioOutputs
                .map(device => `<option value="${device.deviceId}">${device.label || `Speaker ${audioOutputs.indexOf(device) + 1}`}</option>`)
                .join('');
        } catch (error) {
            console.error('Error loading audio devices:', error);
            this.showNotification('Error loading audio devices', 'error');
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
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    deviceId: this.inputDeviceSelect.value
                }
            });

            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            const source = this.audioContext.createMediaStreamSource(stream);
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

            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                this.updateRecordingStatus('stopped');
                this.saveButton.disabled = false;
                this.discardButton.disabled = false;
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            this.startTime = Date.now();
            this.updateTimer();
            this.updateRecordingStatus('recording');
            this.updateButtonStates();
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
        } else {
            this.mediaRecorder.resume();
            this.isPaused = false;
            this.pauseButton.innerHTML = '<i class="fas fa-pause"></i><span>Pause</span>';
            this.updateRecordingStatus('recording');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.isPaused = false;
            clearInterval(this.timerInterval);
            this.updateButtonStates();
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
        if (this.audioChunks.length === 0) {
            this.showNotification('No recording to save', 'error');
            return;
        }

        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('audio', audioBlob);
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
        this.audioChunks = [];
        this.isRecording = false;
        this.isPaused = false;
        clearInterval(this.timerInterval);
        this.timerDisplay.textContent = '00:00:00';
        this.updateRecordingStatus('ready');
        this.updateButtonStates();
        this.saveButton.disabled = true;
        this.discardButton.disabled = true;
        this.visualizerContext.clearRect(0, 0, this.visualizerCanvas.width, this.visualizerCanvas.height);
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
