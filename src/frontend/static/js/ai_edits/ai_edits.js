let enhancedAudioBlob = null;
let enhancedAudioId = null;
let isolatedAudioBlob = null;
let isolatedAudioId = null;

let activeAudioBlob = null;
let activeAudioId = null;

// Expose all functions to the global scope
window.showTab = showTab;
window.transcribe = transcribe;
window.generateCleanTranscript = generateCleanTranscript;
window.generateAISuggestions = generateAISuggestions;
window.generateShowNotes = generateShowNotes;
window.generateQuotes = generateQuotes;
window.generateQuoteImages = generateQuoteImages;
window.runOsintSearch = runOsintSearch;
window.generatePodcastIntroOutro = generatePodcastIntroOutro;
window.convertIntroOutroToSpeech = convertIntroOutroToSpeech;
window.enhanceAudio = enhanceAudio;
window.runVoiceIsolation = runVoiceIsolation;
window.analyzeEnhancedAudio = analyzeEnhancedAudio;
window.displayBackgroundAndMix = displayBackgroundAndMix;
window.cutAudio = cutAudio;
window.aiCutAudio = aiCutAudio;
window.applySelectedCuts = applySelectedCuts;
window.cutAudioFromBlob = cutAudioFromBlob;
window.enhanceVideo = enhanceVideo;
window.previewOriginalAudio = previewOriginalAudio;
window.previewOriginalVideo = previewOriginalVideo;
window.acceptSfx = acceptSfx;
window.rejectSfx = rejectSfx;
window.replaceSfx = replaceSfx;

window.CURRENT_USER_ID = localStorage.getItem("user_id");
const urlParams = new URLSearchParams(window.location.search);
const episodeIdFromUrl = urlParams.get("episodeId");
if (episodeIdFromUrl) {
    sessionStorage.setItem("selected_episode_id", episodeIdFromUrl);
}
console.log("Using episode ID:", sessionStorage.getItem("selected_episode_id"));

const CREDIT_COSTS = {
    ai_audio_analysis: 800,
    ai_audio_cutting: 800,
    ai_quotes: 800,
    ai_quote_images: 800,
    ai_suggestions: 800,
    audio_cutting: 500,
    audio_enhancment: 500,
    show_notes: 500,
    transcription: 600,
    clean_transcript: 500,
    translation: 500,
    video_cutting: 500,
    video_enhancement: 500,
    voice_isolation: 500,
    ai_osint: 800,
    ai_intro_outro: 800,
    ai_intro_outro_audio: 500,
};

function labelWithCredits(text, key) {
    const cost = CREDIT_COSTS[key];
    return `${text} <span style="color: gray; font-size: 0.9em;">(${cost} credits)</span>`;
}

