let enhancedAudioBlob = null;
let enhancedAudioId = null;
let isolatedAudioBlob = null;
let isolatedAudioId = null;

let activeAudioBlob = null;
let activeAudioId = null;

window.CURRENT_USER_ID = localStorage.getItem("user_id");

function showTab(tabName) {
    const content = document.getElementById('content');
    content.innerHTML = ''; // Clear existing content

    if (tabName === 'transcription') {
        content.innerHTML = `
            <h2>🎙 AI-Powered Transcription</h2>
            <input type="file" id="fileUploader" accept="audio/*,video/*">
            <button class="btn ai-edit-button" onclick="transcribe()">▶ Transcribe</button>
            <div class="result-field">
                <pre id="transcriptionResult"></pre>
            </div>

            <div id="enhancementTools" style="display:none;">
                <hr/>
                <h3>🔧 Enhancement Tools</h3>
                <div class="result-group">
                    <button class="btn ai-edit-button" onclick="generateCleanTranscript()">🧹 Clean Transcript</button>
                    <div class="result-field">
                        <pre id="cleanTranscriptResult"></pre>
                    </div>
                </div>
                <div class="result-group">
                    <button class="btn ai-edit-button" onclick="generateAISuggestions()">🤖 AI Suggestions</button>
                    <div class="result-field">
                        <pre id="aiSuggestionsResult"></pre>
                    </div>
                </div>
                <div class="result-group">
                    <button class="btn ai-edit-button" onclick="generateShowNotes()">📝 Show Notes</button>
                    <div class="result-field">
                        <pre id="showNotesResult"></pre>
                    </div>
                </div>
                <div class="result-group">
                    <button class="btn ai-edit-button" onclick="generateQuotes()">💬 Generate Quotes</button>
                    <div class="result-field">
                        <pre id="quotesResult"></pre>
                    </div>
                </div>
                <div class="result-group">
                    <button class="btn ai-edit-button" onclick="generateQuoteImages()">🖼️ Generate Quote Images</button>
                    <div class="result-field">
                        <div id="quoteImagesResult"></div>
                    </div>
                </div>
            </div>
    `;
}
      else if (tabName === 'audio') {
        content.innerHTML = `
            <h2>🎵 AI Audio Enhancement</h2>
            <input type="file" id="audioUploader" accept="audio/*" onchange="previewOriginalAudio()">
            <div id="originalAudioContainer" style="display: none; margin-bottom: 1rem;">
                <p>🎧 <strong>Original Audio</strong></p>
                <audio id="originalAudioPlayer" controls style="width: 100%"></audio>
            </div>

            <div style="margin-top: 1rem; padding: 1rem; border: 1px solid #ddd; border-radius: 12px;">
                <h3>🔊 Choose Audio Processing Method</h3>
                <p style="margin-bottom: 1rem;">Select one of the following enhancements for your uploaded audio file:</p>

                <!-- 🎤 Voice Isolation -->
                <div id="voiceIsolationSection" style="margin-bottom: 1.5rem;">
                    <h4>🎤 <strong>Voice Isolation (Powered by ElevenLabs)</strong></h4>
                    <button class="btn ai-edit-button" onclick="runVoiceIsolation()">🎙️ Isolate Voice</button>
                    <div id="isolatedVoiceResult" style="margin-top: 1rem;"></div>

                </div>

                <!-- 🎚️ Audio Enhancement -->
                <div id="audioEnhancementSection">
                    <h4>🎚️ <strong>Audio Enhancement (Noise Reduction & Normalization)</strong></h4>
                    <button class="btn ai-edit-button" onclick="enhanceAudio()">✨ Enhance Audio</button>
                    <div id="audioControls" style="margin-top: 1rem;"></div>
                </div>
            </div>


            <div id="audioAnalysisSection" style="display: none;">
                <hr/>
                <h3>🤖 AI Analysis</h3>
                <button class="btn ai-edit-button" onclick="analyzeEnhancedAudio()">📊 Analyze</button>
                <pre id="analysisResults"></pre>
                <a id="downloadEnhanced" style="display:none;" download="processed_audio.wav">📥 Download Processed Audio</a>
            </div>

            <div id="audioCuttingSection" style="display: none;">
                <hr/>
                <h3>✂ Audio Cutting</h3>
                <label>Start: <input type="number" id="startTime" min="0" step="0.1"></label>
                <label>End: <input type="number" id="endTime" min="0" step="0.1"></label>
                <button class="btn ai-edit-button" onclick="cutAudio()">✂ Cut</button>
                <div id="cutResult"></div>
                <a id="downloadCut" style="display:none;" download="cut_audio.wav">📥 Download Cut</a>
            </div>

            <div id="aiCuttingSection" style="display: none;">
                <hr/>
                <h3>🧠 AI Cutting + Transcript</h3>
                <button class="btn ai-edit-button" onclick="aiCutAudio()">🧠 Run AI Cut</button>
                <pre id="aiTranscript"></pre>
                <pre id="aiSuggestedCuts"></pre>
            </div>
        `;
    } else if (tabName === 'video') {
        content.innerHTML = `
            <h2>📹 AI Video Enhancement</h2>
            <input type="file" id="videoUploader" accept="video/*" onchange="previewOriginalVideo()">
            <div id="originalVideoContainer" style="display: none; margin-bottom: 1rem;">
                <p>🎬 <strong>Original Video</strong></p>
                <video id="originalVideoPlayer" controls style="width: 100%"></video>
            </div>
            <button class="btn ai-edit-button" onclick="enhanceVideo()">Enhance Video</button>
            <div id="videoResult"></div>
        `;
    }
}

