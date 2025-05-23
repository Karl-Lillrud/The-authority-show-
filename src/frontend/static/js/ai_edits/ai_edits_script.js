// Global variables for audio processing
let enhancedAudioBlob = null
const enhancedAudioId = null
let isolatedAudioBlob = null
const isolatedAudioId = null
let activeAudioBlob = null
let activeAudioId = null
let rawAudioBlob = null
let rawTranscript = ""
let fullTranscript = ""

// Credit costs for different features
const CREDIT_COSTS = {
  ai_audio_analysis: 300,
  ai_audio_cutting: 800,
  ai_quotes: 200,
  ai_quote_images: 1000,
  ai_suggestions: 800,
  audio_clip: 1000,
  audio_cutting: 500,
  audio_enhancement: 500,
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
}

// Lista över AI-funktioner och deras info
const aiOptions = [
  {
    id: "transcribe",
    title: "Transcribe",
    description: "Convert audio to text using AI transcription",
    icon: "T",
    cost: CREDIT_COSTS.transcription,
    handler: transcribe,
  },
  {
    id: "enhanceAudio",
    title: "Enhance Audio",
    description: "Improve audio quality and reduce background noise",
    icon: "A",
    cost: CREDIT_COSTS.audio_enhancement,
    handler: enhanceAudio,
  },
  {
    id: "isolateVoice",
    title: "Isolate Voice",
    description: "Separate voice from background sounds",
    icon: "V",
    cost: CREDIT_COSTS.voice_isolation,
    handler: runVoiceIsolation,
  },
  {
    id: "cleanTranscript",
    title: "Clean Transcript",
    description: "Remove filler words and improve readability",
    icon: "C",
    cost: CREDIT_COSTS.clean_transcript,
    handler: generateCleanTranscript,
  },
  {
    id: "generateShowNotes",
    title: "Generate Show Notes",
    description: "Create detailed notes from your content",
    icon: "N",
    cost: CREDIT_COSTS.show_notes,
    handler: generateShowNotes,
  },
  {
    id: "aiSuggestions",
    title: "AI Suggestions",
    description: "Get content improvement recommendations",
    icon: "S",
    cost: CREDIT_COSTS.ai_suggestions,
    handler: generateAISuggestions,
  },
  {
    id: "generateQuotes",
    title: "Generate Quotes",
    description: "Extract quotable moments from your content",
    icon: "Q",
    cost: CREDIT_COSTS.ai_quotes,
    handler: generateQuotes,
  },
  {
    id: "osintLookup",
    title: "OSINT Lookup",
    description: "Research additional information from open sources",
    icon: "O",
    cost: CREDIT_COSTS.ai_osint,
    handler: runOsintSearch,
  },
]

// Initialize the application when the DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  // Check if we're on the options selection page
  const optionList = document.getElementById("option-list")
  if (optionList) {
    renderAIOptions(optionList)
  }

  // Workspace tab switching
  const workspaceButtons = document.querySelectorAll(".workspace-tab-btn")
  workspaceButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const tabName = this.getAttribute("data-workspace")
      showTab(tabName)
    })
  })

  // Show transcription tab by default
  if (document.getElementById("content")) {
    showTab("transcription")
  }

  // Prevent double-click/spam-clicking to avoid duplicate credit usage
  document.body.addEventListener(
    "click",
    (event) => {
      const button = event.target.closest("button.ai-edit-button")
      if (!button || button.disabled) return

      button.disabled = true
      button.classList.add("disabled")

      setTimeout(() => {
        button.disabled = false
        button.classList.remove("disabled")
      }, 1000)
    },
    true,
  )

  // Audio Cutting: Setup event listener for source selection
  const cuttingSource = document.getElementById("audioSourceSelectCutting")
  if (cuttingSource) {
    cuttingSource.addEventListener("change", function () {
      const source = this.value
      let blob = null

      if (source === "original") blob = rawAudioBlob
      if (source === "enhanced") blob = enhancedAudioBlob
      if (source === "isolated") blob = isolatedAudioBlob

      if (blob) {
        initWaveformCutting(blob)
      } else {
        document.getElementById("waveformCut").innerHTML = "<p>No audio available for the selected source.</p>"
      }
    })
  }

  // Run button for AI options
  const runButton = document.getElementById("run-button")
  if (runButton) {
    runButton.addEventListener("click", () => {
      const selected = []
      document.querySelectorAll(".option-checkbox:checked").forEach((cb) => {
        selected.push(cb.dataset.function)
      })

      if (selected.length === 0) {
        showStatus("Please select at least one editing option", "error")
        return
      }

      runSelectedFunctions(selected)
    })
  }

  // Add file info display
  const mainFileInput = document.getElementById("audio-file")
  if (mainFileInput) {
    mainFileInput.addEventListener("change", function () {
      const fileInfo = document.getElementById("file-info")
      if (fileInfo) {
        if (this.files && this.files[0]) {
          const file = this.files[0]
          const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2)
          fileInfo.textContent = `Selected file: ${file.name} (${fileSizeMB} MB)`

          // Store the file in rawAudioBlob for use in functions
          rawAudioBlob = file
        } else {
          fileInfo.textContent = ""
        }
      }
    })
  }
})

// Render the AI options with checkboxes
function renderAIOptions(optionList) {
  aiOptions.forEach((option) => {
    const item = document.createElement("div")
    item.className = "option-item"
    item.innerHTML = `
      <div class="option-icon">${option.icon}</div>
      <div class="option-content">
        <div class="option-title">${option.title}</div>
        <div class="option-description">${option.description} <span style="color: gray; font-size: 0.9em;">(${option.cost} credits)</span></div>
      </div>
      <input type="checkbox" class="option-checkbox" id="${option.id}" data-function="${option.id}">
    `
    optionList.appendChild(item)

    // Klick på hela boxen togglar checkboxen
    item.addEventListener("click", (e) => {
      if (e.target.type !== "checkbox") {
        const checkbox = item.querySelector(".option-checkbox")
        checkbox.checked = !checkbox.checked
      }
    })
  })
}

// Run the selected AI functions
async function runSelectedFunctions(functionNames) {
  showStatus(`Running: ${functionNames.join(", ")}`, "info")

  // Create a container for results if it doesn't exist
  let resultsContainer = document.getElementById("ai-results-container")
  if (!resultsContainer) {
    resultsContainer = document.createElement("div")
    resultsContainer.id = "ai-results-container"
    resultsContainer.className = "results-container"
    const container = document.querySelector(".container")
    if (container) {
      container.appendChild(resultsContainer)
    } else {
      console.error("Container element not found")
      return
    }
  }

  // Create result sections for each selected function if they don't exist
  functionNames.forEach((funcName) => {
    const resultSectionId = `${funcName}-result`
    if (!document.getElementById(resultSectionId)) {
      const resultSection = document.createElement("div")
      resultSection.id = resultSectionId
      resultSection.className = "output-section"
      resultSection.style.display = "none"

      const heading = document.createElement("h3")
      const option = aiOptions.find((opt) => opt.id === funcName)
      heading.textContent = option ? option.title : funcName

      const content = document.createElement("div")
      content.className = "result-content"

      resultSection.appendChild(heading)
      resultSection.appendChild(content)
      resultsContainer.appendChild(resultSection)
    }
  })

  // Hide all output sections first
  document.querySelectorAll(".output-section").forEach((section) => {
    section.style.display = "none"
    section.classList.remove("visible")
  })

  // Disable run button during processing
  const runButton = document.getElementById("run-button")
  if (runButton) {
    runButton.disabled = true
    runButton.textContent = "Processing..."
  }

  try {
    // Process functions sequentially
    for (const funcName of functionNames) {
      // Find the function in aiOptions
      const option = aiOptions.find((opt) => opt.id === funcName)
      if (!option || !option.handler) {
        showStatus(`Function ${funcName} not found or has no handler`, "error")
        continue
      }

      // Execute the function
      showStatus(`Running: ${option.title}...`, "info")

      try {
        // Execute the handler function
        await option.handler()

        // Show the result section with animation
        const resultSection = document.getElementById(`${funcName}-result`)
        if (resultSection) {
          resultSection.style.display = "block"
          setTimeout(() => resultSection.classList.add("visible"), 10)
        }

        showStatus(`Completed: ${option.title}`, "info")
      } catch (error) {
        // If there's an error, still show the section but with error message
        const resultSection = document.getElementById(`${funcName}-result`)
        if (resultSection) {
          resultSection.style.display = "block"
          setTimeout(() => resultSection.classList.add("visible"), 10)

          const resultContent = resultSection.querySelector(".result-content") || resultSection
          if (resultContent) {
            resultContent.innerHTML = `<p class="error-message">Error: ${error.message}</p>`
          }
        }

        showStatus(`Error in ${option.title}: ${error.message}`, "error")
      }
    }
  } finally {
    // Re-enable run button
    if (runButton) {
      runButton.disabled = false
      runButton.textContent = "Run Selected Edits"
    }
    showStatus("All selected functions completed", "info")
  }
}

// Execute a function and capture its output
async function executeFunction(func, resultContainerId) {
  const resultContainer = document.getElementById(resultContainerId)

  // Create a proxy for the original function to capture its output
  const originalConsoleLog = console.log
  const logs = []

  console.log = (...args) => {
    logs.push(args.join(" "))
    originalConsoleLog(...args)
  }

  try {
    // Execute the function
    await func()

    // Update the result container with any console output
    if (logs.length > 0 && resultContainer) {
      resultContainer.innerHTML += `
        <pre class="console-output">${logs.join("\n")}</pre>
      `
    }

    // Show the result section with animation
    if (resultContainer) {
      resultContainer.style.display = "block"
      setTimeout(() => resultContainer.classList.add("visible"), 10)
    }
  } finally {
    // Restore original console.log
    console.log = originalConsoleLog
  }
}

