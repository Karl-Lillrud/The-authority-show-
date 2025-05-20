"use strict";

// Lista över AI-funktioner och deras info
const aiOptions = [
  { id: 'transcribe', title: 'Transcribe', description: 'Convert audio to text using AI transcription', icon: 'T' },
  { id: 'enhanceAudio', title: 'Enhance Audio', description: 'Improve audio quality and reduce background noise', icon: 'A' },
  { id: 'isolateVoice', title: 'Isolate Voice', description: 'Separate voice from background sounds', icon: 'V' },
  { id: 'cleanTranscript', title: 'Clean Transcript', description: 'Remove filler words and improve readability', icon: 'C' },
  { id: 'generateShowNotes', title: 'Generate Show Notes', description: 'Create detailed notes from your content', icon: 'N' },
  { id: 'aiSuggestions', title: 'AI Suggestions', description: 'Get content improvement recommendations', icon: 'S' },
  { id: 'generateQuotes', title: 'Generate Quotes', description: 'Extract quotable moments from your content', icon: 'Q' },
  { id: 'osintLookup', title: 'OSINT Lookup', description: 'Research additional information from open sources', icon: 'O' }
];

// Rendera options
const optionList = document.getElementById('option-list');
aiOptions.forEach(option => {
  const item = document.createElement('div');
  item.className = 'option-item';
  item.innerHTML = `
    <div class="option-icon">${option.icon}</div>
    <div class="option-content">
      <div class="option-title">${option.title}</div>
      <div class="option-description">${option.description}</div>
    </div>
    <input type="checkbox" class="option-checkbox" id="${option.id}" data-function="${option.id}">
  `;
  optionList.appendChild(item);

  // Klick på hela boxen togglar checkboxen
  item.addEventListener('click', e => {
    if (e.target.type !== 'checkbox') {
      const checkbox = item.querySelector('.option-checkbox');
      checkbox.checked = !checkbox.checked;
    }
  });
});

// Run-knapp
document.getElementById('run-button').addEventListener('click', () => {
  const selected = [];
  document.querySelectorAll('.option-checkbox:checked').forEach(cb => {
    selected.push(cb.dataset.function);
  });

  if (selected.length === 0) {
    showStatus("Please select at least one editing option", 'error');
    return;
  }

  runSelectedFunctions(selected);
});

// Kör funktionerna
function runSelectedFunctions(functionNames) {
  showStatus(`Running: ${functionNames.join(', ')}`, 'info');
  functionNames.forEach(fn => {
    if (typeof window[fn] === 'function') {
      try {
        window[fn]();
        console.log(`✔️ Ran ${fn}()`);
      } catch (e) {
        console.error(`❌ Failed to run ${fn}()`, e);
      }
    } else {
      console.warn(`⚠️ ${fn}() is not defined`);
    }
  });
}

// Statusmeddelande
function showStatus(msg, type = 'info') {
  const el = document.getElementById('status-message');
  el.textContent = msg;
  el.style.display = 'block';
  el.style.backgroundColor = type === 'error' ? '#fff5f5' : '#f0f7ff';
  el.style.color = type === 'error' ? '#c53030' : '#2c5282';
  setTimeout(() => { el.style.display = 'none'; }, 5000);
}

// 👇 Exponera funktionerna i global scope
window.transcribe = () => alert("Running transcribe()");
window.enhanceAudio = () => alert("Running enhanceAudio()");
window.isolateVoice = () => alert("Running isolateVoice()");
window.cleanTranscript = () => alert("Running cleanTranscript()");
window.generateShowNotes = () => alert("Running generateShowNotes()");
window.aiSuggestions = () => alert("Running aiSuggestions()");
window.generateQuotes = () => alert("Running generateQuotes()");
window.osintLookup = () => alert("Running osintLookup()");
