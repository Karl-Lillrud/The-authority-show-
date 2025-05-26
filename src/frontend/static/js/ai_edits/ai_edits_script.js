/**
 * AI Podcast Editing Script
 * Handles the client-side logic for processing audio through the AI pipeline
 */

// Global variables
let activeAudioBlob = null;
// Ensure CURRENT_EPISODE_ID is loaded from session
const storedEpisodeId = sessionStorage.getItem("selected_episode_id") || localStorage.getItem("selected_episode_id");
let CURRENT_EPISODE_ID = storedEpisodeId || `episode_${Date.now()}`;

// AI processing options with dependencies
const aiOptions = [
  {
    id: "transcribe",
    title: "Transcribe Audio",
    description: "Convert speech to text using AI",
    icon: "T",
    dependencies: {},
    resultContainer: "transcribe-result"
  },
  {
    id: "cleanTranscript",
    title: "Clean Transcript",
    description: "Remove filler words and improve readability",
    icon: "C",
    dependencies: {
      transcribe: "Transcription is required first"
    },
    resultContainer: "cleanTranscript-result"
  },
  {
    id: "enhanceAudio",
    title: "Enhance Audio",
    description: "Improve audio quality and reduce noise",
    icon: "E",
    dependencies: {},
    resultContainer: "enhanceAudio-result"
  },
  {
    id: "aiCut",
    title: "AI Cut Suggestions",
    description: "Get AI suggestions for content cuts",
    icon: "A",
    dependencies: {
      transcribe: "Transcription is required for AI cuts"
    },
    resultContainer: "aiCut-result"
  },
  {
    id: "voice_isolation",
    title: "Voice Isolation",
    description: "Separate voice from background noise",
    icon: "V",
    dependencies: {},
    resultContainer: "voiceIsolation-result"
  },
  {
    id: "generateShowNotes",
    title: "Generate Show Notes",
    description: "Create detailed notes from your content",
    icon: "N",
    dependencies: {
      transcribe: "Transcription is required for show notes"
    },
    resultContainer: "generateShowNotes-result"
  },
  {
    id: "aiSuggestions",
    title: "AI Suggestions",
    description: "Get content improvement recommendations",
    icon: "S",
    dependencies: {
      transcribe: "Transcription is required for AI suggestions"
    },
    resultContainer: "aiSuggestions-result"
  },
  {
    id: "generateQuotes",
    title: "Generate Quotes",
    description: "Extract quotable moments from your content",
    icon: "Q",
    dependencies: {
      transcribe: "Transcription is required for quotes"
    },
    resultContainer: "generateQuotes-result"
  },
  {
  id: "analyzeAudio",
  title: "Analyze Audio",
  description: "Analyze audio to extract timestamps and metadata",
  icon: "🔍",
  dependencies: {},
  resultContainer: "analyzeAudio-result"
  },
  {
    id: "planAndMixSfx",
    title: "Plan & Mix Sound Effects",
    description: "Add sound effects to your podcast",
    icon: "M",
    dependencies: {
      transcribe: "Transcription is required for sound effect planning"
    },
    resultContainer: "planAndMixSfx-result"
  }
];

// Initialize the page when DOM is loaded
document.addEventListener("DOMContentLoaded", function() {
  // Generate a random episode ID if not already set
  CURRENT_EPISODE_ID = CURRENT_EPISODE_ID || `episode_${Date.now()}`;
  
  // Populate the options list
  populateOptionsList();
  
  // Set up event listeners
  setupEventListeners();
  
  // Update UI state
  updateUIState();
});

/**
 * Populates the options list with AI processing options
 */