// Show status message
function showStatus(msg, type = "info") {
  const el = document.getElementById("status-message")
  if (el) {
    el.textContent = msg
    el.style.display = "block"
    el.style.backgroundColor = type === "error" ? "#fff5f5" : "#f0f7ff"
    el.style.color = type === "error" ? "#c53030" : "#2c5282"
    setTimeout(() => {
      el.style.display = "none"
    }, 5000)
  }
}

// Show the selected tab
function showTab(tabName) {
  // Get all workspace tab buttons
  const workspaceButtons = document.querySelectorAll(".workspace-tab-btn")

  // Remove active class from all buttons
  workspaceButtons.forEach((btn) => btn.classList.remove("active"))

  // Add active class to clicked button
  const clickedButton = document.querySelector(`.workspace-tab-btn[data-workspace="${tabName}"]`)
  if (clickedButton) {
    clickedButton.classList.add("active")
  }

  const content = document.getElementById("content")
  if (!content) return

  content.innerHTML = ""

  if (tabName === "transcription") {
    content.innerHTML = `
      <div class="content-wrapper">
        <h1>AI-Powered Transcription</h1>

        <input type="file" id="fileUploader" accept="audio/*,video/*">
        <div class="button-with-help">
            <button class="btn ai-edit-button" onclick="transcribe()">
              Transcribe <span style="color: rgba(255,255,255,0.7); font-size: 0.9em;">(${CREDIT_COSTS.transcription} credits)</span>
            </button>
            <span class="help-icon" data-tooltip="Converts the uploaded audio or video file into text using AI">?</span>
        </div>
        <div class="result-field">
            <pre id="transcriptionResult"></pre>
        </div>
      </div>

      <div class="content-wrapper" id="enhancementTools" style="display: none;">
        <h2>Enhancement Tools</h2>

        <div class="result-group">
          <div class="button-with-help">
            <button class="btn ai-edit-button" onclick="generateCleanTranscript()">
              Clean Transcript <span style="color: rgba(255,255,255,0.7); font-size: 0.9em;">(${CREDIT_COSTS.clean_transcript} credits)</span>
            </button>
            <span class="help-icon" data-tooltip="Removes filler words, repeated phrases, and fixes typos in the raw transcription">?</span>
          </div>
          <div class="result-field">
            <pre id="cleanTranscriptResult"></pre>
          </div>
        </div>

        <div class="result-group">
          <label for="languageSelect">Language:</label>
          <select id="languageSelect" class="input-field">
            <option value="English">English</option>
            <option value="Spanish">Spanish</option>
            <option value="French">French</option>
            <option value="German">German</option>
            <option value="Swedish">Swedish</option>
          </select>

          <div class="button-with-help">
            <button class="btn ai-edit-button" onclick="translateTranscript()">
              Translate <span style="color: rgba(255,255,255,0.7); font-size: 0.9em;">(${CREDIT_COSTS.translation} credits)</span>
            </button>
            <span class="help-icon" data-tooltip="Translates the transcript into the selected language">?</span>
          </div>

          <div class="result-field">
            <pre id="translateResult"></pre>
          </div>
        </div>

        <div class="result-group">
          <div class="button-with-help">
            <button class="btn ai-edit-button" onclick="generateAudioClip()">
              Generate Translated Podcast <span style="color: rgba(255,255,255,0.7); font-size: 0.9em;">(${CREDIT_COSTS.audio_clip} credits)</span>
            </button>
            <span class="help-icon" data-tooltip="Produces an audio file of the translated text, ready to play as a podcast">?</span>
          </div>
          <div class="result-field" id="audioClipResult"></div>
        </div>

        <div class="result-group">
          <div class="button-with-help">
            <button class="btn ai-edit-button" onclick="generateAISuggestions()">
              AI Suggestions <span style="color: rgba(255,255,255,0.7); font-size: 0.9em;">(${CREDIT_COSTS.ai_suggestions} credits)</span>
            </button>
            <span class="help-icon" data-tooltip="Provides AI-generated tips on how to improve your transcript">?</span>
          </div>
          <div class="result-field">
            <pre id="aiSuggestionsResult"></pre>
          </div>
        </div>

        <div class="result-group">
          <div class="button-with-help">
            <button class="btn ai-edit-button" onclick="generateShowNotes()">
              Show Notes <span style="color: rgba(255,255,255,0.7); font-size: 0.9em;">(${CREDIT_COSTS.show_notes} credits)</span>
            </button>
            <span class="help-icon" data-tooltip="Creates a concise bullet-point summary of the main topics covered">?</span>
          </div>
          <div class="result-field">
            <pre id="showNotesResult"></pre>
          </div>
        </div>

        <div class="result-group">
          <div class="button-with-help">
            <button class="btn ai-edit-button" onclick="generateQuotes()">
              Generate Quotes <span style="color: rgba(255,255,255,0.7); font-size: 0.9em;">(${CREDIT_COSTS.ai_quotes} credits)</span>
            </button>
            <span class="help-icon" data-tooltip="Extracts memorable quotes from the transcript">?</span>
          </div>
          <div class="result-field">
            <pre id="quotesResult"></pre>
          </div>
        </div>

        <div class="result-group">
          <label for="quoteImageMethodSelect"><strong>Quote Image Style:</strong></label>
          <select id="quoteImageMethodSelect" class="input-field" style="margin-bottom: 0.5rem;">
            <option value="local">Local Template</option>
            <option value="dalle">DALL·E AI Image</option>
          </select>
          <button class="btn ai-edit-button" onclick="generateQuoteImages()">
            Generate Quote Images <span style="color: rgba(255,255,255,0.7); font-size: 0.9em;">(${CREDIT_COSTS.ai_quote_images} credits)</span>
          </button>
          <div class="result-field">
            <div id="quoteImagesResult"></div>
          </div>
        </div>

        <div class="result-group">
          <input type="text" id="guestNameInput" placeholder="Enter guest name..." class="input-field">
          <div class="button-with-help">
            <button class="btn ai-edit-button" onclick="runOsintSearch()">
              OSINT Search <span style="color: rgba(255,255,255,0.7); font-size: 0.9em;">(${CREDIT_COSTS.ai_osint} credits)</span>
            </button>
            <span class="help-icon" data-tooltip="Performs an open-source intelligence search on the entered guest name">?</span>
          </div>
          <div class="result-field">
            <pre id="osintResult"></pre>
          </div>
        </div>

        <div class="button-with-help">
          <button class="btn ai-edit-button" onclick="generatePodcastIntroOutro()">
            Generate Intro/Outro <span style="color: rgba(255,255,255,0.7); font-size: 0.9em;">(${CREDIT_COSTS.ai_intro_outro} credits)</span>
          </button>
          <span class="help-icon" data-tooltip="Writes a suggested introduction and closing script for your episode">?</span>
        </div>
        <div class="result-field">
          <pre id="introOutroScriptResult"></pre>
        </div>
        <div class="button-with-help" style="margin-top: 1rem;">
          <button class="btn ai-edit-button" onclick="convertIntroOutroToSpeech()">
            Convert to Speech <span style="color: rgba(255,255,255,0.7); font-size: 0.9em;">(${CREDIT_COSTS.ai_intro_outro_audio} credits)</span>
          </button>
          <span class="help-icon" data-tooltip="Turns that script into a spoken audio file using AI voice">?</span>
        </div>
        <div class="result-field" id="introOutroAudioResult"></div>
      </div>
    `
  } else if (tabName === "audio") {
    content.innerHTML = `
      <div class="content-wrapper">
        <h1>AI Audio Enhancement</h1>
        <input type="file" id="audioUploader" accept="audio/*" onchange="previewOriginalAudio()">
        <div id="originalAudioContainer" style="display: none; margin-bottom: 1rem;">
          <p><strong>Original Audio</strong></p>
        </div>

        <div style="margin-top: 1rem; padding: 1rem; border: 1px solid #ddd; border-radius: 12px;">
          <h3>Choose Audio Processing Method</h3>
          <p style="margin-bottom: 1rem;">Select one of the following enhancements:</p>

          <div id="voiceIsolationSection" style="margin-bottom: 1.5rem;">
            <h4><strong>Voice Isolation (Powered by ElevenLabs)</strong></h4>
            <div class="button-with-help">
              <button class="btn ai-edit-button" onclick="runVoiceIsolation()">
                Isolate Voice <span style="color: rgba(255,255,255,0.7); font-size: 0.9em;">(${CREDIT_COSTS.voice_isolation} credits)</span>
              </button>
              <span class="help-icon" data-tooltip="Separates the speaker's voice from background noise">?</span>
            </div>
            <div class="result-field">
              <div id="isolatedVoiceResult"></div>
            </div>
            <a id="downloadIsolatedVoice"
              class="btn ai-edit-button"
              style="display: none;"
              download="isolated_voice.wav">
              Download Isolated Voice
            </a>
          </div>

          <div id="audioEnhancementSection">
            <h4><strong>Audio Enhancement (Noise Reduction & Normalization)</strong></h4>
            <div class="button-with-help">
              <button class="btn ai-edit-button" onclick="enhanceAudio()">
                Enhance Audio <span style="color: rgba(255,255,255,0.7); font-size: 0.9em;">(${CREDIT_COSTS.audio_enhancement} credits)</span>
              </button>
              <span class="help-icon" data-tooltip="Reduces noise and normalizes volume levels automatically">?</span>
            </div>
            <div class="result-field">
              <div id="audioControls"></div>
            </div>
          </div>
        </div>
      </div>

      <div class="content-wrapper" id="audioAnalysisSection" style="display: none;">
        <h2>AI Analysis</h2>

        <label for="audioSourceSelectAnalysis"><strong>Audio Source:</strong></label>
        <select id="audioSourceSelectAnalysis" class="input-field" style="margin-bottom: 1rem;">
          <option value="enhanced">Enhanced</option>
          <option value="isolated">Isolated</option>
          <option value="original">Original</option>
        </select>

        <div class="button-with-help">
          <button class="btn ai-edit-button" onclick="analyzeEnhancedAudio()">
            Analyze <span style="color: rgba(255,255,255,0.7); font-size: 0.9em;">(${CREDIT_COSTS.ai_audio_analysis} credits)</span>
          </button>
          <span class="help-icon" data-tooltip="Lets the AI analyze the selected audio source and provide content insights">?</span>
        </div>
        <div class="result-field">
          <pre id="analysisResults"></pre>
        </div>

        <button id="mixBackgroundBtn"
          class="btn ai-edit-button"
          style="display: none; margin-top: 1rem;"
          onclick="displayBackgroundAndMix()">
          Mix Background & Preview
        </button>
        <div class="result-field">
          <div id="backgroundPreview"></div>
        </div>
        <div class="result-field">
          <div id="soundEffectTimeline"></div>
        </div>

        <div class="button-with-help" style="margin-top: 1rem;">
          <a id="downloadEnhanced"
            class="btn ai-edit-button"
            download="processed_audio.wav"
            style="display: none;">
            Download Processed Audio
          </a>
        </div>
      </div>

      <div class="content-wrapper" id="audioCuttingSection" style="display: none;">
        <h2>Audio Cutting</h2>

        <label for="audioSourceSelectCutting"><strong>Audio Source:</strong></label>
        <select id="audioSourceSelectCutting" class="input-field" style="margin-bottom: 1rem;">
          <option value="enhanced">Enhanced</option>
          <option value="isolated">Isolated</option>
          <option value="original">Original</option>
        </select>
        <button class="btn ai-edit-button" id="loadCuttingWaveformBtn" style="margin-bottom: 1rem;">
          Load Audio Waveform
        </button>
        
        <div id="waveformCut" style="margin: 1rem 0; height: 128px;"></div>
        
        <button id="cut-play-pause" class="btn ai-edit-button" style="display:none; margin-bottom:1rem;">
          Play
        </button>
        <label>
          Start (s):
          <input id="cut-start" type="number" step="0.01" class="input-field" style="width:5em;">
        </label>
        <label style="margin-left:1em;">
          End (s):
          <input id="cut-end" type="number" step="0.01" class="input-field" style="width:5em;">
        </label>

        <div class="button-with-help">
          <button class="btn ai-edit-button" onclick="cutAudio()">
            Cut <span style="color: rgba(255,255,255,0.7); font-size: 0.9em;">(${CREDIT_COSTS.audio_cutting} credits)</span>
          </button>
          <span class="help-icon" data-tooltip="Trim the audio between the specified start and end">?</span>
        </div>
        <div class="result-field">
          <div id="cutResult"></div>
        </div>

        <div class="button-with-help" style="margin-top: 1rem;">
          <a id="downloadCut"
            class="btn ai-edit-button"
            download="cut_audio.wav"
            style="display: none;">
            Download Cut
          </a>
        </div>
      </div>

      <div class="content-wrapper" id="aiCuttingSection" style="display: none;">
        <h2>AI Cutting + Transcript</h2>

        <label for="audioSourceSelectAICut"><strong>Audio Source:</strong></label>
        <select id="audioSourceSelectAICut" class="input-field" style="margin-bottom: 1rem;">
          <option value="enhanced">Enhanced</option>
          <option value="isolated">Isolated</option>
          <option value="original">Original</option>
        </select>
        
        <div class="button-with-help">
          <button class="btn ai-edit-button" onclick="aiCutAudio()">
            Run AI Cut <span style="color: rgba(255,255,255,0.7); font-size: 0.9em;">(${CREDIT_COSTS.ai_audio_cutting} credits)</span>
          </button>
          <span class="help-icon" data-tooltip="Automatically removes silent or filler sections and provides a transcript">?</span>
        </div>
        <div class="result-field">
          <h4>Transcript</h4>
          <pre id="aiTranscript"></pre>
        </div>
        <div class="result-field">
          <h4>Suggested Cuts</h4>
          <pre id="aiSuggestedCuts"></pre>
        </div>
      </div>
    `

    // Setup waveform loading button
    setTimeout(() => {
      const loadCutBtn = document.getElementById("loadCuttingWaveformBtn")
      if (loadCutBtn) {
        loadCutBtn.onclick = () => {
          const source = document.getElementById("audioSourceSelectCutting").value
          let blob = null

          if (source === "original") blob = rawAudioBlob
          else if (source === "enhanced") blob = enhancedAudioBlob
          else if (source === "isolated") blob = isolatedAudioBlob

          if (blob) {
            initWaveformCutting(blob)
          } else {
            document.getElementById("waveformCut").innerHTML = "<p>No audio available for the selected source.</p>"
          }
        }
      }
    }, 0)
  } else if (tabName === "video") {
    content.innerHTML = `
      <div class="content-wrapper">
        <h1>AI Video Enhancement</h1>
        <input type="file" id="videoUploader" accept="video/*" onchange="previewOriginalVideo()">
        <div id="originalVideoContainer" style="display: none; margin-bottom: 1rem;">
          <p><strong>Original Video</strong></p>
          <video id="originalVideoPlayer" controls style="width: 100%"></video>
        </div>
        <div class="button-group" style="margin-bottom: 1rem;">
          <div class="button-with-help">
            <button class="btn ai-edit-button" id="enhanceVideoBtn" onclick="enhanceVideo()">
              Enhance Video <span style="color: rgba(255,255,255,0.7); font-size: 0.9em;">(${CREDIT_COSTS.video_enhancement} credits)</span>
            </button>
            <span class="help-icon" data-tooltip="Applies AI enhancements to improve the video's audio quality">?</span>
          </div>
          <button class="btn ai-edit-button" id="resetVideoBtn" onclick="resetVideo()" style="display: none;">
            Reset
          </button>
        </div>
        <div id="videoResult"></div>
        <a id="downloadVideo" class="btn ai-edit-button" download="enhanced_video.mp4" style="display: none;">
          Download Enhanced Video
        </a>
      </div>
    `
  }
}