let rawTranscript = "";
let fullTranscript = "";

async function transcribe() {
    const fileInput = document.getElementById('fileUploader');
    const resultContainer = document.getElementById('transcriptionResult');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please upload a file.');
        return;
    }

    try {
        await consumeUserCredits("transcription");
    } catch (err) {
        resultContainer.innerText = `❌ Not enough credits: ${err.message}`;
        return;
    }

    resultContainer.innerText = "🔄 Transcribing... Please wait.";
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/transcription/transcribe', {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            const result = await response.json();
            rawTranscript = result.raw_transcription || "";
            fullTranscript = result.full_transcript || "";

            resultContainer.innerText = rawTranscript;
            document.getElementById("enhancementTools").style.display = "block";
        } else {
            resultContainer.innerText = `❌ Error: ${response.status} - ${response.statusText}`;
        }
    } catch (error) {
        resultContainer.innerText = `❌ Transcription failed: ${error.message}`;
    }
}

async function generateCleanTranscript() {
    try {
        const res = await fetch("/transcription/clean", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ transcript: fullTranscript })
        });

        const data = await res.json();
        document.getElementById("cleanTranscriptResult").innerText =
            data.clean_transcript || "No clean result.";
    } catch (err) {
        document.getElementById("cleanTranscriptResult").innerText =
            "❌ Failed to clean transcript. Server says: " + err.message;
    }
}


async function generateAISuggestions() {
    try {
        const res = await fetch('/transcription/ai_suggestions', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ transcript: rawTranscript })
        });

        const data = await res.json();
        document.getElementById("aiSuggestionsResult").innerText = data.ai_suggestions || "No suggestions.";
    } catch (err) {
        // 🔧 Show error message if OpenAI or backend fails
        document.getElementById("aiSuggestionsResult").innerText =
            "❌ Failed to generate suggestions. Server says: " + err.message;
    }
}

async function generateShowNotes() {
    try {
        const res = await fetch('/transcription/show_notes', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ transcript: rawTranscript })
        });

        const data = await res.json();
        document.getElementById("showNotesResult").innerText = data.show_notes || "No notes.";
    } catch (err) {
        document.getElementById("showNotesResult").innerText =
            "❌ Failed to generate show notes. Server says: " + err.message;
    }
}


async function generateQuotes() {
    try {
        const res = await fetch('/transcription/quotes', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ transcript: rawTranscript })
        });

        const data = await res.json();
        document.getElementById("quotesResult").innerText = data.quotes || "No quotes.";
    } catch (err) {
        document.getElementById("quotesResult").innerText =
            "❌ Failed to generate quotes. Server says: " + err.message;
    }
}


async function generateQuoteImages() {
    const quotes = document.getElementById("quotesResult").innerText;
    if (!quotes) return alert("Generate quotes first.");

    try {
        const res = await fetch('/transcription/quote_images', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ quotes })
        });

        const data = await res.json();
        const imageDiv = document.getElementById("quoteImagesResult");
        imageDiv.innerHTML = "";

        (data.quote_images || []).forEach(url => {
            const img = document.createElement("img");
            img.src = url;
            img.style.maxWidth = "100%";
            img.style.margin = "10px 0";
            imageDiv.appendChild(img);
        });
    } catch (err) {
        document.getElementById("quoteImagesResult").innerText =
            "❌ Failed to generate quote images. Server says: " + err.message;
    }
}