function populateOptionsList() {
  const optionList = document.getElementById("option-list");
  if (!optionList) return;
  
  optionList.innerHTML = "";
  
  aiOptions.forEach((option, index) => {
    const optionItem = document.createElement("div");
    optionItem.className = "option-item";
    optionItem.dataset.optionId = option.id;
    
    // Check if option should be disabled based on dependencies
    const isDisabled = !checkDependenciesMet(option);
    if (isDisabled) {
      optionItem.classList.add("disabled-option");
    }
    
    optionItem.innerHTML = `
      <div class="option-icon">${option.icon}</div>
      <div class="option-content">
        <div class="option-title">${option.title}</div>
        <div class="option-description">${option.description}</div>
      </div>
      <input type="checkbox" class="option-checkbox" data-function="${option.id}" ${isDisabled ? 'disabled' : ''}>
    `;
    
    // Add tooltip for disabled options
    if (isDisabled) {
      const dependencyMessages = [];
      for (const [depId, message] of Object.entries(option.dependencies)) {
        dependencyMessages.push(message);
      }
      
      if (dependencyMessages.length > 0) {
        optionItem.addEventListener("mouseenter", function(e) {
          const tooltip = document.createElement("div");
          tooltip.className = "dependency-tooltip";
          tooltip.textContent = dependencyMessages.join(", ");
          this.appendChild(tooltip);
        });
        
        optionItem.addEventListener("mouseleave", function() {
          const tooltip = this.querySelector(".dependency-tooltip");
          if (tooltip) {
            tooltip.remove();
          }
        });
      }
    }
    
    optionList.appendChild(optionItem);
  });
}

/**
 * Sets up event listeners for the page
 */
function setupEventListeners() {
  // Run button click handler
  const runButton = document.getElementById("run-button");
  if (runButton) {
    runButton.addEventListener("click", handleRunButtonClick);
  }
  
  // Audio file input change handler
  const audioFileInput = document.getElementById("audio-file");
  if (audioFileInput) {
    audioFileInput.addEventListener("change", handleFileInputChange);
  }
  
  // Option checkbox change handler
  document.addEventListener("change", function(e) {
    if (e.target.classList.contains("option-checkbox")) {
      handleOptionCheckboxChange(e.target);
    }
  });
}

/**
 * Handles file input change
 * @param {Event} e - The change event
 */
function handleFileInputChange(e) {
  const file = e.target.files[0];
  if (!file) {
    activeAudioBlob = null;
    updateFileInfo("");
    return;
  }
  
  // Check if file is audio
  if (!file.type.startsWith("audio/") && !file.type.startsWith("video/")) {
    showStatusMessage("Please select an audio or video file", "error");
    e.target.value = "";
    activeAudioBlob = null;
    updateFileInfo("");
    return;
  }
  
  // Store the file as blob
  activeAudioBlob = file;
  
  // Update file info display
  updateFileInfo(`Selected: ${file.name} (${formatFileSize(file.size)})`);
  
  // Clear status message
  hideStatusMessage();
}

/**
 * Updates the file info display
 * @param {string} message - The message to display
 */
function updateFileInfo(message) {
  const fileInfo = document.getElementById("file-info");
  if (fileInfo) {
    fileInfo.textContent = message;
  }
}

/**
 * Formats file size in human-readable format
 * @param {number} bytes - The file size in bytes
 * @returns {string} - Formatted file size
 */
function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";
  
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

/**
 * Handles option checkbox change
 * @param {HTMLInputElement} checkbox - The changed checkbox
 */
function handleOptionCheckboxChange(checkbox) {
  const functionId = checkbox.dataset.function;
  const isChecked = checkbox.checked;
  
  // If auto-select dependencies is enabled and checkbox is checked
  if (window.autoSelectDependencies && isChecked) {
    selectDependencies(functionId);
  }
  
  // Update execution order preview
  updateExecutionPreview();
  
  // Update UI state
  updateUIState();
}

/**
 * Selects all dependencies for a function
 * @param {string} functionId - The function ID
 */
function selectDependencies(functionId) {
  const option = aiOptions.find(opt => opt.id === functionId);
  if (!option || !option.dependencies) return;
  
  // For each dependency
  Object.keys(option.dependencies).forEach(depId => {
    const depCheckbox = document.querySelector(`.option-checkbox[data-function="${depId}"]`);
    if (depCheckbox && !depCheckbox.checked) {
      depCheckbox.checked = true;
      depCheckbox.dispatchEvent(new Event("change")); // 🛠 triggar UI + order
    }
  });
}