// Function to initialize waveform for audio cutting
let waveformCut = null
let selectedRegion = null

function initWaveformCutting(blob) {
  // Clean up any existing instance
  if (waveformCut) {
    waveformCut.destroy()
    document.getElementById("waveformCut").innerHTML = ""
  }

  // Check if WaveSurfer and RegionsPlugin are available
  if (!window.WaveSurfer || !window.WaveSurferRegions) {
    document.getElementById("waveformCut").innerHTML =
      "<p>WaveSurfer or Regions plugin not loaded. Please check your dependencies.</p>"
    return
  }

  // Create a new WaveSurfer instance with the Regions plugin
  waveformCut = WaveSurfer.create({
    container: "#waveformCut",
    waveColor: "#ccc",
    progressColor: "#f69229",
    height: 128,
    barWidth: 2,
    responsive: true,
    backend: "WebAudio",
    plugins: [
      WaveSurferRegions.create({
        dragSelection: true,
      }),
    ],
  })

  // Load the audio from the blob
  waveformCut.load(URL.createObjectURL(blob))

  waveformCut.on("ready", () => {
    // Add a default region
    const duration = waveformCut.getDuration()
    selectedRegion = waveformCut.addRegion({
      start: 0,
      end: Math.min(5, duration),
      color: "rgba(255, 87, 34, 0.3)",
      drag: true,
      resize: true,
    })

    // Show & wire the Play/Pause button
    const btn = document.getElementById("cut-play-pause")
    btn.style.display = "inline-block"
    btn.onclick = () => {
      waveformCut.isPlaying() ? waveformCut.pause() : waveformCut.play()
    }
    waveformCut.on("play", () => {
      btn.textContent = "Pause"
    })
    waveformCut.on("pause", () => {
      btn.textContent = "Play"
    })

    // Sync numeric inputs with region
    const startInput = document.getElementById("cut-start")
    const endInput = document.getElementById("cut-end")
    startInput.value = selectedRegion.start.toFixed(2)
    endInput.value = selectedRegion.end.toFixed(2)

    startInput.oninput = () => {
      const v = Number.parseFloat(startInput.value)
      if (!isNaN(v) && v < selectedRegion.end) {
        selectedRegion.update({ start: v })
      }
    }
    endInput.oninput = () => {
      const v = Number.parseFloat(endInput.value)
      if (!isNaN(v) && v > selectedRegion.start) {
        selectedRegion.update({ end: v })
      }
    }
  })

  // Keep inputs in sync whenever the user drags/resizes the region
  waveformCut.on("region-updated", (region) => {
    selectedRegion = region
    document.getElementById("cut-start").value = region.start.toFixed(2)
    document.getElementById("cut-end").value = region.end.toFixed(2)
  })
}