async function enhanceAudio() {
    const input = document.getElementById('audioUploader');
    const audioControls = document.getElementById('audioControls');
    const file = input.files[0];
    if (!file) return alert("Upload an audio file first.");

    try {
        await consumeUserCredits("audio_enhancment");
    } catch (err) {
        audioControls.innerHTML = `❌ Not enough credits: ${err.message}`;
        return;
    }

    audioControls.innerHTML = "🔄 Enhancing... Please wait.";
    const formData = new FormData();
    formData.append("audio", file);

    try {
        const response = await fetch("/audio/enhancement", {
            method: "POST",
            body: formData
        });

        const result = await response.json();
        enhancedAudioId = result.enhanced_audio;

        const audioRes = await fetch(`/transcription/get_file/${enhancedAudioId}`);
        const blob = await audioRes.blob();
        enhancedAudioBlob = blob;

        activeAudioBlob = blob;
        activeAudioId = enhancedAudioId;

        const url = URL.createObjectURL(blob);

        // 🎵 Inject custom player
        audioControls.innerHTML = `
            <div class="custom-audio-wrapper">
                <p class="audio-status">✅ Audio enhancement complete!</p>
                <div class="custom-audio-player">
                    <button id="customPlayBtn" class="play-btn">▶</button>
                    <input type="range" id="customSeek" value="0" min="0" step="1" class="seek-bar">
                    <span id="customTime" class="time-display">0:00 / 0:00</span>
                </div>
                <audio id="customAudio" src="${url}" style="display: none;"></audio>
            </div>
        `;

        // 🎛 Custom audio logic
        const audio = document.getElementById("customAudio");
        const playBtn = document.getElementById("customPlayBtn");
        const seek = document.getElementById("customSeek");
        const time = document.getElementById("customTime");

        audio.addEventListener("loadedmetadata", () => {
            seek.max = Math.floor(audio.duration);
            updateTime();
        });

        audio.addEventListener("timeupdate", () => {
            seek.value = Math.floor(audio.currentTime);
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

        seek.addEventListener("input", () => {
            audio.currentTime = seek.value;
            updateTime();
        });

        function updateTime() {
            const current = formatTime(audio.currentTime);
            const duration = formatTime(audio.duration);
            time.textContent = `${current} / ${duration}`;
        }

        function formatTime(seconds) {
            const m = Math.floor(seconds / 60);
            const s = Math.floor(seconds % 60).toString().padStart(2, "0");
            return `${m}:${s}`;
        }

        // 🎯 Enable the rest of the interface
        document.getElementById("audioAnalysisSection").style.display = "block";
        document.getElementById("audioCuttingSection").style.display = "block";
        document.getElementById("aiCuttingSection").style.display = "block";
        const dl = document.getElementById("downloadEnhanced");
        dl.href = url;
        dl.style.display = "inline-block";
    } catch (err) {
        audioControls.innerHTML = `❌ Error: ${err.message}`;
    }
}


async function runVoiceIsolation() {
    const input = document.getElementById('audioUploader');
    const file = input.files[0];
    if (!file) return alert("Upload an audio file first.");

    const resultContainer = document.getElementById("isolatedVoiceResult");

    try {
        await consumeUserCredits("voice_isolation");
    } catch (err) {
        resultContainer.innerText = `❌ Not enough credits: ${err.message}`;
        return;
    }
    resultContainer.innerText = "🎙️ Isolating voice using ElevenLabs...";

    const formData = new FormData();
    formData.append("audio", file);

    try {
        const response = await fetch("/transcription/voice_isolate", { method: "POST", body: formData });
        const data = await response.json();
        isolatedAudioId = data.isolated_file_id;

        const audioRes = await fetch(`/transcription/get_file/${isolatedAudioId}`);
        const blob = await audioRes.blob();
        isolatedAudioBlob = blob;

        activeAudioBlob = blob;
        activeAudioId = isolatedAudioId;

        const url = URL.createObjectURL(blob);
        resultContainer.innerHTML = `
            <div class="custom-audio-wrapper">
                <p class="audio-status">🎧 Isolated Audio</p>
                <div class="custom-audio-player">
                    <button id="isolatedPlayBtn" class="play-btn">▶</button>
                    <input type="range" id="isolatedSeek" value="0" min="0" step="1" class="seek-bar">
                    <span id="isolatedTime" class="time-display">0:00 / 0:00</span>
                </div>
                <audio id="isolatedAudio" src="${url}" style="display: none;"></audio>
            </div>
        `;
        document.getElementById("audioAnalysisSection").style.display = "block";
        document.getElementById("audioCuttingSection").style.display = "block";
        document.getElementById("aiCuttingSection").style.display = "block";

        const dl = document.getElementById("downloadIsolatedVoice");
        dl.href = url;
        dl.style.display = "inline-block";

        // Initialize custom audio player for isolated audio
        const audio = document.getElementById("isolatedAudio");
        const playBtn = document.getElementById("isolatedPlayBtn");
        const seek = document.getElementById("isolatedSeek");
        const time = document.getElementById("isolatedTime");

        audio.addEventListener("loadedmetadata", () => {
            seek.max = Math.floor(audio.duration);
            updateTime();
        });
        audio.addEventListener("timeupdate", () => {
            seek.value = Math.floor(audio.currentTime);
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
        seek.addEventListener("input", () => {
            audio.currentTime = seek.value;
            updateTime();
        });
        function updateTime() {
            const current = formatTime(audio.currentTime);
            const duration = formatTime(audio.duration);
            time.textContent = `${current} / ${duration}`;
        }
        function formatTime(seconds) {
            const m = Math.floor(seconds / 60);
            const s = Math.floor(seconds % 60).toString().padStart(2, "0");
            return `${m}:${s}`;
        }
    } catch (err) {
        resultContainer.innerText = `❌ Isolation failed: ${err.message}`;
    }
}

async function analyzeEnhancedAudio() {
    const resultEl = document.getElementById("analysisResults");
    if (!activeAudioBlob) return alert("No audio loaded. Enhance or Isolate first.");

    resultEl.innerText = "🔍 Analyzing...";
    const formData = new FormData();
    formData.append("audio", activeAudioBlob, "processed_audio.wav");

    try {
        const res = await fetch("/audio_analysis", { method: "POST", body: formData });
        const data = await res.json();
        resultEl.innerText = `
📊 Emotion: ${data.emotion}
📊 Sentiment: ${data.sentiment}
📊 Clarity Score: ${data.clarity_score}
📊 Background Noise: ${data.background_noise}
📊 Speech Rate (WPM): ${data.speech_rate}
        `;
    } catch (err) {
        resultEl.innerText = `❌ Analysis failed: ${err.message}`;
    }
}

async function cutAudio() {
    const start = parseFloat(document.getElementById("startTime").value);
    const end = parseFloat(document.getElementById("endTime").value);
    if (!activeAudioId || isNaN(start) || isNaN(end) || start >= end) return alert("Invalid times or no audio ID.");

    const res = await fetch('/clip_audio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_id: activeAudioId, clips: [{ start, end }] })
    });

    const data = await res.json();
    if (!data.clipped_audio) return alert("❌ Cut failed.");

    const audioRes = await fetch(`/transcription/get_file/${data.clipped_audio}`);
    const blob = await audioRes.blob();
    const url = URL.createObjectURL(blob);

    document.getElementById("cutResult").innerHTML = `<audio controls src="${url}"></audio>`;
    const dl = document.getElementById("downloadCut");
    dl.href = url;
    dl.style.display = "inline-block";
}

async function aiCutAudio() {
    if (!activeAudioId) return alert("No audio loaded.");

    const res = await fetch('/ai_cut_audio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_id: activeAudioId })
    });

    const data = await res.json();
    if (!res.ok || !data.cleaned_transcript) return alert("❌ AI cut failed.");

    document.getElementById("aiTranscript").innerText = data.cleaned_transcript;
    document.getElementById("aiSuggestedCuts").innerText = (data.suggested_cuts || [])
        .map(c => `💬 "${c.sentence}" (${c.start}s - ${c.end}s) | Confidence: ${c.certainty_score}`)
        .join("\n") || "No suggested cuts found.";
}

async function enhanceVideo() {
    const fileInput = document.getElementById('videoUploader');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please upload a video file.');
        return;
    }

    const videoResult = document.getElementById('videoResult');
    videoResult.innerText = "🔄 Uploading video... Please wait.";

    const formData = new FormData();
    formData.append('video', file);

    try {
        // Step 1: Upload the video file and get a video_id
        const uploadResponse = await fetch('/ai_videoedit', {
            method: 'POST',
            body: formData,
        });

        if (!uploadResponse.ok) {
            throw new Error(`Video upload failed: ${uploadResponse.statusText}`);
        }
        
        const uploadResult = await uploadResponse.json();
        const video_id = uploadResult.video_id;
        if (!video_id) {
            throw new Error('No video_id returned from upload.');
        }
        
        videoResult.innerText = "🔄 Enhancing video... Please wait.";
        
        // Step 2: Call the enhance endpoint with the video_id
        const enhanceResponse = await fetch('/ai_videoenhance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ video_id })
        });
        
        if (!enhanceResponse.ok) {
            throw new Error(`Enhancement failed: ${enhanceResponse.statusText}`);
        }
        
        const enhanceResult = await enhanceResponse.json();
        const processed_id = enhanceResult.processed_video_id;
        if (!processed_id) {
            throw new Error('No processed_video_id returned from enhancement.');
        }
        
        // Step 3: Construct video URL from processed_id and display the video
        const videoURL = `/get_video/${processed_id}`;
        videoResult.innerHTML = `<video controls src="${videoURL}" style="width: 100%; margin-top: 1rem;"></video>`;
    } catch (err) {
        videoResult.innerText = `❌ ${err.message}`;
    }
}