function showTab(tabName) {
    // Get all workspace tab buttons
    const workspaceButtons = document.querySelectorAll('.workspace-tab-btn');
    
    // Remove active class from all buttons
    workspaceButtons.forEach(btn => btn.classList.remove('active'));
    
    // Add active class to clicked button
    const clickedButton = document.querySelector(`.workspace-tab-btn[data-workspace="${tabName}"]`);
    if (clickedButton) {
        clickedButton.classList.add('active');
    }

    const content = document.getElementById('content');
    content.innerHTML = '';

    if (tabName === 'transcription') {
        content.innerHTML = `
            <h2>🎙 AI-Powered Transcription</h2>
            <input type="file" id="fileUploader" accept="audio/*,video/*">
            <button class="btn ai-edit-button" onclick="transcribe()">
              ${labelWithCredits("Transcribe", "transcription")}
            </button>
            <div class="result-field">
                <pre id="transcriptionResult"></pre>
            </div>
    
            <div id="enhancementTools";">
                <hr/>
                <h3>Enhancement Tools</h3>
    
                <div class="result-group">
                    <button class="btn ai-edit-button" onclick="generateCleanTranscript()">
                        ${labelWithCredits("Clean Transcript", "clean_transcript")}
                    </button>
                    <div class="result-field">
                        <pre id="cleanTranscriptResult"></pre>
                    </div>
                </div>
    
                <div class="result-group">
                    <button class="btn ai-edit-button" onclick="generateAISuggestions()">
                      ${labelWithCredits("AI Suggestions", "ai_suggestions")}
                    </button>
                    <div class="result-field">
                        <pre id="aiSuggestionsResult"></pre>
                    </div>
                </div>
    
                <div class="result-group">
                    <button class="btn ai-edit-button" onclick="generateShowNotes()">
                      ${labelWithCredits("Show Notes", "show_notes")}
                    </button>
                    <div class="result-field">
                        <pre id="showNotesResult"></pre>
                    </div>
                </div>
    
                <div class="result-group">
                    <button class="btn ai-edit-button" onclick="generateQuotes()">
                      ${labelWithCredits("Generate Quotes", "ai_quotes")}
                    </button>
                    <div class="result-field">
                        <pre id="quotesResult"></pre>
                    </div>
                </div>
    
                <div class="result-group">
                    <button class="btn ai-edit-button" onclick="generateQuoteImages()">
                      ${labelWithCredits("Generate Quote Images", "ai_quote_images")}
                    </button>
                    <div class="result-field">
                        <div id="quoteImagesResult"></div>
                    </div>
                </div>
    
                <div class="result-group">
                    <input type="text" id="guestNameInput" placeholder="Enter guest name..." class="input-field">
                    <button class="btn ai-edit-button" onclick="runOsintSearch()">
                      ${labelWithCredits("OSINT Search", "ai_osint")}
                    </button>
                    <div class="result-field">
                        <pre id="osintResult"></pre>
                    </div>
                </div>
    
                <div class="result-group">
                    <button class="btn ai-edit-button" onclick="generatePodcastIntroOutro()">
                      ${labelWithCredits("Generate Intro/Outro", "ai_intro_outro")}
                    </button>
                    <div class="result-field">
                        <pre id="introOutroResult"></pre>
                    </div>
                    <button class="btn ai-edit-button" onclick="convertIntroOutroToSpeech()">
                      ${labelWithCredits("Convert to Speech", "ai_intro_outro_audio")}
                    </button>
                </div>
            </div>
        `;
    }else if (tabName === 'audio') {
        content.innerHTML = `
            <h2>AI Audio Enhancement</h2>
            <input type="file" id="audioUploader" accept="audio/*" onchange="previewOriginalAudio()">
            <div id="originalAudioContainer" style="display: none; margin-bottom: 1rem;">
                <p><strong>Original Audio</strong></p>
                <audio id="originalAudioPlayer" controls style="width: 100%"></audio>
            </div>
    
            <div style="margin-top: 1rem; padding: 1rem; border: 1px solid #ddd; border-radius: 12px;">
                <h3>Choose Audio Processing Method</h3>
                <p style="margin-bottom: 1rem;">Select one of the following enhancements:</p>
    
                <div id="voiceIsolationSection" style="margin-bottom: 1.5rem;">
                    <h4><strong>Voice Isolation (Powered by ElevenLabs)</strong></h4>
                    <button class="btn ai-edit-button" onclick="runVoiceIsolation()">
                        ${labelWithCredits("Isolate Voice", "voice_isolation")}
                    </button>
                    <div id="isolatedVoiceResult" style="margin-top: 1rem;"></div>
                    <a id="downloadIsolatedVoice"
                       class="inline-block mt-2 bg-orange-500 text-white px-4 py-2 rounded-2xl shadow hover:shadow-lg transition"
                       style="display: none;"
                       download="isolated_voice.wav">
                       Download Isolated Voice
                    </a>
                </div>
    
                <div id="audioEnhancementSection">
                    <h4><strong>Audio Enhancement (Noise Reduction & Normalization)</strong></h4>
                    <button class="btn ai-edit-button" onclick="enhanceAudio()">
                      ${labelWithCredits("Enhance Audio", "audio_enhancment")}
                    </button>
                    <div id="audioControls" style="margin-top: 1rem;"></div>
                </div>
            </div>
    
            <div id="audioAnalysisSection" style="display: none;">
                <hr/>
                <h3>AI Analysis</h3>
                <button class="btn ai-edit-button" onclick="analyzeEnhancedAudio()">
                  ${labelWithCredits("Analyze", "ai_audio_analysis")}
                </button>
                <pre id="analysisResults"></pre>
    
                <button id="mixBackgroundBtn"
                        class="btn ai-edit-button"
                        style="display: none; margin-top: 1rem;"
                        onclick="displayBackgroundAndMix()">
                  Mix Background & Preview
                </button>
    
                <div id="backgroundPreview" style="margin-top: 1rem;"></div>
                <div id="soundEffectTimeline" style="margin-top: 1rem;"></div>
    
                <a id="downloadEnhanced"
                   class="btn ai-edit-button"
                   download="processed_audio.wav"
                   style="display: none;">
                   Download Processed Audio
                </a>
            </div>
    
            <div id="audioCuttingSection" style="display: none;">
                <hr/>
                <h3>Audio Cutting</h3>
                <label>Start: <input type="number" id="startTime" min="0" step="0.1"></label>
                <label>End: <input type="number" id="endTime" min="0" step="0.1"></label>
                <button class="btn ai-edit-button" onclick="cutAudio()">
                  ${labelWithCredits("Cut", "audio_cutting")}
                </button>
                <div id="cutResult"></div>
                <a id="downloadCut" class="btn ai-edit-button" download="cut_audio.wav">
                  Download Cut
                </a>
            </div>
    
            <div id="aiCuttingSection" style="display: none;">
                <hr/>
                <h3>AI Cutting + Transcript</h3>
                <button class="btn ai-edit-button" onclick="aiCutAudio()">
                  ${labelWithCredits("Run AI Cut", "ai_audio_cutting")}
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
            <h2>AI Video Enhancement</h2>
            <h2>AI Video Enhancement</h2>
            <input type="file" id="videoUploader" accept="video/*" onchange="previewOriginalVideo()">
            <div id="originalVideoContainer" style="display: none; margin-bottom: 1rem;">
                <p><strong>Original Video</strong></p>
                <p><strong>Original Video</strong></p>
                <video id="originalVideoPlayer" controls style="width: 100%"></video>
            </div>
            <button class="btn ai-edit-button" onclick="enhanceVideo()">
            ${labelWithCredits("Enhance Video", "video_enhancement")}
            ${labelWithCredits("Enhance Video", "video_enhancement")}
            </button>
            <div id="videoResult"></div>
            <a id="downloadVideo" class="btn ai-edit-button" download="enhanced_video.mp4" style="display: none;">
            Download Enhanced Video
            </a>
        `;
    }
}