// Transcription function
async function transcribe() {
  // Try to get the file input from either the tab content or the main page
  let fileInput = document.getElementById("fileUploader")
  if (!fileInput) {
    fileInput = document.getElementById("audio-file")
    if (!fileInput) {
      alert("File uploader element not found. Please upload a file using the file input above.")
      return
    }
  }

  const file = fileInput.files && fileInput.files[0]
  if (!file) {
    alert("Please upload a file before transcribing.")
    return
  }

  // Get or create the transcription result element
  let transcriptionResult = document.getElementById("transcriptionResult")
  if (!transcriptionResult) {
    // Try to find the parent container
    let transcribeResult = document.getElementById("transcribe-result")
    if (!transcribeResult) {
      // Create the container if it doesn't exist
      transcribeResult = document.createElement("div")
      transcribeResult.id = "transcribe-result"
      transcribeResult.className = "output-section"
      transcribeResult.style.display = "block"

      const heading = document.createElement("h2")
      heading.textContent = "Transcript"

      transcriptionResult = document.createElement("pre")
      transcriptionResult.id = "transcriptionResult"

      transcribeResult.appendChild(heading)
      transcribeResult.appendChild(transcriptionResult)

      // Add to the container
      const container = document.querySelector(".container")
      if (container) {
        container.appendChild(transcribeResult)
      } else {
        alert("Container not found. Please refresh the page.")
        return
      }
    } else {
      // If the container exists but not the result element
      transcriptionResult = document.createElement("pre")
      transcriptionResult.id = "transcriptionResult"
      transcribeResult.appendChild(transcriptionResult)
    }
  }

  // Make sure the container is visible
  const transcribeResultContainer = document.getElementById("transcribe-result")
  if (transcribeResultContainer) {
    transcribeResultContainer.style.display = "block"
    transcribeResultContainer.classList.add("visible")
  }

  // Show loading indicator
  transcriptionResult.innerHTML = '<div class="spinner"></div><p>Transcribing audio... Please wait.</p>'
  showStatus("Transcribing audio... This may take a moment.", "info")

  // Get episode ID (or use a default if not available)
  const episodeId = getSelectedEpisodeId() || "default_episode"

  const formData = new FormData()
  formData.append("file", file)
  formData.append("episode_id", episodeId)

  try {
    console.log("Starting transcription for file:", file.name)
    const response = await fetch("/transcription/transcribe", {
      method: "POST",
      body: formData,
    })

    console.log("Transcription API response status:", response.status)
    const result = await response.json()
    console.log("Transcription result received:", result)

    if (response.status === 403) {
      transcriptionResult.innerHTML = `
        <p style="color: red;">${result.error || "You don't have enough credits."}</p>
        ${result.redirect ? `<a href="${result.redirect}" class="btn ai-edit-button">Go to Store</a>` : ""}
      `
      showStatus("Transcription failed: Not enough credits", "error")
      return
    }

    if (!response.ok) {
      throw new Error(result.error || "Transcription failed")
    }

    // Store the transcripts in global variables
    rawTranscript = result.raw_transcription || ""
    fullTranscript = result.full_transcript || ""

    // Display the transcript
    transcriptionResult.innerHTML = rawTranscript || "No transcript was returned from the server."

    // Show enhancement tools if they exist
    const enhancementTools = document.getElementById("enhancementTools")
    if (enhancementTools) {
      enhancementTools.style.display = "block"
    }

    if (result.credit_warning) {
      alert("Transcription completed, but your credits are too low. Please visit the store.")
    }

    // Only consume credits after successful transcription
    await consumeStoreCredits("transcription")

    showStatus("Transcription completed successfully!", "info")
  } catch (error) {
    console.error("Transcription error:", error)
    transcriptionResult.innerHTML = `<p style="color: red;">Transcription failed: ${error.message}</p>`
    showStatus(`Transcription failed: ${error.message}`, "error")
  }
}

// Translation function
async function translateTranscript() {
  const resultContainer = document.getElementById("translateResult")
  const lang = document.getElementById("languageSelect").value
  if (!rawTranscript) return alert("You need to transcribe first.")

  showSpinner("translateResult")
  try {
    const res = await fetch("/transcription/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        raw_transcription: rawTranscript,
        language: lang,
      }),
    })
    hideSpinner("translateResult")

    const data = await res.json()
    if (!res.ok) throw new Error(data.error || res.statusText)

    resultContainer.innerText = data.translated_transcription

    // Only consume credits after successful translation
    await consumeStoreCredits("translation")
  } catch (err) {
    hideSpinner("translateResult")
    resultContainer.innerText = `Error: ${err.message}`
  }
}

// Clean transcript function
async function generateCleanTranscript() {
  // First, ensure we have a container for the result
  let container = document.getElementById("cleanTranscriptResult")
  if (!container) {
    // Try to find the parent container
    let resultSection = document.getElementById("cleanTranscript-result")
    if (!resultSection) {
      // Create the container if it doesn't exist
      resultSection = document.createElement("div")
      resultSection.id = "cleanTranscript-result"
      resultSection.className = "output-section"
      resultSection.style.display = "block"

      const heading = document.createElement("h2")
      heading.textContent = "Cleaned Transcript"

      container = document.createElement("pre")
      container.id = "cleanTranscriptResult"

      resultSection.appendChild(heading)
      resultSection.appendChild(container)

      // Add to the container
      const mainContainer = document.querySelector(".container")
      if (mainContainer) {
        mainContainer.appendChild(resultSection)
      } else {
        alert("Container not found. Please refresh the page.")
        return
      }
    } else {
      // If the container exists but not the result element
      container = document.createElement("pre")
      container.id = "cleanTranscriptResult"
      resultSection.appendChild(container)
    }
  }

  // Make sure the container is visible
  const resultSection = document.getElementById("cleanTranscript-result")
  if (resultSection) {
    resultSection.style.display = "block"
    resultSection.classList.add("visible")
  }

  // Show loading indicator
  container.innerHTML = '<div class="spinner"></div><p>Cleaning transcript... Please wait.</p>'
  showStatus("Cleaning transcript...", "info")

  try {
    if (!fullTranscript) {
      container.innerHTML = '<p style="color: red;">No transcript available. Please transcribe first.</p>'
      return
    }

    const res = await fetch("/transcription/clean", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcript: fullTranscript }),
    })

    if (res.status === 403) {
      const errorData = await res.json()
      container.innerHTML = `
        <p style="color: red;">${errorData.error || "You don't have enough credits."}</p>
        ${errorData.redirect ? `<a href="${errorData.redirect}" class="btn ai-edit-button">Go to Store</a>` : ""}
      `
      return
    }

    const data = await res.json()
    container.innerHTML = data.clean_transcript || "No clean result."

    // Only consume credits after successful clean transcript generation
    await consumeStoreCredits("clean_transcript")
    showStatus("Transcript cleaned successfully!", "info")
  } catch (err) {
    container.innerHTML = `<p style="color: red;">Failed to clean transcript: ${err.message}</p>`
    showStatus(`Failed to clean transcript: ${err.message}`, "error")
  }
}

// AI Suggestions function
async function generateAISuggestions() {
  // First, ensure we have a container for the result
  let container = document.getElementById("ai-suggestions-output")
  if (!container) {
    // Try to find the parent container
    let resultSection = document.getElementById("aiSuggestions-result")
    if (!resultSection) {
      // Create the container if it doesn't exist
      resultSection = document.createElement("div")
      resultSection.id = "aiSuggestions-result"
      resultSection.className = "output-section"
      resultSection.style.display = "block"

      const heading = document.createElement("h2")
      heading.textContent = "AI Suggestions"

      container = document.createElement("pre")
      container.id = "ai-suggestions-output"

      resultSection.appendChild(heading)
      resultSection.appendChild(container)

      // Add to the container
      const mainContainer = document.querySelector(".container")
      if (mainContainer) {
        mainContainer.appendChild(resultSection)
      } else {
        alert("Container not found. Please refresh the page.")
        return
      }
    } else {
      // If the container exists but not the result element
      container = document.createElement("pre")
      container.id = "ai-suggestions-output"
      resultSection.appendChild(container)
    }
  }

  // Make sure the container is visible
  const resultSection = document.getElementById("aiSuggestions-result")
  if (resultSection) {
    resultSection.style.display = "block"
    resultSection.classList.add("visible")
  }

  // Show loading indicator
  container.innerHTML = '<div class="spinner"></div><p>Generating AI suggestions... Please wait.</p>'
  showStatus("Generating AI suggestions...", "info")

  try {
    if (!rawTranscript) {
      container.innerHTML = '<p style="color: red;">No transcript available. Please transcribe first.</p>'
      return
    }

    const res = await fetch("/transcription/ai_suggestions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcript: rawTranscript }),
    })

    if (res.status === 403) {
      const data = await res.json()
      container.innerHTML = `
        <p style="color: red;">${data.error || "You don't have enough credits."}</p>
        ${data.redirect ? `<a href="${data.redirect}" class="btn ai-edit-button">Go to Store</a>` : ""}
      `
      return
    }

    const data = await res.json()
    const primary = data.primary_suggestions || ""
    const additional = (data.additional_suggestions || []).join("\n")
    container.innerHTML = [primary, additional].filter(Boolean).join("\n\n") || "No suggestions."

    // Only consume credits after successful AI suggestions generation
    await consumeStoreCredits("ai_suggestions")
    showStatus("AI suggestions generated successfully!", "info")
  } catch (err) {
    container.innerHTML = `<p style="color: red;">Failed to generate suggestions: ${err.message}</p>`
    showStatus(`Failed to generate suggestions: ${err.message}`, "error")
  }
}