/**
 * Updates the execution order preview
 */
function updateExecutionPreview() {
  const previewContainer = document.getElementById("execution-preview");
  if (!previewContainer) return;
  
  const checkedBoxes = Array.from(document.querySelectorAll(".option-checkbox:checked"));
  
  if (checkedBoxes.length === 0) {
    previewContainer.innerHTML = "<em>Select functions to see execution order</em>";
    return;
  }
  
  const functionIds = checkedBoxes.map(cb => cb.dataset.function);
  const sortedFunctions = sortFunctionsByDependencies(functionIds);
  
  let html = '<ol style="margin: 0; padding-left: 20px;">';
  sortedFunctions.forEach(funcId => {
    const option = aiOptions.find(opt => opt.id === funcId);
    if (option) {
      html += `<li><strong>${option.title}</strong></li>`;
    }
  });
  html += "</ol>";
  
  previewContainer.innerHTML = html;
}

/**
 * Sorts functions by their dependencies
 * @param {string[]} functionIds - Array of function IDs
 * @returns {string[]} - Sorted array of function IDs
 */
function sortFunctionsByDependencies(functionIds) {
  // Create a dependency graph
  const graph = {};
  const options = [];

  function collectAllDependencies(optionId, visited = new Set()) {
    if (visited.has(optionId)) return;
    visited.add(optionId);
    const opt = aiOptions.find(o => o.id === optionId);
    if (!opt) return;
    options.push(opt);
    if (opt.dependencies) {
      Object.keys(opt.dependencies).forEach(dep => collectAllDependencies(dep, visited));
    }
  }

  functionIds.forEach(id => collectAllDependencies(id));
  
  // Initialize graph
  options.forEach(opt => {
    graph[opt.id] = [];
  });
  
  // Add dependencies
  options.forEach(opt => {
    if (opt.dependencies) {
      Object.keys(opt.dependencies).forEach(depId => {
        if (functionIds.includes(depId)) {
          graph[depId].push(opt.id);
        }
      });
    }
  });
  
  // Topological sort
  const visited = {};
  const temp = {};
  const result = [];
  
  function visit(node) {
    if (temp[node]) {
      // Circular dependency detected
      return;
    }
    if (!visited[node]) {
      temp[node] = true;
      
      // Visit dependencies
      graph[node].forEach(dep => {
        visit(dep);
      });
      
      temp[node] = false;
      visited[node] = true;
      result.unshift(node);
    }
  }
  
  // Visit all nodes
  Object.keys(graph).forEach(node => {
    if (!visited[node]) {
      visit(node);
    }
  });
  
  return result;
}

/**
 * Checks if all dependencies for an option are met
 * @param {Object} option - The option to check
 * @returns {boolean} - True if all dependencies are met
 */
function checkDependenciesMet(option) {
  if (!option.dependencies || Object.keys(option.dependencies).length === 0) {
    return true;
  }
  
  // Check each dependency
  for (const depId of Object.keys(option.dependencies)) {
    const depOption = aiOptions.find(opt => opt.id === depId);
    if (!depOption) {
      return false;
    }
  }
  
  return true;
}

/**
 * Updates the UI state based on current selections
 */
function updateUIState() {
  // Update option availability based on dependencies
  aiOptions.forEach(option => {
    const optionItem = document.querySelector(`.option-item[data-option-id="${option.id}"]`);
    const checkbox = optionItem?.querySelector(".option-checkbox");
    
    if (optionItem && checkbox) {
      const shouldBeDisabled = !checkDependenciesMet(option);
      
      if (shouldBeDisabled) {
        optionItem.classList.add("disabled-option");
        checkbox.disabled = true;
      } else {
        optionItem.classList.remove("disabled-option");
        checkbox.disabled = false;
      }
    }
  });
  
  // Update run button state
  const runButton = document.getElementById("run-button");
  if (runButton) {
    const hasAudioFile = !!activeAudioBlob;
    const hasSelectedOptions = document.querySelectorAll(".option-checkbox:checked").length > 0;
    
    if (!hasAudioFile || !hasSelectedOptions) {
      runButton.classList.add("disabled-button");
      runButton.disabled = true;
    } else {
      runButton.classList.remove("disabled-button");
      runButton.disabled = false;
    }
  }
}

