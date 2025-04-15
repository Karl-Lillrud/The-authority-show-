let enhancedAudioBlob = null;
let enhancedAudioId = null;
let isolatedAudioBlob = null;
let isolatedAudioId = null;

let activeAudioBlob = null;
let activeAudioId = null;

window.CURRENT_USER_ID = localStorage.getItem("user_id");

const CREDIT_COSTS = {
    ai_audio_analysis: 300,
    ai_audio_cutting: 500,
    ai_quotes: 200,
    ai_qoute_images: 1000,
    ai_suggestions: 300,
    audio_cutting: 500,
    audio_enhancment: 500,
    show_notes: 250,
    transcription: 600,
    translation: 150,
    video_cutting: 800,
    video_enhancement: 800,
    voice_isolation: 500
};

function labelWithCredits(text, key) {
    const cost = CREDIT_COSTS[key];
    return `${text} <span style="color: gray; font-size: 0.9em;">(${cost} credits)</span>`;
}

function showTab(tabName) {
    const content = document.getElementById('content');
    content.innerHTML = ''; // Clear existing content

    if (tabName === 'transcription') {
        content.innerHTML = `
            <h2>🎙 AI-Powered Transcription</h2>
            <input type="file" id="fileUploader" accept="audio/*,video/*">
            <button class="btn ai-edit-button" onclick="transcribe()">
              ${labelWithCredits("▶ Transcribe", "transcription")}
            </button>
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
                    <button class="btn ai-edit-button" onclick="generateAISuggestions()">
                      ${labelWithCredits("🤖 AI Suggestions", "ai_suggestions")}
                    </button>
                    <div class="result-field">
                        <pre id="aiSuggestionsResult"></pre>
                    </div>
                </div>
                <div class="result-group">
                    <button class="btn ai-edit-button" onclick="generateShowNotes()">
                      ${labelWithCredits("📝 Show Notes", "show_notes")}
                    </button>
                    <div class="result-field">
                        <pre id="showNotesResult"></pre>
                    </div>
                </div>
                <div class="result-group">
                    <button class="btn ai-edit-button" onclick="generateQuotes()">
                      ${labelWithCredits("💬 Generate Quotes", "ai_quotes")}
                    </button>
                    <div class="result-field">
                        <pre id="quotesResult"></pre>
                    </div>
                </div>
                <div class="result-group">
                    <button class="btn ai-edit-button" onclick="generateQuoteImages()">
                      ${labelWithCredits("🖼️ Generate Quote Images", "ai_qoute_images")}
                    </button>
                    <div class="result-field">
                        <div id="quoteImagesResult"></div>
                    </div>
                </div>
            </div>
        `;
    } else if (tabName === 'audio') {
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

            <div id="voiceIsolationSection" style="margin-bottom: 1.5rem;">
            <h4>🎤 <strong>Voice Isolation (Powered by ElevenLabs)</strong></h4>
            <button class="btn ai-edit-button" onclick="runVoiceIsolation()">
                ${labelWithCredits("🎙️ Isolate Voice", "voice_isolation")}
            </button>
            <div id="isolatedVoiceResult" style="margin-top: 1rem;"></div>
            <a id="downloadIsolatedVoice"
                class="inline-block mt-2 bg-orange-500 text-white px-4 py-2 rounded-2xl shadow hover:shadow-lg transition"
                style="display: none;"
                download="isolated_voice.wav">
                📥 Download Isolated Voice
            </a>
            </div>

                <div id="audioEnhancementSection">
                    <h4>🎚️ <strong>Audio Enhancement (Noise Reduction & Normalization)</strong></h4>
                    <button class="btn ai-edit-button" onclick="enhanceAudio()">
                      ${labelWithCredits("✨ Enhance Audio", "audio_enhancment")}
                    </button>
                    <div id="audioControls" style="margin-top: 1rem;"></div>
                </div>
            </div>

            <div id="audioAnalysisSection" style="display: none;">
                <hr/>
                <h3>🤖 AI Analysis</h3>
                <button class="btn ai-edit-button" onclick="analyzeEnhancedAudio()">
                  ${labelWithCredits("📊 Analyze", "ai_audio_analysis")}
                </button>
                <pre id="analysisResults"></pre>
                <div id="soundEffectTimeline" style="margin-top: 1rem;"></div>
                <a id="downloadEnhanced" class="btn ai-edit-button" download="processed_audio.wav">
                     📥 Download Processed Audio
                </a>
            </div>

            <div id="audioCuttingSection" style="display: none;">
                <hr/>
                <h3>✂ Audio Cutting</h3>
                <label>Start: <input type="number" id="startTime" min="0" step="0.1"></label>
                <label>End: <input type="number" id="endTime" min="0" step="0.1"></label>
                <button class="btn ai-edit-button" onclick="cutAudio()">
                  ${labelWithCredits("✂ Cut", "audio_cutting")}
                </button>
                <div id="cutResult"></div>
                <a id="downloadCut" class="btn ai-edit-button" download="cut_audio.wav">📥 Download Cut</a>
            </div>

            <div id="aiCuttingSection" style="display: none;">
                <hr/>
                <h3>🧠 AI Cutting + Transcript</h3>
                <button class="btn ai-edit-button" onclick="aiCutAudio()">
                  ${labelWithCredits("🧠 Run AI Cut", "ai_audio_cutting")}
                </button>
                <div class="result-field">
                <h4>Transcript</h4>
                <pre id="aiTranscript"></pre>
                </div>
                <div class="result-field">
                <h4>Suggested Cuts</h4>
                <pre id="aiSuggestedCuts"></pre>
                </div>
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
            <button class="btn ai-edit-button" onclick="enhanceVideo()">
            ${labelWithCredits("✨ Enhance Video", "video_enhancement")}
            </button>
            <div id="videoResult"></div>
            <a id="downloadVideo" class="btn ai-edit-button" download="enhanced_video.mp4" style="display: none;">
            📥 Download Enhanced Video
            </a>
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
        await consumeUserCredits("ai_suggestions");

        const res = await fetch('/transcription/ai_suggestions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transcript: rawTranscript })
        });

        const data = await res.json();
        document.getElementById("aiSuggestionsResult").innerText = data.ai_suggestions || "No suggestions.";
    } catch (err) {
        document.getElementById("aiSuggestionsResult").innerText =
            "❌ Not enough credits: " + err.message;
    }
}

