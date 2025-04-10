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
            <input type="file" id="audioUploader" accept="audio/*">
            <button class="btn ai-edit-button" onclick="enhanceAudio()">Enhance Audio</button>
            <div id="audioControls"></div>
    
            <div id="audioAnalysisSection" style="display: none;">
                <hr/>
                <h3>🤖 AI Analysis</h3>
                <button class="btn ai-edit-button" onclick="analyzeEnhancedAudio()">📊 Analyze</button>
                <pre id="analysisResults"></pre>
                <a id="downloadEnhanced" style="display:none;" download="enhanced_audio.wav">📥 Download Enhanced Audio</a>
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
                <button class="btn ai-edit-button" onclick="aiCutAudio()">Run AI Cut</button>
                <pre id="aiTranscript"></pre>
                <pre id="aiSuggestedCuts"></pre>
            </div>
        `;
    } else if (tabName === 'video') {
        content.innerHTML = `
            <h2>📹 AI Video Enhancement</h2>
            <input type="file" id="videoUploader" accept="video/*">
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

    audioControls.innerHTML = "🔄 Enhancing... Please wait.";
    const formData = new FormData();
    formData.append("audio", file);

    try {
        const response = await fetch("/audio/enhancement", {
            method: "POST",
            body: formData
        });

        const result = await response.json();
        const enhancedAudioId = result.enhanced_audio;

        if (enhancedAudioId) {
            const audioRes = await fetch(`/get_file/${enhancedAudioId}`);
            const audioBlob = await audioRes.blob();
            enhancedAudioBlob = audioBlob;

            const audioURL = URL.createObjectURL(audioBlob);
            audioControls.innerHTML = `
                <p>✅ Audio enhancement complete!</p>
                <audio controls src="${audioURL}"></audio>
            `;

            document.getElementById("audioAnalysisSection").style.display = "block";
            const downloadLink = document.getElementById("downloadEnhanced");
            downloadLink.href = audioURL;
            downloadLink.style.display = "inline-block";
        } else {
            audioControls.innerHTML = "❌ Failed to enhance audio.";
        }
    } catch (err) {
        audioControls.innerHTML = `❌ Error: ${err.message}`;
    }
}

async function analyzeEnhancedAudio() {
    const analysisContainer = document.getElementById("analysisResults");
    if (!enhancedAudioBlob) {
        alert("Enhance the audio first.");
        return;
    }

    analysisContainer.textContent = "🔍 Analyzing enhanced audio...";

    const formData = new FormData();
    formData.append("audio", enhancedAudioBlob, "enhanced_audio.wav");

    try {
        const response = await fetch("/audio_analysis", {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        analysisContainer.textContent = `
📊 Emotion: ${data.emotion}
📊 Sentiment: ${data.sentiment}
📊 Clarity Score: ${data.clarity_score}
📊 Background Noise: ${data.background_noise}
📊 Speech Rate (WPM): ${data.speech_rate}
        `;
    } catch (err) {
        analysisContainer.textContent = `❌ Analysis failed: ${err.message}`;
    }
}

async function cutAudio() {
    const start = parseFloat(document.getElementById("startTime").value);
    const end = parseFloat(document.getElementById("endTime").value);

    if (isNaN(start) || isNaN(end) || start >= end) {
        return alert("⚠️ Invalid start/end times");
    }

    const res = await fetch('/clip_audio', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ file_id: enhancedAudioId, start_time: start, end_time: end })
    });

    const data = await res.json();
    const cutAudioId = data.clipped_audio;

    const audioRes = await fetch(`/get_file/${cutAudioId}`);
    const blob = await audioRes.blob();
    const url = URL.createObjectURL(blob);

    document.getElementById("cutResult").innerHTML = `<audio controls src="${url}"></audio>`;
    const download = document.getElementById("downloadCut");
    download.href = url;
    download.style.display = "inline-block";
}

async function aiCutAudio() {
    const res = await fetch('/ai_cut_audio', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ file_id: enhancedAudioId })
    });

    const result = await res.json();

    const transcript = result.cleaned_transcript || "No transcript";
    const cuts = result.suggested_cuts?.map(cut =>
        `🗣 "${cut.sentence}" [${cut.start}s - ${cut.end}s] — Certainty: ${cut.certainty_score}`
    ).join("\n") || "No suggested cuts.";

    document.getElementById("aiTranscript").innerText = transcript;
    document.getElementById("aiSuggestedCuts").innerText = cuts;
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