/**
 * Handles run button click
 */
function handleRunButtonClick() {
  // Validate inputs
  if (!activeAudioBlob) {
    showStatusMessage("Please select an audio file", "warning");
    return;
  }
  
  const selectedOptions = Array.from(document.querySelectorAll(".option-checkbox:checked"));
  if (selectedOptions.length === 0) {
    showStatusMessage("Please select at least one AI function", "warning");
    return;
  }
  
  // Get selected steps
const selectedSteps = selectedOptions.map(checkbox => checkbox.dataset.function);

// Map frontend IDs to backend step names
const stepMappings = {
  transcribe: "transcribe",
  enhanceAudio: "enhance",
  aiCut: "ai_cut",
  voice_isolation: "voice_isolation",
  cleanTranscript: "clean_transcript",
  planAndMixSfx: "plan_and_mix_sfx",
  analyzeAudio: "analyze_audio",
  generateShowNotes: "generate_show_notes",
  aiSuggestions: "ai_suggestions",
  generateQuotes: "generate_quotes"
};



// Sort steps by dependencies (still frontend IDs)
const sortedSteps = sortFunctionsByDependencies(selectedSteps);

// Map sorted steps to backend-compatible step names
const mappedSteps = sortedSteps.map(step => stepMappings[step] || step);

// Show loading state
showStatusMessage("Processing audio...", "info");
showSpinner();

// Create form data
const formData = new FormData();
formData.append("audio", activeAudioBlob);
formData.append("episode_id", CURRENT_EPISODE_ID);
formData.append("steps", JSON.stringify(mappedSteps));  // ✅ Fixat här

  
  // Send request to server
  fetch("/audio/process_pipeline", {
    method: "POST",
    body: formData
  })
    .then(response => {
      if (!response.ok) {
        return response.json().then(data => {
          throw new Error(data.error || "Server error");
        });
      }
      return response.json();
    })
    .then(data => {
      // Process successful response
      processSuccessResponse(data, sortedSteps);
    })
    .catch(error => {
      // Handle error
      showStatusMessage(`Error: ${error.message}`, "error");
    })
    .finally(() => {
      // Hide spinner
      hideSpinner();
      
      // Re-enable run button
      if (runButton) {
        runButton.disabled = false;
        runButton.classList.remove("disabled-button");
      }
    });
}

/**
 * Processes successful response from the server
 * @param {Object} data - The response data
 * @param {string[]} steps - The steps that were processed
 */
function processSuccessResponse(data, steps) {
  // Show success message
  showStatusMessage(`Processing complete! ${steps.length} functions applied.`, "success");
  
  // Process each result based on the steps
  steps.forEach(step => {
    const option = aiOptions.find(opt => opt.id === step);
    if (!option) return;
    
    // Show the result container
    const resultContainer = document.getElementById(option.resultContainer);
    if (resultContainer) {
      resultContainer.style.display = "block";
      resultContainer.classList.add("visible");
    }
    
    // Process specific result types
    switch (step) {
      case "transcribe":
        updateTranscriptionResult(data.transcript || "No transcript generated");
        break;
        
      case "cleanTranscript":
        updateCleanTranscriptResult(data.clean_transcript || data.transcript || "No clean transcript generated");
        break;
        
      case "enhanceAudio":
        updateEnhancedAudioResult(data.final_audio_url);
        break;
        
      case "aiCut":
        updateAICutResult(data.cuts || []);
        break;
        
      case "generateShowNotes":
        updateShowNotesResult(data.show_notes || "No show notes generated");
        break;
        
      case "aiSuggestions":
        updateAISuggestionsResult(data.ai_suggestions || "No AI suggestions generated");
        break;
        
      case "generateQuotes":
        updateQuotesResult(data.quotes || "No quotes generated");
        break;
        
      case "planAndMixSfx":
        updateSoundEffectsResult(data.sfx_plan || [], data.sfx_clips || []);
        break;
        
      case "voice_isolation":
        // Voice isolation is handled in the final audio
        break;
    }
  });
  
  // Always update the final audio result if available
  if (data.final_audio_url) {
    updateFinalAudioResult(data.final_audio_url);
  }
}