// Show notes function
async function generateShowNotes() {
  // First, ensure we have a container for the result
  let container = document.getElementById("show-notes-output")
  if (!container) {
    // Try to find the parent container
    let resultSection = document.getElementById("generateShowNotes-result")
    if (!resultSection) {
      // Create the container if it doesn't exist
      resultSection = document.createElement("div")
      resultSection.id = "generateShowNotes-result"
      resultSection.className = "output-section"
      resultSection.style.display = "block"

      const heading = document.createElement("h2")
      heading.textContent = "Show Notes"

      container = document.createElement("pre")
      container.id = "show-notes-output"

      resultSection.appendChild(heading)
      resultSection.appendChild(container)

      // Add to the container
      const mainContainer = document.querySelector(".container")
      if (mainContainer) {
        mainContainer.appendChild(resultSection)
      } else {
        alert("Container not found. Please refresh the page.")
        return
      }
    } else {
      // If the container exists but not the result element
      container = document.createElement("pre")
      container.id = "show-notes-output"
      resultSection.appendChild(container)
    }
  }

  // Make sure the container is visible
  const resultSection = document.getElementById("generateShowNotes-result")
  if (resultSection) {
    resultSection.style.display = "block"
    resultSection.classList.add("visible")
  }

  // Show loading indicator
  container.innerHTML = '<div class="spinner"></div><p>Generating show notes... Please wait.</p>'
  showStatus("Generating show notes...", "info")

  try {
    if (!rawTranscript) {
      container.innerHTML = '<p style="color: red;">No transcript available. Please transcribe first.</p>'
      return
    }

    const res = await fetch("/transcription/show_notes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcript: rawTranscript }),
    })

    if (res.status === 403) {
      const data = await res.json()
      container.innerHTML = `
        <p style="color: red;">${data.error || "You don't have enough credits."}</p>
        ${data.redirect ? `<a href="${data.redirect}" class="btn ai-edit-button">Go to Store</a>` : ""}
      `
      return
    }

    const data = await res.json()
    container.innerHTML = data.show_notes || "No notes."

    // Only consume credits after successful show notes generation
    await consumeStoreCredits("show_notes")
    showStatus("Show notes generated successfully!", "info")
  } catch (err) {
    container.innerHTML = `<p style="color: red;">Failed to generate show notes: ${err.message}</p>`
    showStatus(`Failed to generate show notes: ${err.message}`, "error")
  }
}

// Generate quotes function
async function generateQuotes() {
  // First, ensure we have a container for the result
  let container = document.getElementById("quotes-output")
  if (!container) {
    // Try to find the parent container
    let resultSection = document.getElementById("generateQuotes-result")
    if (!resultSection) {
      // Create the container if it doesn't exist
      resultSection = document.createElement("div")
      resultSection.id = "generateQuotes-result"
      resultSection.className = "output-section"
      resultSection.style.display = "block"

      const heading = document.createElement("h2")
      heading.textContent = "Quotes"

      container = document.createElement("pre")
      container.id = "quotes-output"

      resultSection.appendChild(heading)
      resultSection.appendChild(container)

      // Add to the container
      const mainContainer = document.querySelector(".container")
      if (mainContainer) {
        mainContainer.appendChild(resultSection)
      } else {
        alert("Container not found. Please refresh the page.")
        return
      }
    } else {
      // If the container exists but not the result element
      container = document.createElement("pre")
      container.id = "quotes-output"
      resultSection.appendChild(container)
    }
  }

  // Make sure the container is visible
  const resultSection = document.getElementById("generateQuotes-result")
  if (resultSection) {
    resultSection.style.display = "block"
    resultSection.classList.add("visible")
  }

  // Show loading indicator
  container.innerHTML = '<div class="spinner"></div><p>Generating quotes... Please wait.</p>'
  showStatus("Generating quotes...", "info")

  try {
    if (!rawTranscript) {
      container.innerHTML = '<p style="color: red;">No transcript available. Please transcribe first.</p>'
      return
    }

    const res = await fetch("/transcription/quotes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcript: rawTranscript }),
    })

    if (res.status === 403) {
      const data = await res.json()
      container.innerHTML = `
        <p style="color: red;">${data.error || "You don't have enough credits."}</p>
        ${data.redirect ? `<a href="${data.redirect}" class="btn ai-edit-button">Go to Store</a>` : ""}
      `
      return
    }
    const data = await res.json()
    container.innerHTML = data.quotes || "No quotes."

    // Only consume credits after successful quotes generation
    await consumeStoreCredits("ai_quotes")
    showStatus("Quotes generated successfully!", "info")
  } catch (err) {
    container.innerHTML = `<p style="color: red;">Failed to generate quotes: ${err.message}</p>`
    showStatus(`Failed to generate quotes: ${err.message}`, "error")
  }
}

// Generate quote images function
async function generateQuoteImages() {
  const containerId = "quoteImagesResult"
  const container = document.getElementById(containerId)

  const quotes = document.getElementById("quotesResult").innerText.trim()
  const method = document.getElementById("quoteImageMethodSelect")?.value || "local"

  if (!quotes) {
    alert("Generate quotes first.")
    return
  }

  showSpinner(containerId)

  try {
    const res = await fetch("/transcription/quote_images", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quotes, method }),
    })

    const data = await res.json()
    container.innerHTML = ""

    if (res.status === 403) {
      container.innerHTML = `
        <p style="color: red;">${data.error || "You don't have enough credits."}</p>
        ${data.redirect ? `<a href="${data.redirect}" class="btn ai-edit-button">Go to Store</a>` : ""}
      `
      return
    }
    ;(data.quote_images || []).forEach((url) => {
      const img = document.createElement("img")
      img.src = url
      img.style.maxWidth = "100%"
      img.style.margin = "10px 0"
      container.appendChild(img)
    })

    // Only consume credits after successful quote images generation
    await consumeStoreCredits("ai_quote_images")
  } catch (err) {
    container.innerText = "Failed to generate quote images: " + err.message
  }
}

// Helper function to fetch audio from blob URL
async function fetchAudioFromBlobUrl(blobUrl) {
  try {
    const res = await fetch(blobUrl)
    if (!res.ok) throw new Error(`Failed to fetch audio: ${res.statusText}`)
    const blob = await res.blob()
    const objectUrl = URL.createObjectURL(blob)
    return { blob, objectUrl }
  } catch (err) {
    console.error("Error fetching audio from blob URL:", err)
    throw err
  }
}

// OSINT search function
async function runOsintSearch() {
  const containerId = "osintResult"
  const container = document.getElementById(containerId)

  const guestName = document.getElementById("guestNameInput").value
  if (!guestName.trim()) {
    alert("Please enter a guest name.")
    return
  }

  showSpinner(containerId)

  try {
    const response = await fetch("/transcription/osint_lookup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ guest_name: guestName }),
    })
    if (response.status === 403) {
      const data = await response.json()
      container.innerHTML = `
        <p style="color: red;">${data.error || "You don't have enough credits."}</p>
        ${data.redirect ? `<a href="${data.redirect}" class="btn ai-edit-button">Go to Store</a>` : ""}
      `
      return
    }
    const data = await response.json()
    container.innerText = data.osint_info || "No info found."

    // Only consume credits after successful OSINT search
    await consumeStoreCredits("ai_osint")
  } catch (err) {
    container.innerText = `Failed: ${err.message}`
  }
}

// Generate podcast intro/outro function
async function generatePodcastIntroOutro() {
  const containerId = "introOutroScriptResult"
  const container = document.getElementById(containerId)

  const guestName = document.getElementById("guestNameInput").value
  if (!guestName.trim()) return alert("Please enter a guest name.")
  if (!rawTranscript) return alert("No transcript available yet.")

  showSpinner(containerId)

  try {
    const res = await fetch("/transcription/generate_intro_outro", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        guest_name: guestName,
        transcript: rawTranscript,
      }),
    })
    if (res.status === 403) {
      const data = await res.json()
      container.innerHTML = `
        <p style="color: red;">${data.error || "You don't have enough credits."}</p>
        ${data.redirect ? `<a href="${data.redirect}" class="btn ai-edit-button">Go to Store</a>` : ""}
      `
      return
    }
    const data = await res.json()
    container.innerText = data.script || "No result."

    // Only consume credits after successful intro/outro generation
    await consumeStoreCredits("ai_intro_outro")
  } catch (err) {
    container.innerText = `Failed: ${err.message}`
  }
}

// Convert intro/outro to speech function
async function convertIntroOutroToSpeech() {
  const containerId = "introOutroAudioResult"
  const container = document.getElementById(containerId)

  const scriptContainer = document.getElementById("introOutroScriptResult")
  const script = scriptContainer ? scriptContainer.innerText.trim() : ""
  if (!script) return alert("No script to convert.")

  showSpinner(containerId)

  try {
    const res = await fetch("/transcription/intro_outro_audio", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ script }),
    })

    const data = await res.json()

    if (res.status === 403) {
      container.innerHTML = `
        <p style="color: red;">${data.error || "You don't have enough credits."}</p>
        ${data.redirect ? `<a href="${data.redirect}" class="btn ai-edit-button">Go to Store</a>` : ""}
      `
      return
    }

    if (data.audio_base64) {
      container.innerHTML = `
        <audio controls src="${data.audio_base64}"></audio>
        <a href="${data.audio_base64}" download="intro_outro.mp3" class="btn ai-edit-button">
          Download Intro/Outro Audio
        </a>
      `

      // Only consume credits after successful intro/outro audio conversion
      await consumeStoreCredits("ai_intro_outro_audio")
    } else {
      container.innerText = data.error || "Unknown error occurred."
    }
  } catch (err) {
    container.innerText = `Failed to convert to audio: ${err.message}`
  }
}

