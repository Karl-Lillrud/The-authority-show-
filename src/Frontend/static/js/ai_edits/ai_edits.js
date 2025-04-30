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
window.CURRENT_EPISODE_ID = localStorage.getItem("selected_episode_id"); 



const CREDIT_COSTS = {
    ai_audio_analysis: 800,
    ai_audio_cutting: 800,
    ai_quotes: 800,
    ai_qoute_images: 800,
    ai_suggestions: 800,
    audio_cutting: 500,
    audio_enhancment: 500,
    show_notes: 500,
    transcription: 500,
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
    
                <div class="result-group">
                    <input type="text" id="guestNameInput" placeholder="Enter guest name..." class="input-field">
                    <button class="btn ai-edit-button" onclick="runOsintSearch()">
                      ${labelWithCredits("🕵️ OSINT Search", "ai_osint")}
                    </button>
                    <div class="result-field">
                        <pre id="osintResult"></pre>
                    </div>
                </div>
    
                <div class="result-group">
                    <button class="btn ai-edit-button" onclick="generatePodcastIntroOutro()">
                      ${labelWithCredits("🎙 Generate Intro/Outro", "ai_intro_outro")}
                    </button>
                    <div class="result-field">
                        <pre id="introOutroResult"></pre>
                    </div>
                    <button class="btn ai-edit-button" onclick="convertIntroOutroToSpeech()">
                      ${labelWithCredits("🔊 Convert to Speech", "ai_intro_outro_audio")}
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

    try {
        await consumeStoreCredits("transcription");
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
            const errorData = await response.json();
            resultContainer.innerText = `❌ Error: ${errorData.error || response.statusText}`;
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
    const suggestionsEl = document.getElementById("aiSuggestionsResult");

    try {
        await consumeStoreCredits("ai_suggestions");

        const res = await fetch('/transcription/ai_suggestions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transcript: rawTranscript })
        });

        if (res.ok) {
            const data = await res.json();
            const primary = data.primary_suggestions || "";
            const additional = (data.additional_suggestions || []).join("\n");

            suggestionsEl.innerText = [primary, additional].filter(Boolean).join("\n\n") || "No suggestions.";
        } else {
            suggestionsEl.innerText = `❌ Error: ${res.status} - ${res.statusText}`;
        }
    } catch (err) {
        suggestionsEl.innerText = "❌ Not enough credits: " + err.message;
    }
}


async function generateShowNotes() {
    try {
        await consumeStoreCredits("show_notes");

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
        await consumeStoreCredits("ai_quotes");

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
        await consumeStoreCredits("ai_qoute_images");

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
    const guestName = document.getElementById("guestNameInput").value;
    const resultEl = document.getElementById("osintResult");

    if (!guestName.trim()) {
        alert("Please enter a guest name.");
        return;
    }

    try {
        await consumeStoreCredits("ai_osint");
        resultEl.innerText = "🔍 Searching OSINT info...";

        const response = await fetch("/transcription/osint_lookup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ guest_name: guestName })
        });

        const data = await response.json();
        resultEl.innerText = data.osint_info || "No info found.";
    } catch (err) {
        resultEl.innerText = `❌ Failed: ${err.message}`;
    }
}

async function generatePodcastIntroOutro() {
    const guestName = document.getElementById("guestNameInput").value;
    const resultEl = document.getElementById("introOutroResult");

    if (!guestName.trim()) return alert("Please enter a guest name.");
    if (!rawTranscript) return alert("No transcript available yet.");

    try {
        await consumeStoreCredits("ai_intro_outro");
        resultEl.innerText = "📝 Generating intro and outro...";

        const res = await fetch("/transcription/generate_intro_outro", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                guest_name: guestName,
                transcript: rawTranscript  // already stored when transcribed
            })
        });

        const data = await res.json();
        resultEl.innerText = data.script || "No result.";
    } catch (err) {
        resultEl.innerText = `❌ Failed: ${err.message}`;
    }
}