/**
 * Updates the transcription result
 * @param {string} transcript - The transcript text
 */
function updateTranscriptionResult(transcript) {
  const container = document.getElementById("transcriptionResult");
  if (container) {
    container.textContent = transcript;
  }
}

/**
 * Updates the clean transcript result
 * @param {string} cleanTranscript - The clean transcript text
 */
function updateCleanTranscriptResult(cleanTranscript) {
  const container = document.getElementById("cleanTranscriptResult");
  if (container) {
    container.textContent = cleanTranscript;
  }
}

/**
 * Updates the enhanced audio result
 * @param {string} audioUrl - The URL of the enhanced audio
 */
function updateEnhancedAudioResult(audioUrl) {
  const container = document.getElementById("audioControls");
  if (container && audioUrl) {
    container.innerHTML = `
      <audio controls>
        <source src="${audioUrl}" type="audio/wav">
        Your browser does not support the audio element.
      </audio>
      <p>Enhanced audio is ready for playback.</p>
    `;
  }
}

/**
 * Updates the AI cut result
 * @param {Array} cuts - The array of cuts
 */
function updateAICutResult(cuts) {
  const container = document.getElementById("aiCut-result");
  if (!container) return;
  
  // Create container if it doesn't exist
  if (!document.getElementById("aiCut-result")) {
    const newContainer = document.createElement("div");
    newContainer.id = "aiCut-result";
    newContainer.className = "output-section";
    newContainer.innerHTML = `<h2>AI Cut Suggestions</h2>`;
    document.querySelector(".container").appendChild(newContainer);
  }
  
  // Update container content
  container.style.display = "block";
  
  if (cuts.length === 0) {
    container.innerHTML = `
      <h2>AI Cut Suggestions</h2>
      <p>No cuts were suggested by the AI.</p>
    `;
    return;
  }
  
  let html = `
    <h2>AI Cut Suggestions</h2>
    <p>The AI has suggested ${cuts.length} cuts:</p>
    <div id="aiSuggestedCuts">
  `;
  
  cuts.forEach((cut, index) => {
    const startTime = formatTime(cut.start);
    const endTime = formatTime(cut.end);
    const duration = formatTime(cut.end - cut.start);
    
    html += `
      <div class="cut-item" style="margin-bottom: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
            <strong>Cut ${index + 1}:</strong> ${startTime} - ${endTime} (${duration})
          </div>
          <div>
            <input type="checkbox" id="cut-${index}" class="cut-checkbox" data-start="${cut.start}" data-end="${cut.end}" checked>
            <label for="cut-${index}">Apply this cut</label>
          </div>
        </div>
        ${cut.reason ? `<div style="margin-top: 5px; color: #666;">Reason: ${cut.reason}</div>` : ''}
      </div>
    `;
  });
  
  html += `
    </div>
    <button id="apply-cuts-button" class="btn ai-edit-button" style="margin-top: 15px;">Apply Selected Cuts</button>
  `;
  
  container.innerHTML = html;
  
  // Add event listener to apply cuts button
  const applyButton = document.getElementById("apply-cuts-button");
  if (applyButton) {
    applyButton.addEventListener("click", function() {
      const selectedCuts = Array.from(document.querySelectorAll(".cut-checkbox:checked")).map(checkbox => {
        return {
          start: parseFloat(checkbox.dataset.start),
          end: parseFloat(checkbox.dataset.end)
        };
      });
      
      if (selectedCuts.length === 0) {
        showStatusMessage("Please select at least one cut to apply", "warning");
        return;
      }
      
      // Apply the cuts
      applyCuts(selectedCuts);
    });
  }
}