// Add event listeners when the page loads
document.addEventListener('DOMContentLoaded', function() {
    const workspaceButtons = document.querySelectorAll('.workspace-tab-btn');
    
    workspaceButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-workspace');
            showTab(tabName);
        });
    });

    // Show transcription tab by default
    showTab('transcription');
});

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

    const episodeId = sessionStorage.getItem("selected_episode_id");
    if (!episodeId) {
        alert("No episode selected.");
        return;
    }

    showSpinner("transcriptionResult");
    const formData = new FormData();
    formData.append('file', file);
    formData.append('episode_id', episodeId);  // Include episode ID

    try {
        const response = await fetch('/transcription/transcribe', {
            method: 'POST',
            body: formData,
        });

        hideSpinner("transcriptionResult");

        if (response.status === 403) {
            const errorData = await response.json();
            resultContainer.innerHTML = `
                <p style="color: red;">${errorData.error || "You don't have enough credits."}</p>
                ${errorData.redirect ? `<a href="${errorData.redirect}" class="btn ai-edit-button">Go to Store</a>` : ""}
            `;
            return;
        }

        if (response.ok) {
            const result = await response.json();
            rawTranscript = result.raw_transcription || "";
            fullTranscript = result.full_transcript || "";
        
            resultContainer.innerText = rawTranscript;
            document.getElementById("enhancementTools").style.display = "block";
        
            if (result.credit_warning) {
                alert("Transcription completed, but your credits are too low. Please visit the store.");
            }
        
        }
    } catch (error) {
        hideSpinner("transcriptionResult");
        resultContainer.innerText = `Transcription failed: ${error.message}`;
    }
}

async function generateCleanTranscript() {
    const containerId = "cleanTranscriptResult";
    const container = document.getElementById(containerId);

    showSpinner(containerId);

    try {
        const res = await fetch("/transcription/clean", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ transcript: fullTranscript })
        });

        if (res.status === 403) {
            const errorData = await res.json();
            container.innerHTML = `
                <p style="color: red;">${errorData.error || "You don't have enough credits."}</p>
                ${errorData.redirect ? `<a href="${errorData.redirect}" class="btn ai-edit-button">Go to Store</a>` : ""}
            `;
            return;
        }

        const data = await res.json();
        container.innerText = data.clean_transcript || "No clean result.";
    } catch (err) {
        container.innerText = "Failed to clean transcript. Server says: " + err.message;
    }
}
async function generateAISuggestions() {
    const containerId = "aiSuggestionsResult";
    const container = document.getElementById(containerId);

    showSpinner(containerId);

    try {
        const res = await fetch("/transcription/ai_suggestions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ transcript: rawTranscript })
        });

        const data = await res.json();
        if (res.ok) {
            const primary = data.primary_suggestions || "";
            const additional = (data.additional_suggestions || []).join("\n");
            container.innerText = [primary, additional].filter(Boolean).join("\n\n") || "No suggestions.";

            // ✅ Consume credits only after success
            await consumeStoreCredits("ai_suggestions");
        } else {
            container.innerText = `Error: ${res.status} - ${res.statusText}`;
        }
    } catch (err) {
        container.innerText = "Failed to generate suggestions: " + err.message;
    }
}

async function generateShowNotes() {
    const containerId = "showNotesResult";
    const container = document.getElementById(containerId);

    showSpinner(containerId);

    try {
        const res = await fetch("/transcription/show_notes", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ transcript: rawTranscript })
        });

        const data = await res.json();
        if (res.ok) {
            container.innerText = data.show_notes || "No notes.";

            // ✅ Consume credits only after success
            await consumeStoreCredits("show_notes");
        } else {
            container.innerText = `Error: ${res.status} - ${res.statusText}`;
        }
    } catch (err) {
        container.innerText = "Failed to generate show notes: " + err.message;
    }
}

