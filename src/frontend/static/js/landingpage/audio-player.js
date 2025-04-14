// This function initializes a custom audio player instance given its wrapper element.
// It assumes that within the wrapper, there is an <audio> element, a play button (.play-btn),
// a range input (.seek-bar), and a time display (.time-display).
function initCustomAudioPlayer(wrapperElement) {
    const audio = wrapperElement.querySelector("audio");
    const playBtn = wrapperElement.querySelector(".play-btn");
    const seekBar = wrapperElement.querySelector(".seek-bar");
    const timeDisplay = wrapperElement.querySelector(".time-display");

    function updateTime() {
        const current = formatTime(audio.currentTime);
        const duration = formatTime(audio.duration);
        timeDisplay.textContent = `${current} / ${duration}`;
    }

    audio.addEventListener("loadedmetadata", () => {
        seekBar.max = Math.floor(audio.duration);
        updateTime();
    });

    audio.addEventListener("timeupdate", () => {
        seekBar.value = Math.floor(audio.currentTime);
        updateTime();
    });

    playBtn.addEventListener("click", () => {
        if (audio.paused) {
            audio.play();
            playBtn.textContent = "⏸";
        } else {
            audio.pause();
            playBtn.textContent = "▶";
        }
    });

    seekBar.addEventListener("input", () => {
        audio.currentTime = seekBar.value;
        updateTime();
    });
}

// Helper function to format seconds as mm:ss
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
}

// Expose the initializer for use in other scripts
window.initCustomAudioPlayer = initCustomAudioPlayer;


// --------------------
// Main Audio Player Code - Updated
// --------------------
const audio = document.getElementById("audio");
const playBtn = document.getElementById("play-btn");
const seekBar = document.getElementById("seek-bar");
const currentTimeEl = document.getElementById("current-time");
const durationEl = document.getElementById("duration");
const rewindBtn = document.getElementById("rewind-btn");
const forwardBtn = document.getElementById("forward-btn");
const speedBtn = document.getElementById("speed-btn");

// Play/Pause Functionality
playBtn.addEventListener("click", () => {
    if (audio.paused) {
        audio.play();
        playBtn.innerHTML = '⏸️'; // Pause icon
    } else {
        audio.pause();
        playBtn.innerHTML = '▶️'; // Play icon
    }
});

// Update Seek Bar
audio.addEventListener("timeupdate", () => {
    const currentTime = formatTime(audio.currentTime);
    const duration = formatTime(audio.duration);
    seekBar.value = (audio.currentTime / audio.duration) * 100 || 0;
    currentTimeEl.innerText = currentTime;
    durationEl.innerText = duration;
});

// Seek Bar Control
seekBar.addEventListener("input", () => {
    audio.currentTime = (seekBar.value / 100) * audio.duration;
});

// Rewind & Forward 15 seconds
rewindBtn.addEventListener("click", () => audio.currentTime -= 15);
forwardBtn.addEventListener("click", () => audio.currentTime += 15);

// Playback Speed Toggle
let speed = 1;
speedBtn.addEventListener("click", () => {
    speed = speed === 1 ? 1.5 : speed === 1.5 ? 2 : 1;
    audio.playbackRate = speed;
    speedBtn.innerText = speed + "x";
});

// Helper Function to Format Time
function formatTime(seconds) {
    let mins = Math.floor(seconds / 60);
    let secs = Math.floor(seconds % 60);
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
}
