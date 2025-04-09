function showTab(tabName) {
    const content = document.getElementById('content');
    content.innerHTML = ''; // Clear existing content

    if (tabName === 'transcription') {
        content.innerHTML = `
            <h2>🎙 AI-Powered Transcription</h2>
            <input type="file" id="fileUploader" accept="audio/*,video/*">
            <button onclick="transcribe()">▶ Transcribe</button>
            <pre id="transcriptionResult"></pre>

            <div id="enhancementTools" style="display:none;">
                <hr/>
                <h3>🔧 Enhancement Tools</h3>
                <button onclick="generateCleanTranscript()">🧹 Clean Transcript</button>
                <pre id="cleanTranscript"></pre>

                <button onclick="generateAISuggestions()">🤖 AI Suggestions</button>
                <pre id="aiSuggestions"></pre>

                <button onclick="generateShowNotes()">📝 Show Notes</button>
                <pre id="showNotes"></pre>

                <button onclick="generateQuotes()">💬 Generate Quotes</button>
                <pre id="quotesText"></pre>

                <button onclick="generateQuoteImages()">🖼️ Generate Quote Images</button>
                <div id="quoteImages"></div>
            </div>
        `;
    } else if (tabName === 'audio') {
        content.innerHTML = `
            <h2>🎵 AI Audio Enhancement</h2>
            <input type="file" id="audioUploader" accept="audio/*">
            <button onclick="enhanceAudio()">Enhance Audio</button>
            <div id="audioResult"></div>
        `;
    } else if (tabName === 'video') {
        content.innerHTML = `
            <h2>📹 AI Video Enhancement</h2>
            <input type="file" id="videoUploader" accept="video/*">
            <button onclick="enhanceVideo()">Enhance Video</button>
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
    const res = await fetch('/transcription/clean', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ transcript: fullTranscript })
    });

    const data = await res.json();
    document.getElementById("cleanTranscript").innerText = data.clean_transcript || "No clean result.";
}

async function generateAISuggestions() {
    const res = await fetch('/transcription/ai_suggestions', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ transcript: rawTranscript })
    });

    const data = await res.json();
    document.getElementById("aiSuggestions").innerText = data.ai_suggestions || "No suggestions.";
}

async function generateShowNotes() {
    const res = await fetch('/transcription/show_notes', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ transcript: rawTranscript })
    });

    const data = await res.json();
    document.getElementById("showNotes").innerText = data.show_notes || "No notes.";
}

async function generateQuotes() {
    const res = await fetch('/transcription/quotes', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ transcript: rawTranscript })
    });

    const data = await res.json();
    document.getElementById("quotesText").innerText = data.quotes || "No quotes.";
}

async function generateQuoteImages() {
    const quotes = document.getElementById("quotesText").innerText;
    if (!quotes) return alert("Generate quotes first.");

    const res = await fetch('/transcription/quote_images', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ quotes })
    });

    const data = await res.json();
    const imageDiv = document.getElementById("quoteImages");
    imageDiv.innerHTML = "";

    (data.quote_images || []).forEach(url => {
        const img = document.createElement("img");
        img.src = url;
        img.style.maxWidth = "100%";
        img.style.margin = "10px 0";
        imageDiv.appendChild(img);
    });
}


async function enhanceAudio() {
    const fileInput = document.getElementById('audioUploader');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please upload an audio file.');
        return;
    }

    const formData = new FormData();
    formData.append('audio', file);

    const response = await fetch('/audio/enhancement', {
        method: 'POST',
        body: formData,
    });

    const result = await response.json();
    document.getElementById('audioResult').innerText = JSON.stringify(result, null, 2);
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