async function generateQuotes() {
    const containerId = "quotesResult";
    const container = document.getElementById(containerId);

    showSpinner(containerId);

    try {
        const res = await fetch("/transcription/quotes", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ transcript: rawTranscript })
        });

        const data = await res.json();
        if (res.ok) {
            container.innerText = data.quotes || "No quotes.";

            // ✅ Consume credits only after success
            await consumeStoreCredits("ai_quotes");
        } else {
            container.innerText = `Error: ${res.status} - ${res.statusText}`;
        }
    } catch (err) {
        container.innerText = "Failed to generate quotes: " + err.message;
    }
}

async function generateQuoteImages() {
    const containerId = "quoteImagesResult";
    const container = document.getElementById(containerId);

    const quotes = document.getElementById("quotesResult").innerText;
    if (!quotes) {
        alert("Generate quotes first.");
        return;
    }

    showSpinner(containerId);

    try {
        const res = await fetch("/transcription/quote_images", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ quotes })
        });

        const data = await res.json();
        if (res.ok) {
            container.innerHTML = "";

            (data.quote_images || []).forEach(url => {
                const img = document.createElement("img");
                img.src = url;
                img.style.maxWidth = "100%";
                img.style.margin = "10px 0";
                container.appendChild(img);
            });

            // ✅ Consume credits only after success
            await consumeStoreCredits("ai_quote_images");
        } else {
            container.innerText = `Error: ${res.status} - ${res.statusText}`;
        }
    } catch (err) {
        container.innerText = "Failed to generate quote images: " + err.message;
    }
}

async function fetchAudioFromBlobUrl(blobUrl) {
    try {
        const res = await fetch(blobUrl);
        if (!res.ok) throw new Error(`Failed to fetch audio: ${res.statusText}`);
        const blob = await res.blob();
        const objectUrl = URL.createObjectURL(blob);
        return { blob, objectUrl };
    } catch (err) {
        console.error("Error fetching audio from blob URL:", err);
        throw err;
    }
}

async function runOsintSearch() {
    const containerId = "osintResult";
    const container = document.getElementById(containerId);

    const guestName = document.getElementById("guestNameInput").value;
    if (!guestName.trim()) {
        alert("Please enter a guest name.");
        return;
    }

    showSpinner(containerId);

    try {
        const response = await fetch("/transcription/osint_lookup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ guest_name: guestName })
        });

        const data = await response.json();
        container.innerText = data.osint_info || "No info found.";

        // ✅ Consume credits only after success
        await consumeStoreCredits("ai_osint");
    } catch (err) {
        container.innerText = `Failed: ${err.message}`;
    }
}

async function generatePodcastIntroOutro() {
    const containerId = "introOutroResult";
    const container = document.getElementById(containerId);

    const guestName = document.getElementById("guestNameInput").value;
    if (!guestName.trim()) return alert("Please enter a guest name.");
    if (!rawTranscript) return alert("No transcript available yet.");

    showSpinner(containerId);

    try {
        const res = await fetch("/transcription/generate_intro_outro", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                guest_name: guestName,
                transcript: rawTranscript
            })
        });

        const data = await res.json();
        container.innerText = data.script || "No result.";

        // ✅ Consume credits only after success
        await consumeStoreCredits("ai_intro_outro");
    } catch (err) {
        container.innerText = `Failed: ${err.message}`;
    }
}

async function convertIntroOutroToSpeech() {
    const containerId = "introOutroResult";
    const container = document.getElementById(containerId);

    const script = container.innerText;
    if (!script.trim()) return alert("No script to convert.");

    container.innerText += "\n\nGenerating voice...";

    try {
        const res = await fetch("/transcription/intro_outro_audio", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ script })
        });

        const data = await res.json();
        if (data.audio_base64) {
            const audio = document.createElement("audio");
            audio.controls = true;
            audio.src = data.audio_base64;

            const download = document.createElement("a");
            download.href = data.audio_base64;
            download.download = "intro_outro.mp3";
            download.className = "btn ai-edit-button";
            download.innerText = "Download Intro/Outro Audio";

            container.appendChild(document.createElement("hr"));
            container.appendChild(audio);
            container.appendChild(download);

            // ✅ Consume credits only after success
            await consumeStoreCredits("ai_intro_outro_audio");
        } else {
            throw new Error(data.error || "Unknown error");
        }
    } catch (err) {
        container.innerText += `\nFailed to convert to audio: ${err.message}`;
    }
}