/**
 * Applies selected cuts to the audio
 * @param {Array} cuts - The array of cuts to apply
 */
function applyCuts(cuts) {
  if (!activeAudioBlob) {
    showStatusMessage("No audio file available", "error");
    return;
  }
  
  // Show loading state
  showStatusMessage("Applying cuts...", "info");
  showSpinner();
  
  // Create form data
  const formData = new FormData();
  formData.append("audio", activeAudioBlob);
  formData.append("episode_id", CURRENT_EPISODE_ID);
  formData.append("steps", JSON.stringify(["cut_audio"]));
  formData.append("cuts", JSON.stringify(cuts));
  
  // Send request to server
  fetch("/audio/process_pipeline", {
    method: "POST",
    body: formData
  })
    .then(response => {
      if (!response.ok) {
        return response.json().then(data => {
          throw new Error(data.error || "Server error");
        });
      }
      return response.json();
    })
    .then(data => {
      // Update the final audio
      if (data.final_audio_url) {
        updateFinalAudioResult(data.final_audio_url);
        showStatusMessage("Cuts applied successfully!", "success");
        
        // Update the active audio blob
        fetch(data.final_audio_url)
          .then(response => response.blob())
          .then(blob => {
            activeAudioBlob = new File([blob], "cut_audio.wav", { type: "audio/wav" });
            updateFileInfo(`Updated: cut_audio.wav (${formatFileSize(blob.size)})`);
          });
      } else {
        showStatusMessage("No audio was returned after applying cuts", "warning");
      }
    })
    .catch(error => {
      showStatusMessage(`Error applying cuts: ${error.message}`, "error");
    })
    .finally(() => {
      hideSpinner();
    });
}

/**
 * Updates the show notes result
 * @param {string} showNotes - The show notes text
 */
function updateShowNotesResult(showNotes) {
  const container = document.getElementById("show-notes-output");
  if (container) {
    container.textContent = showNotes;
  }
}

/**
 * Updates the AI suggestions result
 * @param {string} suggestions - The AI suggestions text
 */
function updateAISuggestionsResult(suggestions) {
  const container = document.getElementById("ai-suggestions-output");
  if (container) {
    container.textContent = suggestions;
  }
}

/**
 * Updates the quotes result
 * @param {string} quotes - The quotes text
 */
function updateQuotesResult(quotes) {
  const container = document.getElementById("quotes-output");
  if (container) {
    container.textContent = quotes;
  }
}

/**
 * Updates the sound effects result
 * @param {Array} sfxPlan - The sound effects plan
 * @param {Array} sfxClips - The sound effects clips
 */
function updateSoundEffectsResult(sfxPlan, sfxClips) {
  const container = document.getElementById("planAndMixSfx-result");
  
  // Create container if it doesn't exist
  if (!container) {
    const newContainer = document.createElement("div");
    newContainer.id = "planAndMixSfx-result";
    newContainer.className = "output-section";
    document.querySelector(".container").appendChild(newContainer);
  }
  
  // Update container content
  let html = `<h2>Sound Effects</h2>`;
  
  if (sfxPlan.length === 0) {
    html += `<p>No sound effects plan was generated.</p>`;
  } else {
    html += `
      <h3>Sound Effects Plan</h3>
      <div id="soundEffectTimeline" style="margin-bottom: 20px;">
    `;
    
    sfxPlan.forEach((item, index) => {
      html += `
        <div class="sfx-item" style="margin-bottom: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 8px;">
          <strong>${index + 1}. ${item.type || "Sound Effect"}</strong> at ${formatTime(item.timestamp)}
          <div style="margin-top: 5px; color: #666;">${item.description || ""}</div>
        </div>
      `;
    });
    
    html += `</div>`;
  }
  
  if (sfxClips.length > 0) {
    html += `
      <h3>Sound Effect Clips</h3>
      <div id="soundEffectClips">
    `;
    
    sfxClips.forEach((clip, index) => {
      html += `
        <div class="sfx-clip" style="margin-bottom: 15px;">
          <div style="margin-bottom: 5px;"><strong>${index + 1}. ${clip.name || "Sound Clip"}</strong></div>
          ${clip.url ? `
            <audio controls>
              <source src="${clip.url}" type="audio/wav">
              Your browser does not support the audio element.
            </audio>
          ` : "No audio URL provided"}
        </div>
      `;
    });
    
    html += `</div>`;
  }
  
  // Update the container
  if (container) {
    container.innerHTML = html;
    container.style.display = "block";
    container.classList.add("visible");
  }
}

