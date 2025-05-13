// Audio Player Controls
export class AudioPlayer {
    constructor() {
        this.audioElement = document.getElementById('audioElement');
        this.playPauseBtn = document.getElementById('playPauseBtn');
        this.progressBar = document.getElementById('progressBar');
        this.progress = document.getElementById('progress');
        this.currentTimeDisplay = document.getElementById('currentTime');
        this.durationDisplay = document.getElementById('duration');
        this.rewindBtn = document.getElementById('rewindBtn');
        this.forwardBtn = document.getElementById('forwardBtn');
        this.speedBtn = document.getElementById('speedBtn');
        this.muteBtn = document.getElementById('muteBtn');
        this.volumeSlider = document.getElementById('volumeSlider');
        this.episodeTitle = document.getElementById('episodeTitle');
        this.episodeMeta = document.getElementById('episodeMeta');
        this.episodeThumbnail = document.getElementById('episodeThumbnail');

        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Play/Pause
        this.playPauseBtn.addEventListener('click', () => this.togglePlay());
        
        // Progress bar
        this.progressBar.addEventListener('click', (e) => this.seek(e));
        
        // Time updates
        this.audioElement.addEventListener('timeupdate', () => this.updateProgress());
        this.audioElement.addEventListener('loadedmetadata', () => this.updateDuration());
        
        // Control buttons
        this.rewindBtn.addEventListener('click', () => this.rewind());
        this.forwardBtn.addEventListener('click', () => this.forward());
        this.speedBtn.addEventListener('click', () => this.changeSpeed());
        this.muteBtn.addEventListener('click', () => this.toggleMute());
        
        // Volume control
        this.volumeSlider.addEventListener('input', (e) => this.changeVolume(e));

        // Track ended
        this.audioElement.addEventListener('ended', () => this.onTrackEnded());
    }

    loadEpisode(episode) {
        this.audioElement.src = episode.audioUrl;
        this.episodeTitle.textContent = episode.title;
        this.episodeMeta.textContent = episode.meta || '';
        this.episodeThumbnail.src = episode.thumbnail || '';
        this.episodeThumbnail.alt = episode.title;
        this.audioElement.load();
    }

    togglePlay() {
        if (this.audioElement.paused) {
            this.audioElement.play();
            this.playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
        } else {
            this.audioElement.pause();
            this.playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
        }
    }

    updateProgress() {
        const percent = (this.audioElement.currentTime / this.audioElement.duration) * 100;
        this.progress.style.width = `${percent}%`;
        this.currentTimeDisplay.textContent = this.formatTime(this.audioElement.currentTime);
    }

    updateDuration() {
        this.durationDisplay.textContent = this.formatTime(this.audioElement.duration);
    }

    seek(event) {
        const bounds = this.progressBar.getBoundingClientRect();
        const percent = (event.clientX - bounds.left) / bounds.width;
        this.audioElement.currentTime = percent * this.audioElement.duration;
    }

    rewind() {
        this.audioElement.currentTime = Math.max(this.audioElement.currentTime - 15, 0);
    }

    forward() {
        this.audioElement.currentTime = Math.min(
            this.audioElement.currentTime + 15,
            this.audioElement.duration
        );
    }

    changeSpeed() {
        const speeds = [1, 1.25, 1.5, 1.75, 2];
        const currentSpeed = this.audioElement.playbackRate;
        const nextSpeedIndex = (speeds.indexOf(currentSpeed) + 1) % speeds.length;
        this.audioElement.playbackRate = speeds[nextSpeedIndex];
        this.speedBtn.textContent = `${speeds[nextSpeedIndex]}x`;
    }

    toggleMute() {
        this.audioElement.muted = !this.audioElement.muted;
        this.muteBtn.innerHTML = this.audioElement.muted 
            ? '<i class="fas fa-volume-mute"></i>' 
            : '<i class="fas fa-volume-up"></i>';
        this.volumeSlider.value = this.audioElement.muted ? 0 : this.audioElement.volume;
    }

    changeVolume(event) {
        const volume = event.target.value;
        this.audioElement.volume = volume;
        this.audioElement.muted = volume === 0;
        this.muteBtn.innerHTML = volume === 0
            ? '<i class="fas fa-volume-mute"></i>'
            : '<i class="fas fa-volume-up"></i>';
    }

    onTrackEnded() {
        this.playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
        this.progress.style.width = '0%';
    }

    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60).toString().padStart(2, '0');
        return `${mins}:${secs}`;
    }

    // Public methods for external control
    play() {
        this.audioElement.play();
        this.playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
    }

    pause() {
        this.audioElement.pause();
        this.playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
    }

    stop() {
        this.audioElement.pause();
        this.audioElement.currentTime = 0;
        this.playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
    }
}