async function enhanceAudio() {
    const containerId = "audioControls";
    const container = document.getElementById(containerId);

    const input = document.getElementById('audioUploader');
    const file = input.files[0];
    if (!file) return alert("Upload an audio file first.");

    const episodeId = sessionStorage.getItem("selected_episode_id");
    if (!episodeId) return alert("No episode selected.");

    showSpinner(containerId);

    try {
        const formData = new FormData();
        formData.append("audio", file);
        formData.append("episode_id", episodeId);

        const response = await fetch("/audio/enhancement", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            container.innerHTML = `Error: ${result.error || response.statusText}`;
            return;
        }

        const blobUrl = result.enhanced_audio_url;

        const audioRes = await fetch(`/get_enhanced_audio?url=${encodeURIComponent(blobUrl)}`);
        const blob = await audioRes.blob();
        const url = URL.createObjectURL(blob);

        enhancedAudioBlob = blob;
        activeAudioBlob = blob;
        activeAudioId = "external";

        container.innerHTML = `
            <p>Audio enhancement complete!</p>
            <audio controls src="${url}" style="width: 100%;"></audio>
        `;

        document.getElementById("audioAnalysisSection").style.display = "block";
        document.getElementById("audioCuttingSection").style.display = "block";
        document.getElementById("aiCuttingSection").style.display = "block";

        const dl = document.getElementById("downloadEnhanced");
        dl.href = url;
        dl.style.display = "inline-block";

        // ✅ Consume credits only after success
        await consumeStoreCredits("audio_enhancment");
    } catch (err) {
        container.innerHTML = `Error: ${err.message}`;
    }
}