// Enhance audio function
async function enhanceAudio() {
  const containerId = "audioControls"
  const container = document.getElementById(containerId)
  if (!container) {
    // Create a container for results if it doesn't exist
    const resultsContainer = document.getElementById("ai-results-container") || document.querySelector(".container")
    if (resultsContainer) {
      const newContainer = document.createElement("div")
      newContainer.id = "audioControls"
      newContainer.className = "result-field"
      resultsContainer.appendChild(newContainer)
    } else {
      alert("Results container not found. Please refresh the page and try again.")
      return
    }
  }

  // Try to get the file input from either the tab content or the main page
  let input = document.getElementById("audioUploader")
  if (!input) {
    input = document.getElementById("audio-file")
    if (!input) {
      alert("Audio uploader element not found. Please upload a file using the file input above.")
      return
    }
  }

  const file = input.files && input.files[0]
  if (!file) return alert("Upload an audio file first.")

  const episodeId = getSelectedEpisodeId()
  if (!episodeId) return alert("No episode selected.")

  showSpinner(containerId)

  try {
    const formData = new FormData()
    formData.append("audio", file)
    formData.append("episode_id", episodeId)

    const response = await fetch("/audio/enhancement", {
      method: "POST",
      body: formData,
    })

    const result = await response.json()

    if (response.status === 403) {
      container.innerHTML = `
        <p style="color: red;">${result.error || "You don't have enough credits."}</p>
        ${result.redirect ? `<a href="${result.redirect}" class="btn ai-edit-button">Go to Store</a>` : ""}
      `
      return
    }
    if (!response.ok || !result.enhanced_audio_url) {
      throw new Error(result.error || "Enhancement failed.")
    }

    const blobUrl = result.enhanced_audio_url || result.clipUrl
    if (!blobUrl) {
      throw new Error("No audio URL returned")
    }

    const audioRes = await fetch(`/get_enhanced_audio?url=${encodeURIComponent(blobUrl)}`)
    const blob = await audioRes.blob()
    const url = URL.createObjectURL(blob)

    enhancedAudioBlob = blob
    activeAudioBlob = blob
    activeAudioId = "external"

    container.innerHTML = "<p>Audio enhancement complete!</p>"
    renderAudioPlayer("audioControls", blob, "enhancedAudioPlayer")

    const audioAnalysisSection = document.getElementById("audioAnalysisSection")
    if (audioAnalysisSection) audioAnalysisSection.style.display = "block"

    const audioCuttingSection = document.getElementById("audioCuttingSection")
    if (audioCuttingSection) audioCuttingSection.style.display = "block"

    const aiCuttingSection = document.getElementById("aiCuttingSection")
    if (aiCuttingSection) aiCuttingSection.style.display = "block"

    const dl = document.getElementById("downloadEnhanced")
    if (dl) {
      dl.href = url
      dl.style.display = "inline-block"
    }

    // Only consume credits after successful audio enhancement
    await consumeStoreCredits("audio_enhancement")
  } catch (err) {
    container.innerHTML = `Error: ${err.message}`
  }
}

// Voice isolation function
async function runVoiceIsolation() {
  const containerId = "isolatedVoiceResult"
  let container = document.getElementById(containerId)
  if (!container) {
    // Create a container for results if it doesn't exist
    const resultsContainer = document.getElementById("ai-results-container") || document.querySelector(".container")
    if (resultsContainer) {
      container = document.createElement("div")
      container.id = containerId
      container.className = "result-field"
      const heading = document.createElement("h3")
      heading.textContent = "Voice Isolation Result"
      resultsContainer.appendChild(heading)
      resultsContainer.appendChild(container)
    } else {
      alert("Results container not found. Please refresh the page and try again.")
      return
    }
  }

  // Try to get the file input from either the tab content or the main page
  let input = document.getElementById("audioUploader")
  if (!input) {
    input = document.getElementById("audio-file")
    if (!input) {
      alert("Audio uploader element not found. Please upload a file using the file input above.")
      return
    }
  }

  const file = input.files && input.files[0]
  if (!file) return alert("Upload an audio file first.")

  const episodeId = getSelectedEpisodeId()
  if (!episodeId) return alert("No episode selected.")

  showSpinner(containerId)

  try {
    const formData = new FormData()
    formData.append("audio", file)
    formData.append("episode_id", episodeId)

    const response = await fetch("/transcription/voice_isolate", {
      method: "POST",
      body: formData,
    })

    if (response.status === 403) {
      const data = await response.json()
      container.innerHTML = `
        <p style="color: red;">${data.error || "You don't have enough credits."}</p>
        ${data.redirect ? `<a href="${data.redirect}" class="btn ai-edit-button">Go to Store</a>` : ""}
      `
      return
    }

    const data = await response.json()
    const blobUrl = data.isolated_blob_url

    const audioRes = await fetch(`/transcription/get_isolated_audio?url=${encodeURIComponent(blobUrl)}`)
    const blob = await audioRes.blob()
    const url = URL.createObjectURL(blob)

    isolatedAudioBlob = blob
    activeAudioBlob = blob
    activeAudioId = "external"

    renderAudioPlayer(containerId, blob, "isolatedAudioPlayer")

    const audioAnalysisSection = document.getElementById("audioAnalysisSection")
    if (audioAnalysisSection) audioAnalysisSection.style.display = "block"

    const audioCuttingSection = document.getElementById("audioCuttingSection")
    if (audioCuttingSection) audioCuttingSection.style.display = "block"

    const aiCuttingSection = document.getElementById("aiCuttingSection")
    if (aiCuttingSection) aiCuttingSection.style.display = "block"

    const dl = document.getElementById("downloadIsolatedVoice")
    if (dl) {
      dl.href = url
      dl.style.display = "inline-block"
    }

    // Only consume credits after successful voice isolation
    await consumeStoreCredits("voice_isolation")
  } catch (err) {
    console.error("Voice isolation failed:", err)
    container.innerText = `Isolation failed: ${err.message}`
  }
}

// Analyze enhanced audio function
let selectedSoundFX = {}
async function analyzeEnhancedAudio() {
  const containerId = "analysisResults"
  const container = document.getElementById(containerId)
  const timeline = document.getElementById("soundEffectTimeline")
  const mixBtn = document.getElementById("mixBackgroundBtn")

  if (!activeAudioBlob) {
    return alert("No audio loaded. Enhance or Isolate first.")
  }

  showSpinner(containerId)

  try {
    const fd = new FormData()
    fd.append("audio", activeAudioBlob, "processed_audio.wav")

    const res = await fetch("/audio_analysis", { method: "POST", body: fd })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || res.statusText)

    container.innerText = `
      Sentiment:     ${data.sentiment ?? "–"}
      Clarity Score: ${data.clarity_score ?? "–"}
      Noise Level:   ${data.background_noise ?? "–"}
      Dominant Emo:  ${data.dominant_emotion}
    `

    timeline.innerHTML = ""
    renderSoundSuggestions(data, timeline)

    window.analysisData = {
      emotion: data.dominant_emotion,
      audioBlob: activeAudioBlob,
    }

    mixBtn.style.display = "inline-block"

    // Only consume credits after successful audio analysis
    await consumeStoreCredits("ai_audio_analysis")
  } catch (err) {
    container.innerText = `Analysis failed: ${err.message}`
  }
}

// Render sound suggestions function
function renderSoundSuggestions(data, timeline) {
  timeline.innerHTML = "<h4>AI-Driven Sound Suggestions</h4>"
  selectedSoundFX = {}
  ;(data.sound_effect_suggestions || []).forEach((entry, i) => {
    const sfxList = entry.sfx_options || []
    const container = document.createElement("div")
    container.className = "sound-suggestion"
    container.innerHTML = `
      <p><strong>Text:</strong> ${entry.timestamp_text}</p>
      <p><strong>Emotion:</strong> ${entry.emotion}</p>
      ${sfxList.length ? `<audio controls src="${sfxList[0]}" class="sfx-preview"></audio>` : "<em>No preview.</em>"}
    `
    timeline.appendChild(container)
    if (sfxList.length) {
      selectedSoundFX[i] = { emotion: entry.emotion, sfxUrl: sfxList[0] }
    }
  })
}

