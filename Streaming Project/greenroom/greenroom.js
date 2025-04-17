let currentStream = null;

async function populateMicOptions() {
    try {
      // Asks for permission to access audio
      await navigator.mediaDevices.getUserMedia({ audio: true });
  
      const micSelect = document.getElementById("micSelect");
      const devices = await navigator.mediaDevices.enumerateDevices();
      const mics = devices.filter(device => device.kind === "audioinput");
  
      micSelect.innerHTML = ''; 
  
      if (mics.length === 0) {
        const option = document.createElement("option");
        option.text = "No microphones found";
        micSelect.appendChild(option);
        micSelect.disabled = true;
      } else {
        mics.forEach((mic, index) => {
          const option = document.createElement("option");
          option.value = mic.deviceId;
          option.text = mic.label || `Microphone ${index + 1}`;
          micSelect.appendChild(option);
        });
        micSelect.disabled = false;
      }
  
    } catch (err) {
      console.error("Error accessing microphone:", err);
      const micSelect = document.getElementById("micSelect");
      micSelect.innerHTML = '<option>Permission denied</option>';
      micSelect.disabled = true;
    }
}

let currentCameraStream = null;

populateMicOptions();

async function populateCameraOptions() {
  const cameraSelect = document.getElementById("cameraSelect");

  try {
    // Request permission to get device labels
    await navigator.mediaDevices.getUserMedia({ video: true });

    const devices = await navigator.mediaDevices.enumerateDevices();
    const cameras = devices.filter(device => device.kind === "videoinput");

    cameraSelect.innerHTML = "";

    if (cameras.length === 0) {
      const option = document.createElement("option");
      option.text = "No cameras found";
      cameraSelect.appendChild(option);
      cameraSelect.disabled = true;
      return;
    }

    // Add options to dropdown
    cameras.forEach((cam, index) => {
      const option = document.createElement("option");
      option.value = cam.deviceId;
      option.text = cam.label || `Camera ${index + 1}`;
      cameraSelect.appendChild(option);
    });

    cameraSelect.disabled = false;

    // Start preview with first camera
    startCameraPreview(cameras[0].deviceId);

    // Handles switching cameras
    cameraSelect.addEventListener("change", () => {
      startCameraPreview(cameraSelect.value);
    });

  } catch (err) {
    console.error("Camera permission denied or error:", err);
    cameraSelect.innerHTML = '<option>Permission denied</option>';
    cameraSelect.disabled = true;
  }
}

function startCameraPreview(deviceId) {
  if (currentCameraStream) {
    currentCameraStream.getTracks().forEach(track => track.stop());
  }

  navigator.mediaDevices.getUserMedia({
    video: { deviceId: { exact: deviceId } }
  }).then(stream => {
    currentCameraStream = stream;
    const videoElement = document.getElementById("cameraPreview");
    videoElement.srcObject = stream;
  }).catch(err => {
    console.error("Failed to start camera preview:", err);
  });
}

populateCameraOptions();


function testMic(deviceId) {
  navigator.mediaDevices.getUserMedia({ audio: { deviceId: deviceId ? { exact: deviceId } : undefined } })
    .then(stream => {
      const micStatus = document.getElementById("micStatus");
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      source.connect(analyser);
      analyser.fftSize = 512;

      const buffer = new Uint8Array(analyser.frequencyBinCount);

      function detectAudio() {
        analyser.getByteFrequencyData(buffer);
        const maxVolume = Math.max(...buffer);
        micStatus.textContent = maxVolume > 20 ? "Mic working 🎤" : "Listening...";
        requestAnimationFrame(detectAudio);
      }

      detectAudio();
    })
    .catch(err => {
      console.error("Mic access error:", err);
      document.getElementById("micStatus").textContent = "Mic test failed";
    });
}

document.getElementById("micTestBtn").addEventListener("click", () => {
  const selectedMic = document.getElementById("micSelect").value;
  testMic(selectedMic);
});

document.getElementById("joinRoomBtn").addEventListener("click", async () => {
    const name = document.getElementById("username").value.trim();
    if (!name) {
        alert("Please enter your display name.");
        return;
    }

    try {
        // Explicitly request microphone access
        await navigator.mediaDevices.getUserMedia({ audio: true })
            .then((stream) => {
                const hasMic = stream.active;  // Check if the stream is active
                if (!hasMic) {
                    alert("Microphone access is required to join.");
                    return;
                }
                // Successfully got the mic stream
                localStorage.setItem("hasMic", "true");
            })
            .catch((err) => {
                console.error("Mic access failed:", err);
                alert("Microphone access is required to join.");
                return;
            });

        // Try camera access separately
        try {
            await navigator.mediaDevices.getUserMedia({ video: true });
            localStorage.setItem("hasCamera", "true");
        } catch {
            console.warn("Camera not available or permission denied.");
            localStorage.setItem("hasCamera", "false");
        }

        // Saves user info (name) to localStorage
        const user = { name };
        localStorage.setItem("currentUser", JSON.stringify(user)); // Save user data to localStorage
        localStorage.setItem("hasMic", "true"); // Optionally save mic status (if needed)

        // Now redirect to the meeting room
        console.log("Redirecting to meetingroom.html");
        window.location.href = "../meetingroom/meetingroom.html"; // Make sure the path is correct

    } catch (err) {
        alert("Microphone access is required to join.");
        console.error("Mic access failed:", err);
    }
});


  