async function runVoiceIsolation() {
    const containerId = "isolatedVoiceResult";
    const container = document.getElementById(containerId);

    const input = document.getElementById('audioUploader');
    const file = input.files[0];
    if (!file) return alert("Upload an audio file first.");

    const episodeId = sessionStorage.getItem("selected_episode_id");
    if (!episodeId) return alert("No episode selected.");

    showSpinner(containerId);

    try {
        const formData = new FormData();
        formData.append("audio", file);
        formData.append("episode_id", episodeId);

        const response = await fetch("/transcription/voice_isolate", {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Voice isolation failed.");

        // ✅ Only now consume credits, since we know it worked
        await consumeStoreCredits("voice_isolation");

        const blobUrl = data.isolated_blob_url;
        const audioRes = await fetch(`/transcription/get_isolated_audio?url=${encodeURIComponent(blobUrl)}`);
        const blob = await audioRes.blob();
        const url = URL.createObjectURL(blob);

        isolatedAudioBlob = blob;
        activeAudioBlob = blob;
        activeAudioId = "external";

        container.innerHTML = `
            <p>Isolated Audio</p>
            <audio controls src="${url}" style="width: 100%;"></audio>
        `;

        document.getElementById("audioAnalysisSection").style.display = "block";
        document.getElementById("audioCuttingSection").style.display = "block";
        document.getElementById("aiCuttingSection").style.display = "block";

        const mixBtn = document.getElementById("mixBackgroundBtn");
        mixBtn.style.display = "none";

        const dl = document.getElementById("downloadIsolatedVoice");
        dl.href = url;
        dl.style.display = "inline-block";

    } catch (err) {
        console.error("Voice isolation failed:", err);
        container.innerText = `Isolation failed: ${err.message}`;
    }
}

async function analyzeEnhancedAudio() {
    const containerId = "analysisResults";
    const container = document.getElementById(containerId);
    const timeline = document.getElementById("soundEffectTimeline");
    const mixBtn = document.getElementById("mixBackgroundBtn");

    if (!activeAudioBlob) {
        return alert("No audio loaded. Enhance or Isolate first.");
    }

    showSpinner(containerId);

    try {
        const fd = new FormData();
        fd.append("audio", activeAudioBlob, "processed_audio.wav");

        const res = await fetch("/audio_analysis", { method: "POST", body: fd });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || res.statusText);

        container.innerText = `
            Sentiment:     ${data.sentiment ?? "–"}
            Clarity Score: ${data.clarity_score ?? "–"}
            Noise Level:   ${data.background_noise ?? "–"}
            Dominant Emo:  ${data.dominant_emotion}
        `;

        timeline.innerHTML = "";
        renderSoundSuggestions(data, timeline);

        window.analysisData = {
            emotion: data.dominant_emotion,
            audioBlob: activeAudioBlob
        };

        mixBtn.style.display = "inline-block";

        // ✅ Consume credits only after success
        await consumeStoreCredits("ai_audio_analysis");
    } catch (err) {
        container.innerText = `Analysis failed: ${err.message}`;
    }
}

/* Hjälper att rendera suggestion-listan */
function renderSoundSuggestions(data, timeline) {
    timeline.innerHTML = "<h4>AI-Driven Sound Suggestions</h4>";
    window.selectedSoundFX = {};

    (data.sound_effect_suggestions || []).forEach((entry, i) => {
        const sfxList = entry.sfx_options || [];
        const container = document.createElement("div");
        container.className = "sound-suggestion";
        container.innerHTML = `
            <p><strong>Text:</strong> ${entry.timestamp_text}</p>
            <p><strong>Emotion:</strong> ${entry.emotion}</p>
            ${sfxList.length ? `<audio controls src="${sfxList[0]}" class="sfx-preview"></audio>` : "<em>No preview.</em>"}
        `;
        timeline.appendChild(container);
        if (sfxList.length) {
            window.selectedSoundFX[i] = { emotion: entry.emotion, sfxUrl: sfxList[0] };
        }
    });
}

async function displayBackgroundAndMix() {
    const preview = document.getElementById("backgroundPreview");
    const mixBtn  = document.getElementById("mixBackgroundBtn");
    const dl      = document.getElementById("downloadEnhanced");
    const { emotion, audioBlob } = window.analysisData || {};
  
    if (!emotion || !audioBlob) {
      return alert("Run analysis first!");
    }
  
    // Disable button & show spinner text
    mixBtn.disabled  = true;
    mixBtn.innerText = "Generating…";
    preview.innerHTML = "";
  
    const fd = new FormData();
    fd.append("audio",   audioBlob, "processed_audio.wav");
    fd.append("emotion", emotion);
  
    try {
      const res  = await fetch("/audio_background_mix", { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || res.statusText);
  
      // ONLY render the mixed overlay:
      if (data.merged_audio) {
        preview.innerHTML = `
          <h4>Mixed Preview</h4>
          <audio controls src="${data.merged_audio}" style="width:100%;"></audio>
        `;
        // Update download link
        dl.href          = data.merged_audio;
        dl.style.display = "inline-block";
      }

      // ✅ Consume credits only after success
      await consumeStoreCredits("ai_audio_analysis");
    } catch (err) {
      preview.innerText = `Error: ${err.message}`;
    } finally {
      // Restore button
      mixBtn.disabled  = false;
      mixBtn.innerText = "Mix Background & Preview";
    }
  }

async function cutAudio() {
    const startInput = document.getElementById("startTime");
    const endInput = document.getElementById("endTime");
    const cutResult = document.getElementById("cutResult");
    const dl = document.getElementById("downloadCut");

    const start = parseFloat(startInput.value);
    const end = parseFloat(endInput.value);

    const episodeId = sessionStorage.getItem("selected_episode_id");
    if (!episodeId || !activeAudioBlob) return alert("No audio or episode selected.");
    if (isNaN(start) || isNaN(end) || start >= end) return alert("Invalid timestamps.");

    const formData = new FormData();
    formData.append("audio", new File([activeAudioBlob], "clip.wav", { type: "audio/wav" }));
    formData.append("episode_id", episodeId);
    formData.append("start", start);
    formData.append("end", end);

    try {
        const response = await fetch("/cut_from_blob", {
            method: "POST",
            body: formData
        });

        const result = await response.json();
        if (!response.ok || !result.clipped_audio_url) {
            throw new Error(result.error || "Clipping failed.");
        }

        const proxyUrl = `/get_clipped_audio?url=${encodeURIComponent(result.clipped_audio_url)}`;
        const audioRes = await fetch(proxyUrl);
        if (!audioRes.ok) throw new Error("Failed to fetch clipped audio.");
        const blob = await audioRes.blob();
        const url = URL.createObjectURL(blob);

        cutResult.innerHTML = `<audio controls src="${url}" style="width: 100%;"></audio>`;
        dl.href = url;
        dl.download = "clipped_audio.wav";
        dl.style.display = "inline-block";

        activeAudioBlob = blob;
        activeAudioId = "external";

        // ✅ Consume credits only after success
        await consumeStoreCredits("audio_cutting");
    } catch (err) {
        alert(`Cut failed: ${err.message}`);
    }
}

async function aiCutAudio() {
    const episodeId = sessionStorage.getItem("selected_episode_id") || localStorage.getItem("selected_episode_id");

    if (!episodeId) {
        alert("No episode selected.");
        return;
    }

    if (!activeAudioBlob && !activeAudioId) {
        alert("No audio loaded.");
        return;
    }

    const containerIdTranscript = "aiTranscript";
    const containerTranscript = document.getElementById(containerIdTranscript);
    const containerIdCuts = "aiSuggestedCuts";
    const containerCuts = document.getElementById(containerIdCuts);

    showSpinner(containerIdTranscript);
    containerCuts.innerHTML = "";

    try {
        let response, data;

        if (activeAudioId === "external") {
            const formData = new FormData();
            formData.append("audio", new File([activeAudioBlob], "ai_cut.wav", { type: "audio/wav" }));
            formData.append("episode_id", episodeId);

            response = await fetch("/ai_cut_from_blob", {
                method: "POST",
                body: formData
            });
        } else {
            response = await fetch("/ai_cut_audio", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    file_id: activeAudioId,
                    episode_id: episodeId
                })
            });
        }

        data = await response.json();
        if (!response.ok) throw new Error(data.error || "AI Cut failed");

        containerTranscript.innerText = data.cleaned_transcript || "No transcript available.";

        const suggestedCuts = data.suggested_cuts || [];
        if (!suggestedCuts.length) {
            containerCuts.innerText = "No suggested cuts found.";
            return;
        }

        containerCuts.innerHTML = "";
        window.selectedAiCuts = {};

        suggestedCuts.forEach((cut, index) => {
            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.checked = true;
            checkbox.dataset.index = index;
            checkbox.onchange = () => {
                if (checkbox.checked) {
                    window.selectedAiCuts[index] = cut;
                } else {
                    delete window.selectedAiCuts[index];
                }
            };
            window.selectedAiCuts[index] = cut;

            const label = document.createElement("label");
            label.innerText = ` "${cut.sentence}" (${cut.start}s - ${cut.end}s) | Confidence: ${cut.certainty_score.toFixed(2)}`;

            const div = document.createElement("div");
            div.appendChild(checkbox);
            div.appendChild(label);
            containerCuts.appendChild(div);
        });

        const applyBtn = document.createElement("button");
        applyBtn.className = "btn ai-edit-button";
        applyBtn.innerText = "Apply AI Cuts";
        applyBtn.onclick = applySelectedCuts;

        containerCuts.appendChild(applyBtn);

        // ✅ Consume credits only after success
        await consumeStoreCredits("ai_audio_cutting");
    } catch (err) {
        containerTranscript.innerText = "Failed to process audio.";
        alert(`AI Cut failed: ${err.message}`);
    }
}