// Display background and mix function
async function displayBackgroundAndMix() {
  const preview = document.getElementById("backgroundPreview")
  const mixBtn = document.getElementById("mixBackgroundBtn")
  const dl = document.getElementById("downloadEnhanced")
  const timeline = document.getElementById("soundEffectTimeline")
  const { audioBlob } = window.analysisData || {}

  console.log("Starting displayBackgroundAndMix function")

  if (!audioBlob) {
    console.error("No audioBlob available in window.analysisData")
    return alert("Run analysis first!")
  }

  console.log(`Audio blob size: ${audioBlob.size} bytes, type: ${audioBlob.type}`)

  // Disable button & show spinner text
  mixBtn.disabled = true
  mixBtn.innerText = "Generating…"
  preview.innerHTML = ""

  const fd = new FormData()
  fd.append("audio", audioBlob, "processed_audio.wav")
  console.log("FormData created with audio blob")

  try {
    console.log("Sending request to /plan_and_mix_sfx endpoint")
    // Call our new endpoint that uses the GPT-based SFX plan
    const res = await fetch("/plan_and_mix_sfx", { method: "POST", body: fd })
    console.log(`Response status: ${res.status}`)

    const data = await res.json()
    console.log("Response data received:", data)

    if (!res.ok) {
      console.error(`Error response: ${data.error || res.statusText}`)
      throw new Error(data.error || res.statusText)
    }

    // Check if we have a valid SFX plan
    if (!data.sfx_plan || data.sfx_plan.length === 0) {
      console.warn("No SFX plan returned from server")
      preview.innerHTML = `
        <div class="alert alert-warning">
          <p>No sound effects were generated for this audio.</p>
          <p>This might be because:</p>
          <ul>
            <li>The content doesn't have clear opportunities for sound effects</li>
            <li>The GPT model couldn't identify suitable moments</li>
            <li>There was an issue with the SFX generation process</li>
          </ul>
        </div>
      `
    } else {
      console.log(`Received SFX plan with ${data.sfx_plan.length} effects`)

      // Render the SFX plan
      timeline.innerHTML = "<h4>AI-Generated Sound Effects Plan</h4>"
      renderSfxPlan(data.sfx_plan, timeline)
    }

    // Check if we have mixed audio
    if (data.merged_audio) {
      console.log(`Received merged audio (${data.merged_audio.length} characters)`)
      preview.innerHTML = `
        <h4>Mixed Preview</h4>
        <audio controls src="${data.merged_audio}" style="width:100%;"></audio>
      `
      // Update download link
      dl.href = data.merged_audio
      dl.style.display = "inline-block"

      // Only consume credits after successful background mixing
      await consumeStoreCredits("ai_audio_analysis")
    } else {
      console.warn("No merged audio in response")
      preview.innerHTML += `<p class="text-warning">No mixed audio was returned from the server.</p>`
    }
  } catch (err) {
    console.error("Error in displayBackgroundAndMix:", err)
    preview.innerText = `Error: ${err.message}`
  } finally {
    // Restore button
    mixBtn.disabled = false
    mixBtn.innerText = "Mix Background & Preview"
    console.log("displayBackgroundAndMix function completed")
  }
}

/* Renders the GPT-generated SFX plan */
function renderSfxPlan(sfxPlan, timeline) {
  console.log(`Rendering SFX plan with ${sfxPlan.length} effects`)
  selectedSoundFX = {}
  ;(sfxPlan || []).forEach((entry, i) => {
    console.log(`Rendering SFX ${i}: ${entry.description} [${entry.start}s - ${entry.end}s]`)

    const container = document.createElement("div")
    container.className = "sound-suggestion"

    // Check if we have a valid sfxUrl
    const hasAudio = entry.sfxUrl && entry.sfxUrl.startsWith("data:")
    console.log(`SFX ${i} has audio: ${hasAudio}`)

    container.innerHTML = `
    <p><strong>Description:</strong> ${entry.description}</p>
    <p><strong>Timing:</strong> ${entry.start.toFixed(2)}s - ${entry.end.toFixed(2)}s</p>
    ${
      hasAudio
        ? `<audio controls src="${entry.sfxUrl}" class="sfx-preview"></audio>`
        : "<em>No audio preview available.</em>"
    }
    <!-- SFX interaction controls (disabled for now) -->
    <!--
    <div class="sfx-controls">
        <button class="btn btn-sm" onclick="acceptSfx(${i}, '${entry.description}', '${entry.sfxUrl || ""}')">Accept</button>
        <button class="btn btn-sm" onclick="rejectSfx(${i})">Reject</button>
    </div>
    -->
    `
    timeline.appendChild(container)

    if (hasAudio) {
      selectedSoundFX[i] = {
        description: entry.description,
        sfxUrl: entry.sfxUrl,
        start: entry.start,
        end: entry.end,
      }
    }
  })

  console.log("SFX plan rendering complete")
}

// Cut audio function
async function cutAudio() {
  const startInput = document.getElementById("cut-start")
  const endInput = document.getElementById("cut-end")
  const cutResult = document.getElementById("cutResult")
  const dl = document.getElementById("downloadCut")

  const start = Number.parseFloat(startInput.value)
  const end = Number.parseFloat(endInput.value)

  const episodeId = getSelectedEpisodeId()
  if (!episodeId) return alert("No episode selected.")

  const selectedSource = document.getElementById("audioSourceSelectCutting").value

  let blobToUse
  if (selectedSource === "enhanced") {
    blobToUse = enhancedAudioBlob
  } else if (selectedSource === "isolated") {
    blobToUse = isolatedAudioBlob
  } else if (selectedSource === "original") {
    blobToUse = rawAudioBlob
  }

  if (!blobToUse) return alert("No audio selected or loaded.")
  if (isNaN(start) || isNaN(end) || start >= end) return alert("Invalid timestamps.")

  const formData = new FormData()
  formData.append("audio", new File([blobToUse], "clip.wav", { type: "audio/wav" }))
  formData.append("episode_id", episodeId)
  formData.append("start", start)
  formData.append("end", end)

  try {
    const response = await fetch("/cut_from_blob", {
      method: "POST",
      body: formData,
    })

    const result = await response.json()

    if (response.status === 403) {
      cutResult.innerHTML = `
        <p style="color: red;">${result.error || "You don't have enough credits."}</p>
        ${result.redirect ? `<a href="${result.redirect}" class="btn ai-edit-button">Go to Store</a>` : ""}
      `
      return
    }

    if (!response.ok || !result.clipped_audio_url) {
      throw new Error(result.error || "Clipping failed.")
    }

    const proxyUrl = `/get_clipped_audio?url=${encodeURIComponent(result.clipped_audio_url)}`
    const audioRes = await fetch(proxyUrl)
    if (!audioRes.ok) throw new Error("Failed to fetch clipped audio.")
    const blob = await audioRes.blob()
    const url = URL.createObjectURL(blob)

    cutResult.innerHTML = `<audio controls src="${url}" style="width: 100%;"></audio>`
    dl.href = url
    dl.download = "clipped_audio.wav"
    dl.style.display = "inline-block"

    activeAudioBlob = blob
    activeAudioId = "external"

    // Only consume credits after successful audio cutting
    await consumeStoreCredits("audio_cutting")
  } catch (err) {
    alert(`Cut failed: ${err.message}`)
  }
}

// AI cut audio function
async function aiCutAudio() {
  const episodeId = getSelectedEpisodeId()
  if (!episodeId) {
    alert("No episode selected.")
    return
  }

  const selectedSource = document.getElementById("audioSourceSelectAICut").value

  let blobToUse
  if (selectedSource === "enhanced") {
    blobToUse = enhancedAudioBlob
    activeAudioId = "external"
  } else if (selectedSource === "isolated") {
    blobToUse = isolatedAudioBlob
    activeAudioId = "external"
  } else if (selectedSource === "original") {
    blobToUse = rawAudioBlob
    activeAudioId = "external"
  }

  if (!blobToUse) {
    alert("No audio selected or loaded.")
    return
  }

  activeAudioBlob = blobToUse

  const containerIdTranscript = "aiTranscript"
  const containerTranscript = document.getElementById(containerIdTranscript)
  const containerIdCuts = "aiSuggestedCuts"
  const containerCuts = document.getElementById(containerIdCuts)

  showSpinner(containerIdTranscript)
  containerCuts.innerHTML = ""

  try {
    let response
    if (!activeAudioId || activeAudioId === "external") {
      const formData = new FormData()
      formData.append("audio", new File([blobToUse], "ai_cut.wav", { type: "audio/wav" }))
      formData.append("episode_id", episodeId)

      response = await fetch("/ai_cut_from_blob", {
        method: "POST",
        body: formData,
      })
    } else {
      response = await fetch("/ai_cut_audio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_id: activeAudioId,
          episode_id: episodeId,
        }),
      })
    }

    const data = await response.json()

    if (response.status === 403) {
      containerTranscript.innerHTML = `
        <p style="color: red;">${data.error || "You don't have enough credits."}</p>
        ${data.redirect ? `<a href="${data.redirect}" class="btn ai-edit-button">Go to Store</a>` : ""}
      `
      return
    }

    if (!response.ok) {
      throw new Error(data.error || "AI Cut failed")
    }

    containerTranscript.innerText = data.cleaned_transcript || "No transcript available."

    const suggestedCuts = data.suggested_cuts || []
    if (!suggestedCuts.length) {
      containerCuts.innerText = "No suggested cuts found."
      return
    }

    containerCuts.innerHTML = ""
    window.selectedAiCuts = {}

    suggestedCuts.forEach((cut, index) => {
      const checkbox = document.createElement("input")
      checkbox.type = "checkbox"
      checkbox.checked = true
      checkbox.dataset.index = index
      checkbox.onchange = () => {
        if (checkbox.checked) {
          window.selectedAiCuts[index] = cut
        } else {
          delete window.selectedAiCuts[index]
        }
      }
      window.selectedAiCuts[index] = cut

      const label = document.createElement("label")
      label.innerText = ` "${cut.sentence}" (${cut.start}s - ${cut.end}s) | Confidence: ${cut.certainty_score.toFixed(2)}`

      const div = document.createElement("div")
      div.appendChild(checkbox)
      div.appendChild(label)
      containerCuts.appendChild(div)
    })

    const applyBtn = document.createElement("button")
    applyBtn.className = "btn ai-edit-button"
    applyBtn.innerText = "Apply AI Cuts"
    applyBtn.onclick = applySelectedCuts
    containerCuts.appendChild(applyBtn)

    // Only consume credits after successful AI audio cutting
    await consumeStoreCredits("ai_audio_cutting")
  } catch (err) {
    containerTranscript.innerText = "Failed to process audio."
    alert(`AI Cut failed: ${err.message}`)
  }
}