function previewOriginalAudio() {
    const fileInput = document.getElementById('audioUploader');
    const file = fileInput.files[0];
    if (!file) return;
    const audioURL = URL.createObjectURL(file);
    const container = document.getElementById('originalAudioContainer');

    container.innerHTML = `
        <div class="custom-audio-wrapper">
            <p class="audio-status">🎧 Original Audio</p>
            <div class="custom-audio-player">
                <button id="originalPlayBtn" class="play-btn">▶</button>
                <input type="range" id="originalSeek" value="0" min="0" step="1" class="seek-bar">
                <span id="originalTime" class="time-display">0:00 / 0:00</span>
            </div>
            <audio id="originalAudio" src="${audioURL}" style="display: none;"></audio>
        </div>
    `;
    container.style.display = 'block';

    // Initialize custom audio player events
    const audio = document.getElementById("originalAudio");
    const playBtn = document.getElementById("originalPlayBtn");
    const seek = document.getElementById("originalSeek");
    const time = document.getElementById("originalTime");

    audio.addEventListener("loadedmetadata", () => {
        seek.max = Math.floor(audio.duration);
        updateTime();
    });
    audio.addEventListener("timeupdate", () => {
        seek.value = Math.floor(audio.currentTime);
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
    seek.addEventListener("input", () => {
        audio.currentTime = seek.value;
        updateTime();
    });
    function updateTime() {
        const current = formatTime(audio.currentTime);
        const duration = formatTime(audio.duration);
        time.textContent = `${current} / ${duration}`;
    }
    function formatTime(seconds) {
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60).toString().padStart(2, "0");
        return `${m}:${s}`;
    }
}

function previewOriginalVideo() {
    const fileInput = document.getElementById('videoUploader');
    const file = fileInput.files[0];
    if (!file) return;
    const videoURL = URL.createObjectURL(file);
    const videoPlayer = document.getElementById('originalVideoPlayer');
    const container = document.getElementById('originalVideoContainer');
    videoPlayer.src = videoURL;
    container.style.display = 'block';
}

async function fetchUserCredits(userId) {
    try {
        const response = await fetch(`/api/credits/check?user_id=${userId}`);
        if (response.ok) {
            const data = await response.json();
            document.getElementById("userCredits").innerText = `Available Credits: ${data.availableCredits}`;
        } else {
            alert("Failed to fetch user credits.");
        }
    } catch (error) {
        console.error("Error fetching user credits:", error);
    }
}

async function consumeUserCredits(featureKey) {
    if (!window.CURRENT_USER_ID) {
        throw new Error("User not logged in.");
    }

    const res = await fetch('/credits/consume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: window.CURRENT_USER_ID,
            feature: featureKey
        })
    });

    const result = await res.json();
    if (!res.ok) {
        throw new Error(result.error || "Failed to consume credits");
    }

    // ✅ Update the UI to reflect new credit balance
    await fetchUserCredits(CURRENT_USER_ID);

    return result.data;
}