async function applySelectedCuts() {
    const cuts = Object.values(window.selectedAiCuts || {});
    if (!cuts.length) {
        alert("No cuts selected.");
        return;
    }

    const episodeId = sessionStorage.getItem("selected_episode_id") || localStorage.getItem("selected_episode_id");


    try {
        let blobUrl;

        // Skicka till rätt backend beroende på var ljudet finns
        if (activeAudioId === "external") {
            const formData = new FormData();
            formData.append("audio", new File([activeAudioBlob], "cleaned.wav", { type: "audio/wav" }));
            formData.append("episode_id", episodeId);
            formData.append("cuts", JSON.stringify(cuts));

            const response = await fetch("/apply_ai_cuts_from_blob", {
                method: "POST",
                body: formData
            });

            const result = await response.json();
            if (!response.ok) throw new Error(result.error || "Apply failed");
            blobUrl = result.cleaned_file_url;
        } else {
            const response = await fetch('/apply_ai_cuts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    file_id: activeAudioId,
                    cuts: cuts.map(c => ({ start: c.start, end: c.end })),
                    episode_id: episodeId
                })
            });

            const result = await response.json();
            if (!response.ok) throw new Error(result.error || "Apply failed");
            blobUrl = result.cleaned_file_url;
        }

        // Använd backend-proxy för att undvika CORS
        const proxyUrl = `/get_clipped_audio?url=${encodeURIComponent(blobUrl)}`;
        const audioRes = await fetch(proxyUrl);
        if (!audioRes.ok) throw new Error("Failed to fetch clipped audio.");
        const blob = await audioRes.blob();
        const url = URL.createObjectURL(blob);

        //  Visa spelare och ladda ner-knapp
        const section = document.getElementById("aiCuttingSection");
        section.appendChild(document.createElement("hr"));

        const player = document.createElement("audio");
        player.controls = true;
        player.src = url;
        section.appendChild(player);

        const dl = document.createElement("a");
        dl.href = url;
        dl.download = "ai_cleaned_audio.wav";
        dl.className = "btn ai-edit-button";
        dl.innerText = "Download Cleaned Audio";
        section.appendChild(dl);

        // Uppdatera aktiv blob
        activeAudioBlob = blob;
        activeAudioId = "external";
    } catch (err) {
        alert(`Apply failed: ${err.message}`);
    }
}

