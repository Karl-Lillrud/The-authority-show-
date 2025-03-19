// Select elements
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
    playBtn.innerHTML = '<i class="fas fa-pause"></i>';
  } else {
    audio.pause();
    playBtn.innerHTML = '<i class="fas fa-play"></i>';
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