/**
 * Updates the final audio result
 * @param {string} audioUrl - The URL of the final audio
 */
function updateFinalAudioResult(audioUrl) {
  const container = document.getElementById("finalAudioResult");
  
  // Create container if it doesn't exist
  if (!container) {
    const newContainer = document.createElement("div");
    newContainer.id = "finalAudioResult";
    newContainer.className = "output-section";
    document.querySelector(".container").appendChild(newContainer);
  }
  
  // Update container content
  const finalContainer = document.getElementById("finalAudioResult");
  if (finalContainer && audioUrl) {
    finalContainer.innerHTML = `
      <h2>Final Processed Audio</h2>
      <audio controls style="width: 100%;">
        <source src="${audioUrl}" type="audio/wav">
        Your browser does not support the audio element.
      </audio>
      <div style="margin-top: 10px;">
        <a href="${audioUrl}" download="processed_audio.wav" class="btn ai-edit-button">Download Audio</a>
      </div>
    `;
    finalContainer.style.display = "block";
    finalContainer.classList.add("visible");
  }
}

/**
 * Shows a status message
 * @param {string} message - The message to show
 * @param {string} type - The type of message (info, success, warning, error)
 */
function showStatusMessage(message, type = "info") {
  const statusMessage = document.getElementById("status-message");
  if (!statusMessage) return;
  
  // Clear existing classes
  statusMessage.className = "status-message";
  
  // Add type-specific class
  statusMessage.classList.add(`status-${type}`);
  
  // Set message
  statusMessage.textContent = message;
  
  // Show message
  statusMessage.style.display = "block";
}

/**
 * Hides the status message
 */
function hideStatusMessage() {
  const statusMessage = document.getElementById("status-message");
  if (statusMessage) {
    statusMessage.style.display = "none";
  }
}

/**
 * Shows the loading spinner
 */
function showSpinner() {
  // Check if spinner already exists
  if (document.querySelector(".spinner")) return;
  
  // Create spinner
  const spinner = document.createElement("div");
  spinner.className = "spinner";
  
  // Add spinner to status message
  const statusMessage = document.getElementById("status-message");
  if (statusMessage) {
    statusMessage.appendChild(spinner);
  }
}

/**
 * Hides the loading spinner
 */
function hideSpinner() {
  const spinner = document.querySelector(".spinner");
  if (spinner) {
    spinner.remove();
  }
}

/**
 * Hides all result containers
 */
function hideAllResults() {
  // Hide all output sections
  const outputSections = document.querySelectorAll(".output-section");
  outputSections.forEach(section => {
    section.style.display = "none";
    section.classList.remove("visible");
  });
}

/**
 * Formats time in seconds to MM:SS format
 * @param {number} seconds - The time in seconds
 * @returns {string} - Formatted time
 */
function formatTime(seconds) {
  if (isNaN(seconds)) return "00:00";
  
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

// Export functions for testing
if (typeof module !== "undefined") {
  module.exports = {
    formatTime,
    formatFileSize,
    sortFunctionsByDependencies,
    checkDependenciesMet
  };
}