// Apply selected cuts function
async function applySelectedCuts() {
  const cuts = Object.values(window.selectedAiCuts || {})
  if (!cuts.length) {
    alert("No cuts selected.")
    return
  }

  const episodeId = getSelectedEpisodeId()

  try {
    let blobUrl

    // Send to the right backend depending on where the audio is
    if (activeAudioId === "external") {
      const formData = new FormData()
      formData.append("audio", new File([activeAudioBlob], "cleaned.wav", { type: "audio/wav" }))
      formData.append("episode_id", episodeId)
      formData.append("cuts", JSON.stringify(cuts))

      const response = await fetch("/apply_ai_cuts_from_blob", {
        method: "POST",
        body: formData,
      })

      const result = await response.json()
      if (!response.ok) throw new Error(result.error || "Apply failed")
      blobUrl = result.cleaned_file_url
    } else {
      const response = await fetch("/apply_ai_cuts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_id: activeAudioId,
          cuts: cuts.map((c) => ({ start: c.start, end: c.end })),
          episode_id: episodeId,
        }),
      })

      const result = await response.json()
      if (!response.ok) throw new Error(result.error || "Apply failed")
      blobUrl = result.cleaned_file_url
    }

    // Use backend proxy to avoid CORS
    const proxyUrl = `/get_clipped_audio?url=${encodeURIComponent(blobUrl)}`
    const audioRes = await fetch(proxyUrl)
    if (!audioRes.ok) throw new Error("Failed to fetch clipped audio.")
    const blob = await audioRes.blob()
    const url = URL.createObjectURL(blob)

    // Show player and download button
    const section = document.getElementById("aiCuttingSection")
    section.appendChild(document.createElement("hr"))

    const player = document.createElement("audio")
    player.controls = true
    player.src = url
    section.appendChild(player)

    const dl = document.createElement("a")
    dl.href = url
    dl.download = "ai_cleaned_audio.wav"
    dl.className = "btn ai-edit-button"
    dl.innerText = "Download Cleaned Audio"
    section.appendChild(dl)

    // Update active blob
    activeAudioBlob = blob
    activeAudioId = "external"

    // No credit consumption here as it's already done in aiCutAudio
  } catch (err) {
    alert(`Apply failed: ${err.message}`)
  }
}

// Enhance video function
async function enhanceVideo() {
  const fileInput = document.getElementById("videoUploader")
  if (!fileInput) {
    alert("Video uploader element not found. Please make sure you're on the correct tab.")
    return
  }

  const file = fileInput.files && fileInput.files[0]
  if (!file) {
    alert("Please upload a video file.")
    return
  }

  const containerId = "videoResult"
  const container = document.getElementById(containerId)
  if (!container) {
    alert("Video result container not found. Please make sure you're on the correct tab.")
    return
  }

  showSpinner(containerId)

  try {
    const formData = new FormData()
    formData.append("video", file)

    const uploadResponse = await fetch("/ai_videoedit", {
      method: "POST",
      body: formData,
    })

    if (!uploadResponse.ok) {
      throw new Error(`Video upload failed: ${uploadResponse.statusText}`)
    }

    const uploadResult = await uploadResponse.json()
    const video_id = uploadResult.video_id
    if (!video_id) throw new Error("No video_id returned from upload.")

    const enhanceResponse = await fetch("/ai_videoenhance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ video_id }),
    })

    const enhanceResult = await enhanceResponse.json()

    if (enhanceResponse.status === 403) {
      container.innerHTML = `
        <p style="color: red;">${enhanceResult.error || "You don't have enough credits."}</p>
        ${enhanceResult.redirect ? `<a href="${enhanceResult.redirect}" class="btn ai-edit-button">Go to Store</a>` : ""}
      `
      return
    }

    if (!enhanceResponse.ok || !enhanceResult.processed_video_id) {
      throw new Error(enhanceResult.error || "Enhancement failed.")
    }

    const processed_id = enhanceResult.processed_video_id
    const videoURL = `/get_video/${processed_id}`
    container.innerHTML = `
      <video controls src="${videoURL}" style="width: 100%; margin-top: 1rem;"></video>
    `

    const dl = document.getElementById("downloadVideo")
    if (dl) {
      dl.href = videoURL
      dl.style.display = "inline-block"
    }

    // Only consume credits after successful video enhancement
    await consumeStoreCredits("video_enhancement")
  } catch (err) {
    container.innerText = `Error: ${err.message}`
  }
}

// Preview original audio function
function previewOriginalAudio() {
  const fileInput = document.getElementById("audioUploader")
  if (!fileInput) {
    console.error("Audio uploader element not found")
    return
  }

  const file = fileInput.files && fileInput.files[0]
  if (!file) return

  rawAudioBlob = file

  const container = document.getElementById("originalAudioContainer")
  if (!container) {
    console.error("Original audio container not found")
    return
  }

  container.style.display = "block"

  renderAudioPlayer("originalAudioContainer", rawAudioBlob, "originalAudioPlayer")
}

// Preview original video function
function previewOriginalVideo() {
  const fileInput = document.getElementById("videoUploader")
  if (!fileInput) {
    console.error("Video uploader element not found")
    return
  }

  const file = fileInput.files && fileInput.files[0]
  if (!file) return

  const videoURL = URL.createObjectURL(file)
  const videoPlayer = document.getElementById("originalVideoPlayer")
  const container = document.getElementById("originalVideoContainer")

  if (!videoPlayer || !container) {
    console.error("Video player or container elements not found")
    return
  }

  videoPlayer.src = videoURL
  container.style.display = "block"
}

// Generate audio clip function
async function generateAudioClip() {
  const container = document.getElementById("audioClipResult")
  const translated = document.getElementById("translateResult").innerText
  if (!translated.trim()) return alert("No translated transcript available to generate an podcast.")

  showSpinner("audioClipResult")
  try {
    const res = await fetch("/transcription/audio_clip", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ translated_transcription: translated }),
    })
    hideSpinner("audioClipResult")

    if (!res.ok) throw new Error(`Server svarade ${res.status}`)
    const data = await res.json()
    const audio = document.createElement("audio")
    audio.controls = true
    audio.src = data.audio_base64
    container.innerHTML = ""
    container.appendChild(audio)

    // Only consume credits after successful audio clip generation
    await consumeStoreCredits("audio_clip")
  } catch (err) {
    hideSpinner("audioClipResult")
    container.innerText = `Failed to generate audio clip: ${err.message}`
  }
}

// Render audio player function
function renderAudioPlayer(containerId, audioBlob, playerId, options = {}) {
  const container = document.getElementById(containerId)
  container.innerHTML = ""

  const url = URL.createObjectURL(audioBlob)

  const audioEl = document.createElement("audio")
  audioEl.id = playerId
  audioEl.src = url
  audioEl.style = "display: none;"
  container.appendChild(audioEl)

  const playBtn = document.createElement("button")
  playBtn.className = "btn ai-edit-button"
  playBtn.textContent = "Play"
  container.appendChild(playBtn)

  const waveformDiv = document.createElement("div")
  waveformDiv.id = `${playerId}_waveform`
  waveformDiv.style = "width: 100%; height: 96px; margin-top: 1rem;"
  container.appendChild(waveformDiv)

  // Check if WaveSurfer is available
  if (window.WaveSurfer) {
    const wavesurfer = WaveSurfer.create({
      container: `#${playerId}_waveform`,
      waveColor: "#ccc",
      progressColor: "#f69229",
      height: 96,
      barWidth: 2,
      responsive: true,
      backend: "MediaElement",
      media: audioEl,
    })

    wavesurfer.load(url)

    if (options.onWaveformClick) {
      wavesurfer.on("click", options.onWaveformClick)
    }
  } else {
    waveformDiv.innerHTML = "<p>WaveSurfer not available. Simple audio player shown.</p>"
  }

  playBtn.addEventListener("click", () => {
    if (audioEl.paused) {
      audioEl.play()
      playBtn.textContent = "Pause"
    } else {
      audioEl.pause()
      playBtn.textContent = "Play"
    }
  })

  audioEl.addEventListener("ended", () => {
    playBtn.textContent = "Play"
  })
}

// Helper functions for SFX
function acceptSfx(index, emotion, url) {
  selectedSoundFX[index] = { emotion, sfxUrl: url }
}

function rejectSfx(index) {
  delete selectedSoundFX[index]
}

function replaceSfx(index, url) {
  if (selectedSoundFX[index]) {
    selectedSoundFX[index].sfxUrl = url
  }
}

// Show spinner function
function showSpinner(containerId) {
  const container = document.getElementById(containerId)
  if (container) {
    container.innerHTML = '<div class="spinner"></div>'
  }
}

// Hide spinner function
function hideSpinner(containerId) {
  const container = document.getElementById(containerId)
  if (container) {
    container.innerHTML = ""
  }
}

// Get selected episode ID
function getSelectedEpisodeId() {
  return (
    sessionStorage.getItem("selected_episode_id") ||
    localStorage.getItem("selected_episode_id") ||
    window.CURRENT_EPISODE_ID
  )
}

// Consume store credits function
async function consumeStoreCredits(featureKey) {
  if (!window.CURRENT_USER_ID) {
    console.warn("User not logged in, skipping credit consumption")
    return
  }

  try {
    const res = await fetch("/credits/consume", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: window.CURRENT_USER_ID,
        feature: featureKey,
      }),
    })

    const result = await res.json()
    if (!res.ok) {
      throw new Error(result.error || "Failed to consume credits")
    }

    if (window.populateStoreCredits) {
      await window.populateStoreCredits()
    }

    return result.data
  } catch (err) {
    console.error("Error consuming credits:", err)
  }
}