async function cutAudioFromBlob() {
    const startInput = document.getElementById("startTime");
    const endInput = document.getElementById("endTime");
    const cutResult = document.getElementById("cutResult");
    const dl = document.getElementById("downloadCut");

    const start = parseFloat(startInput.value);
    const end = parseFloat(endInput.value);

    const episodeId = sessionStorage.getItem("selected_episode_id");
    if (!episodeId || !activeAudioBlob) return alert("No audio or episode selected.");
    if (isNaN(start) || isNaN(end) || start >= end) return alert("Invalid timestamps.");

    const formData = new FormData();
    formData.append("audio", new File([activeAudioBlob], "clip.wav", { type: "audio/wav" }));
    formData.append("episode_id", episodeId);
    formData.append("start", start);
    formData.append("end", end);

    try {
        const response = await fetch("/cut_from_blob", {
            method: "POST",
            body: formData
        });

        const result = await response.json();
        if (!response.ok || !result.clipped_audio_url) {
            throw new Error(result.error || "Clipping failed.");
        }

        const { blob, objectUrl: url } = await fetchAudioFromBlobUrl(result.clipped_audio_url);

        cutResult.innerHTML = `<audio controls src="${url}" style="width: 100%;"></audio>`;
        dl.href = url;
        dl.download = "clipped_audio.wav";
        dl.style.display = "inline-block";

        activeAudioBlob = blob;
        activeAudioId = "external";

        // ✅ Consume credits only after success
        await consumeStoreCredits("audio_cutting");
    } catch (err) {
        alert(`Cut failed: ${err.message}`);
    }
}

async function loadAudioEditsForEpisode(episodeId) {
    const container = document.getElementById("editHistory");
    container.innerHTML = "<p>Loading audio edits...</p>";

    try {
        const response = await fetch(`/edits/${episodeId}`);
        const edits = await response.json();

        if (!Array.isArray(edits) || edits.length === 0) {
            container.innerHTML = "<p>No edits found.</p>";
            return;
        }

        container.innerHTML = "<h4>Audio Edit History</h4>";
        edits.forEach(edit => {
            const div = document.createElement("div");
            div.classList.add("edit-entry");

            const audioPlayer = edit.clipUrl
                ? `<audio controls src="${edit.clipUrl}" style="width: 100%;"></audio>`
                : "<em>No audio preview</em>";

            div.innerHTML = `
                <strong>${edit.editType}</strong> - ${edit.clipName ?? "Untitled"}<br/>
                <small>Created: ${new Date(edit.createdAt).toLocaleString()}</small><br/>
                ${audioPlayer}
                ${edit.transcript ? `<p><strong>Transcript:</strong> ${edit.transcript}</p>` : ""}
            `;

            container.appendChild(div);
        });
    } catch (err) {
        container.innerHTML = `<p>Error loading edits: ${err.message}</p>`;
    }
}

async function enhanceVideo() {
    const fileInput = document.getElementById("videoUploader");
    const file = fileInput.files[0];
    if (!file) {
        alert("Please upload a video file.");
        return;
    }

    const containerId = "videoResult";
    const container = document.getElementById(containerId);
    showSpinner(containerId);

    try {
        const formData = new FormData();
        formData.append("video", file);

        const uploadResponse = await fetch("/ai_videoedit", {
            method: "POST",
            body: formData,
        });

        if (!uploadResponse.ok) {
            throw new Error(`Video upload failed: ${uploadResponse.statusText}`);
        }

        const uploadResult = await uploadResponse.json();
        const video_id = uploadResult.video_id;
        if (!video_id) throw new Error("No video_id returned from upload.");

        const enhanceResponse = await fetch("/ai_videoenhance", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ video_id }),
        });

        if (!enhanceResponse.ok) {
            throw new Error(`Enhancement failed: ${enhanceResponse.statusText}`);
        }

        const enhanceResult = await enhanceResponse.json();
        const processed_id = enhanceResult.processed_video_id;
        if (!processed_id) throw new Error("No processed_video_id returned from enhancement.");

        const videoURL = `/get_video/${processed_id}`;
        container.innerHTML = `
            <video controls src="${videoURL}" style="width: 100%; margin-top: 1rem;"></video>
        `;

        const dl = document.getElementById("downloadVideo");
        dl.href = videoURL;
        dl.style.display = "inline-block";

        // ✅ Consume credits only after success
        await consumeStoreCredits("video_enhancement");
    } catch (err) {
        container.innerText = `Error: ${err.message}`;
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

async function fetchStoreCredits(userId) {
    try {
        const response = await fetch(`/api/credits/check?user_id=${userId}`);
        if (response.ok) {
            const data = await response.json();
            document.getElementById("storeCredits").innerText = `Available Credits: ${data.availableCredits}`;
        } else {
            alert("Failed to fetch user credits.");
        }
    } catch (error) {
        console.error("Error fetching user credits:", error);
    }
}

async function consumeStoreCredits(featureKey) {
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

    // ✅ Update header credits
    if (window.populateStoreCredits) {
        await window.populateStoreCredits();
    }

    return result.data;
}


function acceptSfx(index, emotion, url) {
    selectedSoundFX[index] = { emotion, sfxUrl: url };
}

function rejectSfx(index) {
    delete selectedSoundFX[index];
}

function replaceSfx(index, url) {
    if (selectedSoundFX[index]) {
        selectedSoundFX[index].sfxUrl = url;
    }
}

function showSpinner(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '<div class="spinner"></div>';
    }
}

function hideSpinner(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '';
    }
}