async function generateShowNotes() {
    try {
        await consumeUserCredits("show_notes");

        const res = await fetch('/transcription/show_notes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transcript: rawTranscript })
        });

        const data = await res.json();
        document.getElementById("showNotesResult").innerText = data.show_notes || "No notes.";
    } catch (err) {
        document.getElementById("showNotesResult").innerText =
            "❌ Not enough credits: " + err.message;
    }
}

async function generateQuotes() {
    try {
        await consumeUserCredits("ai_quotes");

        const res = await fetch('/transcription/quotes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transcript: rawTranscript })
        });

        const data = await res.json();
        document.getElementById("quotesResult").innerText = data.quotes || "No quotes.";
    } catch (err) {
        document.getElementById("quotesResult").innerText =
            "❌ Not enough credits: " + err.message;
    }
}

async function generateQuoteImages() {
    const quotes = document.getElementById("quotesResult").innerText;
    if (!quotes) return alert("Generate quotes first.");

    try {
        await consumeUserCredits("ai_qoute_images");

        const res = await fetch('/transcription/quote_images', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
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
            "❌ Not enough credits: " + err.message;
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

        // Inject plain audio player without custom styling
        audioControls.innerHTML = `
            <p>Audio enhancement complete!</p>
            <audio controls src="${url}" style="width: 100%;"></audio>
        `;

        // Enable other sections of the interface
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
            <p>Isolated Audio</p>
            <audio controls src="${url}" style="width: 100%;"></audio>
        `;
        document.getElementById("audioAnalysisSection").style.display = "block";
        document.getElementById("audioCuttingSection").style.display = "block";
        document.getElementById("aiCuttingSection").style.display = "block";

        const dl = document.getElementById("downloadIsolatedVoice");
        dl.href = url;
        dl.style.display = "inline-block";
    } catch (err) {
        resultContainer.innerText = `❌ Isolation failed: ${err.message}`;
    }
}

async function analyzeEnhancedAudio() {
    const resultEl = document.getElementById("analysisResults");
    if (!activeAudioBlob) return alert("No audio loaded. Enhance or Isolate first.");

    try {
        await consumeUserCredits("ai_audio_analysis");
    } catch (err) {
        resultEl.innerText = `❌ Not enough credits: ${err.message}`;
        return;
    }

    resultEl.innerText = "🔍 Analyzing...";

    const formData = new FormData();
    formData.append("audio", activeAudioBlob, "processed_audio.wav");

    try {
        const res = await fetch("/audio_analysis", { method: "POST", body: formData });
        const data = await res.json();

        resultEl.innerText = `
📊 Sentiment: ${data.sentiment}
📊 Clarity Score: ${data.clarity_score}
📊 Background Noise: ${data.background_noise}
        `;

        
        const timeline = document.getElementById("soundEffectTimeline");
        timeline.innerHTML = `<h4>🎧 AI-Driven Sound Suggestions</h4>`;

        window.selectedSoundFX = {};

        (data.sound_effect_suggestions || []).forEach((entry, i) => {
        const container = document.createElement("div");
        container.className = "sound-suggestion";

        const sfxList = entry.sfx_options || [];
        const preview = sfxList.length
            ? `<audio controls src="${sfxList[0]}" class="sfx-preview"></audio>`
            : "<em>No audio preview available.</em>";

        container.innerHTML = `
            <p class="sfx-text"><strong>📍 Text:</strong> ${entry.timestamp_text}</p>
            <p class="sfx-emotion"><strong>🎭 Emotion:</strong> ${entry.emotion}</p>
            ${preview}
            <div class="sfx-actions">
            <button class="btn ai-sound-sug-button" onclick="acceptSfx(${i}, '${entry.emotion}', '${sfxList[0]}')">✅ Accept</button>
            <button class="btn ai-sound-sug-button" onclick="rejectSfx(${i})">❌ Reject</button>
            <select class="sfx-select" onchange="replaceSfx(${i}, this.value)">
                ${sfxList.map(url => `<option value="${url}">${url.split("/").pop()}</option>`).join('')}
            </select>
            </div>
        `;

        timeline.appendChild(container);

        if (sfxList.length) {
            selectedSoundFX[i] = { emotion: entry.emotion, sfxUrl: sfxList[0] };
        }
        });

        renderSfxDebug();

    } catch (err) {
        resultEl.innerText = `❌ Analysis failed: ${err.message}`;
    }
}

async function cutAudio() {
    const start = parseFloat(document.getElementById("startTime").value);
    const end = parseFloat(document.getElementById("endTime").value);
    if (!activeAudioId || isNaN(start) || isNaN(end) || start >= end) return alert("Invalid times or no audio ID.");

    try {
        await consumeUserCredits("audio_cutting");
    } catch (err) {
        return alert("❌ Not enough credits: " + err.message);
    }

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
    if (!activeAudioId) {
        alert('No audio loaded.');
        return;
    }

    try {
        await consumeUserCredits("ai_audio_cutting");
    } catch (err) {
        alert(`❌ Not enough credits: ${err.message}`);
        return;
    }

    // Optionally show a spinner or processing message in the transcript container
    document.getElementById("aiTranscript").innerText = "🔄 Processing AI Cut... Please wait.";

    try {
        const response = await fetch('/ai_cut_audio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_id: activeAudioId })
        });

        if (response.ok) {
            const data = await response.json();
            // Update transcript container
            document.getElementById("aiTranscript").innerText = data.cleaned_transcript || "No transcript available.";

            // Update suggested cuts container
            document.getElementById("aiSuggestedCuts").innerText =
                (data.suggested_cuts || [])
                    .map(c => `💬 "${c.sentence}" (${c.start}s - ${c.end}s) | Confidence: ${c.certainty_score}`)
                    .join("\n") || "No suggested cuts found.";
        } else {
            alert(`❌ Error: ${response.status} - ${response.statusText}`);
        }
    } catch (error) {
        alert(`❌ AI cut failed: ${error.message}`);
    }
}

async function enhanceVideo() {
    const fileInput = document.getElementById('videoUploader');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please upload a video file.');
        return;
    }

    try {
        await consumeUserCredits("video_enhancement");
    } catch (err) {
        return alert("❌ Not enough credits: " + err.message);
    }

    const videoResult = document.getElementById('videoResult');
    videoResult.innerText = "🔄 Uploading video... Please wait.";

    const formData = new FormData();
    formData.append('video', file);

    try {
        const uploadResponse = await fetch('/ai_videoedit', {
            method: 'POST',
            body: formData,
        });

        if (!uploadResponse.ok) {
            throw new Error(`Video upload failed: ${uploadResponse.statusText}`);
        }

        const uploadResult = await uploadResponse.json();
        const video_id = uploadResult.video_id;
        if (!video_id) throw new Error('No video_id returned from upload.');

        videoResult.innerText = "🔄 Enhancing video... Please wait.";

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
        if (!processed_id) throw new Error('No processed_video_id returned from enhancement.');

        const videoURL = `/get_video/${processed_id}`;
        videoResult.innerHTML = `<video controls src="${videoURL}" style="width: 100%; margin-top: 1rem;"></video>`;

        // Update the download button for video
        const dl = document.getElementById("downloadVideo");
        dl.href = videoURL;
        dl.style.display = "inline-block";

    } catch (err) {
        videoResult.innerText = `❌ ${err.message}`;
    }
}

function previewOriginalAudio() {
    const fileInput = document.getElementById('audioUploader');
    const file = fileInput.files[0];
    if (!file) return;
    const audioURL = URL.createObjectURL(file);
    
    // Use the correct ID from your audio tab markup
    const audioPlayer = document.getElementById("originalAudioPlayer");
    if (audioPlayer) {
        audioPlayer.src = audioURL;
        audioPlayer.load();
        document.getElementById("originalAudioContainer").style.display = "block";
    } else {
        console.error("Audio player element not found");
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

function acceptSfx(index, emotion, url) {
    selectedSoundFX[index] = { emotion, sfxUrl: url };
    renderSfxDebug();
}

function rejectSfx(index) {
    delete selectedSoundFX[index];
    renderSfxDebug();
}

function replaceSfx(index, url) {
    if (selectedSoundFX[index]) {
        selectedSoundFX[index].sfxUrl = url;
        renderSfxDebug();
    }
}


