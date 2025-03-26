// Select elements
const audioPlayer = document.getElementById("audio-player");
const audioSource = document.getElementById("audio-source");
const playBtn = document.getElementById("play-btn");
const seekBar = document.getElementById("seek-bar");
const currentTimeEl = document.getElementById("current-time");
const durationEl = document.getElementById("duration");
const rewindBtn = document.getElementById("rewind-btn");
const forwardBtn = document.getElementById("forward-btn");
const speedBtn = document.getElementById("speed-btn");

// ✅ Check if an audio file exists
if (!audioSource.src || audioSource.src.trim() === "") {
    console.error("❌ No audio file found!");
    audioPlayer.style.display = "none"; // Hide player if no audio
} else {
    console.log("🎵 Audio file loaded:", audioSource.src);
    audioPlayer.load(); // Ensure audio loads correctly
}

// Play/Pause Functionality
playBtn.addEventListener("click", () => {
    if (audioPlayer.paused) {
        audioPlayer.play();
        playBtn.innerHTML = '<i class="fas fa-pause"></i>';
    } else {
        audioPlayer.pause();
        playBtn.innerHTML = '<i class="fas fa-play"></i>';
    }
});

// Update Seek Bar
audioPlayer.addEventListener("timeupdate", () => {
    const currentTime = formatTime(audioPlayer.currentTime);
    const duration = formatTime(audioPlayer.duration);
    seekBar.value = (audioPlayer.currentTime / audioPlayer.duration) * 100 || 0;
    currentTimeEl.innerText = currentTime;
    durationEl.innerText = duration;
});

// Seek Bar Control
seekBar.addEventListener("input", () => {
    audioPlayer.currentTime = (seekBar.value / 100) * audioPlayer.duration;
});

// Rewind & Forward 15 seconds
rewindBtn.addEventListener("click", () => audioPlayer.currentTime -= 15);
forwardBtn.addEventListener("click", () => audioPlayer.currentTime += 15);

// Playback Speed Toggle
let speed = 1;
speedBtn.addEventListener("click", () => {
    speed = speed === 1 ? 1.5 : speed === 1.5 ? 2 : 1;
    audioPlayer.playbackRate = speed;
    speedBtn.innerText = speed + "x";
});

// Helper Function to Format Time
function formatTime(seconds) {
    let mins = Math.floor(seconds / 60);
    let secs = Math.floor(seconds % 60);
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
}