async function convertIntroOutroToSpeech() {
    const script = document.getElementById("introOutroResult").innerText;
    if (!script.trim()) return alert("No script to convert.");

    const resultEl = document.getElementById("introOutroResult");
    resultEl.innerText += "\n\n🔊 Generating voice...";

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
            download.innerText = "📥 Download Intro/Outro Audio";

            resultEl.appendChild(document.createElement("hr"));
            resultEl.appendChild(audio);
            resultEl.appendChild(download);
        } else {
            throw new Error(data.error || "Unknown error");
        }
    } catch (err) {
        resultEl.innerText += `\n❌ Failed to convert to audio: ${err.message}`;
    }
}

async function enhanceAudio() {
    const input = document.getElementById('audioUploader');
    const audioControls = document.getElementById('audioControls');
    const file = input.files[0];
    if (!file) return alert("Upload an audio file first.");

    const episodeId = sessionStorage.getItem("selected_episode_id") || localStorage.getItem("selected_episode_id");

    if (!episodeId) return alert("❌ No episode selected.");

    try {
        await consumeStoreCredits("audio_enhancment");
    } catch (err) {
        audioControls.innerHTML = `❌ Not enough credits: ${err.message}`;
        return;
    }

    const formData = new FormData();
    formData.append("audio", file);
    formData.append("episode_id", episodeId);

    audioControls.innerHTML = "🔄 Enhancing... Please wait.";

    try {
        const response = await fetch("/audio/enhancement", {
            method: "POST",
            body: formData
        });

        const result = await response.json();
        const blobUrl = result.enhanced_audio_url;

        // ✅ Use backend proxy to avoid CORS
        const audioRes = await fetch(`/get_enhanced_audio?url=${encodeURIComponent(blobUrl)}`);
        const blob = await audioRes.blob();
        const url = URL.createObjectURL(blob);

        enhancedAudioBlob = blob;
        activeAudioBlob = blob;
        activeAudioId = "external";

        audioControls.innerHTML = `
            <p>Audio enhancement complete!</p>
            <audio controls src="${url}" style="width: 100%;"></audio>
        `;

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
    const episodeId = sessionStorage.getItem("selected_episode_id") || localStorage.getItem("selected_episode_id");

    if (!episodeId) return alert("❌ No episode selected.");
  
    try {
      await consumeStoreCredits("voice_isolation");
    } catch (err) {
      resultContainer.innerText = `❌ Not enough credits: ${err.message}`;
      return;
    }
  
    resultContainer.innerText = "🎙️ Isolating voice using ElevenLabs...";
  
    const formData = new FormData();
    formData.append("audio", file);
    formData.append("episode_id", episodeId);
  
    try {
      const response = await fetch("/transcription/voice_isolate", {
        method: "POST",
        body: formData
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Voice isolation failed.");
  
      // Fetch the actual blob via proxy
      const blobUrl = data.isolated_blob_url;
      const audioRes = await fetch(`/transcription/get_isolated_audio?url=${encodeURIComponent(blobUrl)}`);
      const blob = await audioRes.blob();
      const url  = URL.createObjectURL(blob);
  
      // Set the isolated audio as active
      isolatedAudioBlob = blob;
      activeAudioBlob   = blob;
      activeAudioId     = "external";
  
      // Show the isolated audio player
      resultContainer.innerHTML = `
        <p>🎧 Isolated Audio</p>
        <audio controls src="${url}" style="width: 100%;"></audio>
      `;
  
      // Reveal the analysis UI
      document.getElementById("audioAnalysisSection").style.display = "block";
      document.getElementById("audioCuttingSection").style.display  = "block";
      document.getElementById("aiCuttingSection").style.display     = "block";
  
      // Hide the mix button until analysis completes
      const mixBtn = document.getElementById("mixBackgroundBtn");
      mixBtn.style.display = "none";
  
      // Wire up the download link for the isolated audio
      const dl = document.getElementById("downloadIsolatedVoice");
      dl.href           = url;
      dl.style.display  = "inline-block";
  
      // Optionally: automatically start analysis on the isolated audio
      // await analyzeEnhancedAudio();
    } catch (err) {
      console.error("Voice isolation failed:", err);
      resultContainer.innerText = `❌ Isolation failed: ${err.message}`;
    }
  }



async function analyzeEnhancedAudio() {
    const resultEl = document.getElementById("analysisResults");
    const timeline = document.getElementById("soundEffectTimeline");
    const mixBtn   = document.getElementById("mixBackgroundBtn");
  
    // Ensure we have something to analyze
    if (!activeAudioBlob) {
      return alert("No audio loaded. Enhance or Isolate first.");
    }
  
    // Spend credits
    try {
      await consumeStoreCredits("ai_audio_analysis");
    } catch (err) {
      resultEl.innerText = `❌ Not enough credits: ${err.message}`;
      return;
    }
  
    resultEl.innerText = "🔍 Analyzing...";
    const fd = new FormData();
    fd.append("audio", activeAudioBlob, "processed_audio.wav");
  
    try {
      const res  = await fetch("/audio_analysis", { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || res.statusText);
  
      // Show just the stats + dominant emotion
      resultEl.innerText = `
  📊 Sentiment:     ${data.sentiment ?? "–"}
  📊 Clarity Score: ${data.clarity_score ?? "–"}
  📊 Noise Level:   ${data.background_noise ?? "–"}
  📊 Dominant Emo:  ${data.dominant_emotion}
      `;
  
      // Render any sound-effect suggestions
      timeline.innerHTML = "";
      renderSoundSuggestions(data, timeline);
  
      // Save for mix step
      window.analysisData = {
        emotion:   data.dominant_emotion,
        audioBlob: activeAudioBlob
      };
  
      // Reveal the Mix button
      mixBtn.style.display = "inline-block";
    }
    catch (err) {
      resultEl.innerText = `❌ Analysis failed: ${err.message}`;
    }
  }

/* Hjälper att rendera suggestion-listan */
function renderSoundSuggestions(data, timeline) {
    timeline.innerHTML = "<h4>🎧 AI-Driven Sound Suggestions</h4>";
    window.selectedSoundFX = {};

    (data.sound_effect_suggestions || []).forEach((entry, i) => {
        const sfxList = entry.sfx_options || [];
        const container = document.createElement("div");
        container.className = "sound-suggestion";
        container.innerHTML = `
            <p><strong>📍 Text:</strong> ${entry.timestamp_text}</p>
            <p><strong>🎭 Emotion:</strong> ${entry.emotion}</p>
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
    mixBtn.innerText = "🔄 Generating…";
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
          <h4>🎶 Mixed Preview</h4>
          <audio controls src="${data.merged_audio}" style="width:100%;"></audio>
        `;
        // Update download link
        dl.href          = data.merged_audio;
        dl.style.display = "inline-block";
      }
    } catch (err) {
      preview.innerText = `❌ Error: ${err.message}`;
    } finally {
      // Restore button
      mixBtn.disabled  = false;
      mixBtn.innerText = "🔉 Mix Background & Preview";
    }
  }

async function cutAudio() {
    const startInput = document.getElementById("startTime");
    const endInput = document.getElementById("endTime");
    const cutResult = document.getElementById("cutResult");
    const dl = document.getElementById("downloadCut");

    const start = parseFloat(startInput.value);
    const end = parseFloat(endInput.value);

    const episodeId = sessionStorage.getItem("selected_episode_id") || localStorage.getItem("selected_episode_id");

    if (!episodeId || !activeAudioBlob) return alert("⚠️ No audio or episode selected.");
    if (isNaN(start) || isNaN(end) || start >= end) return alert("⚠️ Invalid timestamps.");

    try {
        await consumeStoreCredits("audio_cutting");
    } catch (err) {
        alert(`❌ Not enough credits: ${err.message}`);
        return;
    }

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
    } catch (err) {
        alert(`❌ Cut failed: ${err.message}`);
    }
}

async function aiCutAudio() {
    const episodeId = sessionStorage.getItem("selected_episode_id") || localStorage.getItem("selected_episode_id");

    if (!episodeId) {
        alert("❌ No episode selected.");
        return;
    }

    if (!activeAudioBlob && !activeAudioId) {
        alert("⚠️ No audio loaded.");
        return;
    }

    try {
        await consumeStoreCredits("ai_audio_cutting");
    } catch (err) {
        alert(`❌ Not enough credits: ${err.message}`);
        return;
    }

    const transcriptEl = document.getElementById("aiTranscript");
    const cutsContainer = document.getElementById("aiSuggestedCuts");
    transcriptEl.innerText = "🔄 Processing AI Cut... Please wait.";
    cutsContainer.innerHTML = "";

    try {
        let response, data;

        if (activeAudioId === "external") {
            // Använd blob och skicka till /ai_cut_from_blob
            const formData = new FormData();
            formData.append("audio", new File([activeAudioBlob], "ai_cut.wav", { type: "audio/wav" }));
            formData.append("episode_id", episodeId);

            response = await fetch("/ai_cut_from_blob", {
                method: "POST",
                body: formData
            });
        } else {
            // Använd file_id och skicka till /ai_cut_audio
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

        // 🧠 Visa transcript och suggested cuts
        transcriptEl.innerText = data.cleaned_transcript || "No transcript available.";

        const suggestedCuts = data.suggested_cuts || [];
        if (!suggestedCuts.length) {
            cutsContainer.innerText = "No suggested cuts found.";
            return;
        }

        cutsContainer.innerHTML = "";
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
            label.innerText = `💬 "${cut.sentence}" (${cut.start}s - ${cut.end}s) | Confidence: ${cut.certainty_score.toFixed(2)}`;

            const div = document.createElement("div");
            div.appendChild(checkbox);
            div.appendChild(label);
            cutsContainer.appendChild(div);
        });

        const applyBtn = document.createElement("button");
        applyBtn.className = "btn ai-edit-button";
        applyBtn.innerText = "✅ Apply AI Cuts";
        applyBtn.onclick = applySelectedCuts;

        cutsContainer.appendChild(applyBtn);

    } catch (err) {
        alert(`❌ AI Cut failed: ${err.message}`);
        transcriptEl.innerText = "❌ Failed to process audio.";
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

        // 🛡 Använd backend-proxy för att undvika CORS
        const proxyUrl = `/get_clipped_audio?url=${encodeURIComponent(blobUrl)}`;
        const audioRes = await fetch(proxyUrl);
        if (!audioRes.ok) throw new Error("Failed to fetch clipped audio.");
        const blob = await audioRes.blob();
        const url = URL.createObjectURL(blob);

        // 🎧 Visa spelare och ladda ner-knapp
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
        dl.innerText = "📥 Download Cleaned Audio";
        section.appendChild(dl);

        // Uppdatera aktiv blob
        activeAudioBlob = blob;
        activeAudioId = "external";
    } catch (err) {
        alert(`❌ Apply failed: ${err.message}`);
    }
}


async function cutAudioFromBlob() {
    const startInput = document.getElementById("startTime");
    const endInput = document.getElementById("endTime");
    const cutResult = document.getElementById("cutResult");
    const dl = document.getElementById("downloadCut");

    const start = parseFloat(startInput.value);
    const end = parseFloat(endInput.value);

    const episodeId = sessionStorage.getItem("selected_episode_id") || localStorage.getItem("selected_episode_id");

    if (!episodeId || !activeAudioBlob) return alert("⚠️ No audio or episode selected.");
    if (isNaN(start) || isNaN(end) || start >= end) return alert("⚠️ Invalid timestamps.");

    try {
        await consumeStoreCredits("audio_cutting");
    } catch (err) {
        alert(`❌ Not enough credits: ${err.message}`);
        return;
    }

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
    } catch (err) {
        alert(`❌ Cut failed: ${err.message}`);
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
        await consumeStoreCredits("video_enhancement");
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

    // ✅ Update the UI to reflect new credit balance
    await fetchStoreCredits(CURRENT_USER_ID);

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