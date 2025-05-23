import { publishEpisode, getSasUrl } from "/static/requests/publishRequests.js"; // Import getSasUrl
import { fetchEpisode } from "/static/requests/episodeRequest.js"; // For episode preview
import { showNotification } from "/static/js/components/notifications.js";
import { fetchPodcasts } from "/static/requests/podcastRequests.js"; // For podcast dropdown
import { fetchEpisodesByPodcast } from "/static/requests/episodeRequest.js"; // For episode dropdown

console.log("[publish.js] Script loaded and running!");

document.addEventListener("DOMContentLoaded", () => {
  console.log("[publish.js] DOMContentLoaded event fired");

  const podcastSelect = document.getElementById("podcast-select");
  const episodeSelect = document.getElementById("episode-select");
  const episodeDetailsPreview = document.getElementById("episode-details-preview");
  const previewTitle = document.getElementById("preview-title");
  const previewDescription = document.getElementById("preview-description");
  const previewImage = document.getElementById("preview-image");
  const previewAudio = document.getElementById("preview-audio");
  const publishNowBtn = document.getElementById("publish-now-btn");
  const publishStatusDiv = document.getElementById("publish-status");
  const publishLogPre = document.getElementById("publish-log");
  const platformToggles = document.querySelectorAll('.platform-toggle input[type="checkbox"]');
  // const publishNotes = document.getElementById("publish-notes"); // Removed

  // Load podcasts into the dropdown
  async function loadPodcasts() {
    console.log("[publish.js] loadPodcasts() function called.");
    try {
      podcastSelect.innerHTML = '<option value="">Loading podcasts...</option>';
      podcastSelect.disabled = true;
      console.log("[publish.js] Fetching podcasts via fetchPodcasts()...");
      const podcastData = await fetchPodcasts(); // Uses /get_podcasts
      console.log("[publish.js] fetchPodcasts() raw response:", JSON.stringify(podcastData, null, 2));

      if (!podcastData) {
        podcastSelect.innerHTML = '<option value="">No response from server</option>';
        podcastSelect.disabled = true;
        episodeSelect.disabled = true;
        showNotification("Error", "No response from server when fetching podcasts.", "error");
        console.error("[publish.js] No response from fetchPodcasts() - podcastData is falsy.");
        return;
      }

      if (podcastData.error) {
        podcastSelect.innerHTML = `<option value="">Error: ${podcastData.error}</option>`;
        podcastSelect.disabled = true;
        episodeSelect.disabled = true;
        showNotification("Error", `Error fetching podcasts: ${podcastData.error}`, "error");
        console.error("[publish.js] Error in podcastData from server:", podcastData.error);
        return;
      }

      const podcasts = Array.isArray(podcastData.podcast)
        ? podcastData.podcast
        : (Array.isArray(podcastData.podcasts) ? podcastData.podcasts : null);
        
      console.log("[publish.js] Extracted podcasts array:", JSON.stringify(podcasts, null, 2));

      podcastSelect.innerHTML = ''; 
      podcastSelect.disabled = false;

      if (!podcasts || podcasts.length === 0) {
        podcastSelect.innerHTML = '<option value="">No podcasts found</option>';
        episodeSelect.innerHTML = '<option value="">Select a podcast first...</option>';
        episodeSelect.disabled = true;
        showNotification("Info", "No podcasts found in your account.", "info");
        console.warn("[publish.js] No podcasts in array or array is null/empty. Full response:", JSON.stringify(podcastData, null, 2));
        return;
      }

      podcastSelect.innerHTML = '<option value="">-- Select a Podcast --</option>';
      console.log(`[publish.js] Populating podcast dropdown. Number of podcasts: ${podcasts.length}`);
      podcasts.forEach((podcast, index) => {
        console.log(`[publish.js] Processing podcast at index ${index}:`, JSON.stringify(podcast, null, 2));
        if (podcast && podcast._id && podcast.podName && typeof podcast.podName === 'string' && podcast.podName.trim() !== '') {
          console.log(`[publish.js] Adding podcast option: ID=${podcast._id}, Name=${podcast.podName}`);
          const option = document.createElement("option");
          option.value = podcast._id;
          option.textContent = podcast.podName;
          podcastSelect.appendChild(option);
        } else {
          console.warn(
            `[publish.js] Skipping invalid podcast object at index ${index}.`,
            `ID: ${podcast ? podcast._id : 'N/A'},`,
            `Name: ${podcast ? podcast.podName : 'N/A'} (Type: ${podcast ? typeof podcast.podName : 'N/A'}),`,
            "Full object:", JSON.stringify(podcast, null, 2)
          );
        }
      });

      // Preselect the podcast if only one is available
      if (podcasts.length === 1) {
        podcastSelect.value = podcasts[0]._id;
        console.log(`[publish.js] Only one podcast found. Preselecting podcast ID: ${podcasts[0]._id}`);
        loadEpisodesForPodcast(podcasts[0]._id); // Automatically load episodes for the preselected podcast
      }

      console.log("[publish.js] Finished populating podcast dropdown.");
    } catch (error) {
      podcastSelect.innerHTML = '<option value="">Error loading podcasts</option>';
      podcastSelect.disabled = true;
      episodeSelect.innerHTML = '<option value="">Select a podcast first...</option>';
      episodeSelect.disabled = true;
      showNotification("Error", "Error loading podcasts. Please try again.", "error");
      console.error("[publish.js] CRITICAL EXCEPTION in loadPodcasts:", error);
    }
  }

  // Load episodes for the selected podcast
  async function loadEpisodesForPodcast(podcastId) {
    console.log(`[publish.js] loadEpisodesForPodcast called with podcastId: ${podcastId}`);
    const episodeSelectElement = document.getElementById("episode-select");

    episodeSelectElement.innerHTML = '<option value="">Loading episodes...</option>';
    episodeSelectElement.disabled = true;
    episodeDetailsPreview.classList.add("hidden");

    if (!podcastId) {
      episodeSelectElement.innerHTML = '<option value="">Select a podcast first...</option>';
      return;
    }

    try {
      console.log(`[publish.js] Fetching episodes for podcast ID ${podcastId} via fetchEpisodesByPodcast()...`);
      const episodesData = await fetchEpisodesByPodcast(podcastId);
      const episodes = Array.isArray(episodesData) ? episodesData : (episodesData && Array.isArray(episodesData.episodes) ? episodesData.episodes : []);

      console.log(`[publish.js] fetchEpisodesByPodcast() raw response for podcast ${podcastId}:`, JSON.stringify(episodes, null, 2));

      episodeSelectElement.innerHTML = ''; // Clear previous options
      episodeSelectElement.disabled = false;

      if (episodes && episodes.length > 0) {
        // Filter out episodes with status "published"
        const unpublishedEpisodes = episodes.filter(episode => episode.status?.toLowerCase() !== "published");

        if (unpublishedEpisodes.length > 0) {
          episodeSelectElement.innerHTML = '<option value="">-- Select an Episode --</option>';
          unpublishedEpisodes.forEach(episode => {
            if (episode && episode._id && episode.title) {
              console.log(`[publish.js] Adding episode option: ID=${episode._id}, Title=${episode.title}, Status=${episode.status}`);
              const option = document.createElement("option");
              option.value = episode._id;
              option.textContent = `${episode.title} (${episode.status || "Unpublished"})`;
              episodeSelectElement.appendChild(option);
            } else {
              console.warn("[publish.js] Skipping invalid episode object:", JSON.stringify(episode, null, 2));
            }
          });
        } else {
          episodeSelectElement.innerHTML = '<option value="">No unpublished episodes found for this podcast</option>';
          episodeSelectElement.disabled = true;
          console.log(`[publish.js] No unpublished episodes found for podcast ${podcastId}.`);
        }
      } else {
        episodeSelectElement.innerHTML = '<option value="">No episodes found for this podcast</option>';
        episodeSelectElement.disabled = true;
        console.log(`[publish.js] No episodes found for podcast ${podcastId}.`);
      }
    } catch (error) {
      console.error(`[publish.js] Error loading episodes for podcast ${podcastId}:`, error);
      episodeSelectElement.innerHTML = '<option value="">Error loading episodes</option>';
      episodeSelectElement.disabled = true;
      showNotification("Error", "Error loading episodes for the selected podcast.", "error");
    }
  }

  // Load episode preview
  async function loadEpisodePreview(episodeId) {
    if (!episodeId) {
      episodeDetailsPreview.classList.add("hidden");
      return;
    }
    console.log(`[publish.js] Loading preview for episode ID: ${episodeId}`);
    try {
      const episode = await fetchEpisode(episodeId); // Uses /get_episodes/<episode_id>
      if (episode && !episode.error) { // Check for backend error structure
        previewTitle.textContent = episode.title || "No title";
        previewDescription.textContent = episode.description || "No description available.";

        if (episode.imageUrl) { // Assuming 'imageUrl' from episode schema
          previewImage.src = episode.imageUrl;
          previewImage.classList.remove("hidden");
        } else {
          previewImage.classList.add("hidden");
        }

        if (episode.audioUrl) { // Assuming 'audioUrl' from episode schema
          previewAudio.src = episode.audioUrl;
          previewAudio.classList.remove("hidden");
        } else {
          previewAudio.classList.add("hidden");
        }
        episodeDetailsPreview.classList.remove("hidden");
      } else {
        episodeDetailsPreview.classList.add("hidden");
        const errorMsg = episode ? episode.error : "Episode data not found.";
        addToLog(`Could not load preview for episode ID: ${episodeId}. Reason: ${errorMsg}`);
        showNotification("Error", `Could not load preview: ${errorMsg}`, "error");
        console.error(`[publish.js] Error loading episode preview for ${episodeId}:`, errorMsg);
      }
    } catch (error) {
      console.error(`[publish.js] Exception loading episode preview for ${episodeId}:`, error);
      episodeDetailsPreview.classList.add("hidden");
      addToLog(`Error loading preview for episode ID: ${episodeId}.`);
      showNotification("Error", "Error loading episode preview.", "error");
    }
  }

  function addToLog(message) {
    publishStatusDiv.classList.remove("hidden");
    const timestamp = new Date().toLocaleTimeString();
    publishLogPre.textContent += `[${timestamp}] ${message}\n`;
    publishLogPre.scrollTop = publishLogPre.scrollHeight; // Auto-scroll
  }

  podcastSelect.addEventListener("change", (event) => {
    const podcastId = event.target.value;
    console.log(`[publish.js] Podcast selection changed. Selected podcastId: ${podcastId}`);
    // The loadEpisodesForPodcast function already uses the correct episode select ID internally
    loadEpisodesForPodcast(podcastId); 
    episodeSelect.value = ""; // Reset episode selection
    episodeDetailsPreview.classList.add("hidden"); // Hide preview
  });

  episodeSelect.addEventListener("change", (event) => {
    const episodeId = event.target.value;
    console.log(`[publish.js] Episode selection changed. Selected episodeId: ${episodeId}`);
    loadEpisodePreview(episodeId);
  });

  // Helper: Check for missing required RSS fields for selected platforms
  function getMissingRequiredFields(podcast, episode, selectedPlatforms) {
    // Always required for all platforms:
    const requiredPodcastFields = [
      { key: "podName", label: "Podcast Title" },
      { key: "description", label: "Podcast Description" },
      { key: "logoUrl", label: "Podcast Artwork (logoUrl)" },
      { key: "ownerName", label: "Podcast Owner Name" },
      { key: "email", label: "Podcast Owner Email" },
      { key: "language", label: "Podcast Language" },
      { key: "author", label: "Podcast Author" }
    ];
    const requiredEpisodeFields = [
      { key: "title", label: "Episode Title" },
      { key: "description", label: "Episode Description" },
      { key: "audioUrl", label: "Episode Audio URL" },
      { key: "pubDate", label: "Episode Publish Date" }, // May be publishDate
      { key: "explicit", label: "Explicit (yes/no)" }
    ];

    // Optional but recommended tags for best compatibility
    const recommendedPodcastFields = [
      { key: "itunes_keywords", label: "Podcast Keywords (itunes:keywords)" },
      { key: "itunes_block", label: "Podcast Block (itunes:block)" },
      { key: "googleplay_author", label: "Google Play Author" },
      { key: "googleplay_email", label: "Google Play Email" },
      { key: "googleplay_image", label: "Google Play Image" },
      { key: "spotify_locked", label: "Spotify Locked" }
    ];
    const recommendedEpisodeFields = [
      { key: "itunes_keywords", label: "Episode Keywords (itunes:keywords)" },
      { key: "itunes_title", label: "Episode iTunes Title" },
      { key: "itunes_block", label: "Episode Block (itunes:block)" },
      { key: "googleplay_author", label: "Google Play Author" },
      { key: "googleplay_email", label: "Google Play Email" },
      { key: "googleplay_image", label: "Google Play Image" },
      { key: "spotify_locked", label: "Spotify Locked" }
    ];

    let missing = [];
    let recommended = [];

    requiredPodcastFields.forEach(f => {
      if (!podcast || !podcast[f.key] || podcast[f.key].toString().trim() === "") {
        missing.push({ type: "podcast", ...f });
      }
    });
    requiredEpisodeFields.forEach(f => {
      let val = episode ? (f.key === "pubDate" ? (episode.publishDate || episode.pubDate) : episode[f.key]) : null;
      if (!val || val.toString().trim() === "") {
        missing.push({ type: "episode", ...f });
      }
    });

    // Check recommended fields (not required)
    recommendedPodcastFields.forEach(f => {
      if (!podcast || !podcast[f.key] || podcast[f.key].toString().trim() === "") {
        recommended.push({ type: "podcast", ...f });
      }
    });
    recommendedEpisodeFields.forEach(f => {
      if (!episode || !episode[f.key] || episode[f.key].toString().trim() === "") {
        recommended.push({ type: "episode", ...f });
      }
    });

    // Return both lists
    return { missing, recommended };
  }

  // Helper: Show modal to fill missing fields (required and recommended)
  function showMissingFieldsModal(missingFieldsObj, podcast, episode, onSave) {
    const { missing, recommended } = missingFieldsObj;
    // Remove any existing modal
    let existingModal = document.getElementById("missing-fields-modal");
    if (existingModal) existingModal.remove();

    const modal = document.createElement("div");
    modal.id = "missing-fields-modal";
    modal.style.position = "fixed";
    modal.style.top = "0";
    modal.style.left = "0";
    modal.style.width = "100vw";
    modal.style.height = "100vh";
    modal.style.background = "rgba(0,0,0,0.7)";
    modal.style.zIndex = "9999";
    modal.style.display = "flex";
    modal.style.alignItems = "center";
    modal.style.justifyContent = "center";

    const formBox = document.createElement("div");
    formBox.style.background = "#fff";
    formBox.style.padding = "2rem";
    formBox.style.borderRadius = "8px";
    formBox.style.maxWidth = "400px";
    formBox.style.width = "100%";
    // Make the list scrollable and smaller
    formBox.style.maxHeight = "70vh";
    formBox.style.overflowY = "auto";

    // Helper to clean label text (remove (podcast), (episode), and (itunes:block) etc.)
    function cleanLabel(label) {
      // Remove anything in parentheses, including the parentheses and any whitespace before them
      return label.replace(/\s*\([^)]+\)/g, "").trim();
    }

    formBox.innerHTML = `<h2>Required Details</h2>
      <form id="missing-fields-form">
        <div style="max-height: 45vh; overflow-y: auto;">
        ${missing.map(f => {
          let inputField = "";
          if (f.type === "episode" && f.key === "pubDate") {
            const now = new Date();
            const timezoneOffset = now.getTimezoneOffset() * 60000;
            const localISOTime = (new Date(now - timezoneOffset)).toISOString().slice(0, 16);
            inputField = `<input type="datetime-local" name="${f.type}_${f.key}" value="${localISOTime}" required />`;
          } else if (f.key === "explicit") {
            inputField = `
              <div style="display: flex; gap: 1rem;">
                <label><input type="radio" name="${f.type}_${f.key}" value="yes" required /> Yes</label>
                <label><input type="radio" name="${f.type}_${f.key}" value="no" required /> No</label>
              </div>
            `;
          } else if (f.key === "logoUrl" && f.type === "podcast") { // Handle podcast artwork
            inputField = `<input type="file" name="${f.type}_${f.key}" accept="image/*" required />`;
          } else {
            inputField = `<input type="text" name="${f.type}_${f.key}" required />`;
          }
          return `
          <div class="field-group">
            <label>${cleanLabel(f.label)} <span style="color:orange;font-size:0.9em;">(Required)</span></label>
            ${inputField}
          </div>
        `}).join("")}
        ${recommended.length > 0 ? `<h3 style="margin-top:2rem;">Recommended (Optional)</h3>` : ""}
        ${recommended.map(f => {
          let inputField = `<input type="text" name="${f.type}_${f.key}" />`;
          // Note: If logoUrl could be recommended, this would need similar file input logic.
          // Currently, logoUrl is only in the 'required' list.
          return `
          <div class="field-group">
            <label>${cleanLabel(f.label)} <span style="color:#888;font-size:0.9em;">(Optional)</span></label>
            ${inputField}
          </div>
        `}).join("")}
        </div>
        <div style="margin-top:1rem;display:flex;gap:1rem;">
          <button type="submit" class="save-btn">Save & Continue</button>
          <button type="button" id="cancel-missing-fields" class="cancel-btn">Cancel</button>
        </div>
      </form>
    `;
    modal.appendChild(formBox);
    document.body.appendChild(modal);

    document.getElementById("cancel-missing-fields").onclick = () => {
      document.body.removeChild(modal);
    };

    formBox.querySelector("#missing-fields-form").onsubmit = async (e) => { // Make async
      e.preventDefault();
      const submitButton = formBox.querySelector('button[type="submit"]');
      submitButton.disabled = true;
      submitButton.textContent = "Saving...";

      try {
        for (const f of [...missing, ...recommended]) { // Use for...of for async/await
          const inputElement = formBox.querySelector(`[name='${f.type}_${f.key}']:checked`) ||
                               formBox.querySelector(`[name='${f.type}_${f.key}']`);
          if (!inputElement) continue;

          if (f.key === "logoUrl" && f.type === "podcast" && inputElement.type === "file") {
            if (inputElement.files && inputElement.files[0]) {
              const imageFile = inputElement.files[0];
              try {
                addToLog(`Uploading podcast artwork: ${imageFile.name}`);
                const { uploadUrl, blobUrl } = await getSasUrl(imageFile.name, imageFile.type);
                
                const headers = {
                  'x-ms-blob-type': 'BlockBlob',
                  'Content-Type': imageFile.type
                  // Note: If you encounter CORS issues here, ensure your Azure Blob Storage account
                  // has CORS rules configured to allow PUT requests from this origin (e.g., http://127.0.0.1:8000)
                  // and allows the 'x-ms-blob-type' and 'Content-Type' headers.
                };

                await fetch(uploadUrl, {
                  method: 'PUT',
                  body: imageFile,
                  headers: headers
                });
                podcast.logoUrl = blobUrl; // Update the podcast object
                addToLog(`Podcast artwork uploaded: ${blobUrl}`);
                showNotification("Success", "Podcast artwork uploaded successfully.", "success");
              } catch (uploadError) {
                console.error("Error uploading podcast artwork:", uploadError);
                addToLog(`Error uploading podcast artwork: ${uploadError.message}`);
                showNotification("Error", `Failed to upload podcast artwork: ${uploadError.message}`, "error");
                // Optionally, re-enable button and return if upload is critical
                // submitButton.disabled = false;
                // submitButton.textContent = "Save & Continue";
                // return; 
              }
            }
          } else {
            let val = inputElement.value.trim();
            if (f.type === "episode" && f.key === "pubDate" && inputElement.type === "datetime-local") {
              val = new Date(val).toISOString();
            }
            if (f.type === "podcast") podcast[f.key] = val;
            else if (f.type === "episode") {
              if (f.key === "pubDate") episode.publishDate = val;
              else episode[f.key] = val;
            }
          }
        }
        document.body.removeChild(modal);
        onSave(); // Call the original onSave callback
      } catch (error) {
        console.error("Error processing missing fields form:", error);
        addToLog(`Error saving missing fields: ${error.message}`);
        showNotification("Error", "An error occurred while saving details.", "error");
        submitButton.disabled = false; // Re-enable button on error
        submitButton.textContent = "Save & Continue";
      }
    };
  }

  function showRssFeedPopup(rssFeedUrl) {
    // Remove any existing modal
    let existingModal = document.getElementById("rss-feed-popup");
    if (existingModal) existingModal.remove();

    const modal = document.createElement("div");
    modal.id = "rss-feed-popup";
    modal.className = "popup rss-feed-popup"; // Add a class for specific styling
    modal.style.position = "fixed";
    modal.style.top = "0";
    modal.style.left = "0";
    modal.style.width = "100vw";
    modal.style.height = "100vh";
    modal.style.background = "rgba(0,0,0,0.7)";
    modal.style.zIndex = "10000"; // Ensure it's on top
    modal.style.display = "flex";
    modal.style.alignItems = "center";
    modal.style.justifyContent = "center";

    const popupContent = document.createElement("div");
    popupContent.className = "form-box"; // Use existing form-box styling or create new
    popupContent.style.maxWidth = "600px";
    popupContent.style.width = "90%";
    
    popupContent.innerHTML = `
      <span class="close-btn" id="close-rss-popup" style="float:right; cursor:pointer; font-size: 1.5rem;">&times;</span>
      <h2>Your Podcast RSS Feed is Ready!</h2>
      <p>Your episode has been published and your RSS feed has been updated. You can copy the URL below to submit it to podcast directories that require manual submission or to check your feed.</p>
      
      <div class="field-group">
        <label for="rss-feed-url-display">RSS Feed URL:</label>
        <input type="text" id="rss-feed-url-display" value="${rssFeedUrl}" readonly style="width: calc(100% - 16px); padding: 8px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px;">
        <button id="copy-rss-url-btn" class="action-btn" style="padding: 8px 12px; margin-left: 5px;">Copy URL</button>
      </div>

      <h3>Submit to Directories:</h3>
      <ul style="list-style: none; padding-left: 0;">
        <li style="margin-bottom: 8px;"><a href="https://podcasters.spotify.com/" target="_blank" rel="noopener noreferrer">Spotify for Podcasters</a> (Usually polls automatically, but you can check status)</li>
        <li style="margin-bottom: 8px;"><a href="https://podcastsconnect.apple.com/" target="_blank" rel="noopener noreferrer">Apple Podcasts Connect</a></li>
        <li style="margin-bottom: 8px;"><a href="https://podcastsmanager.google.com/" target="_blank" rel="noopener noreferrer">Google Podcasts Manager</a></li>
        <li style="margin-bottom: 8px;"><a href="https://podcasters.amazon.com/podcasts" target="_blank" rel="noopener noreferrer">Amazon Music for Podcasters</a></li>
        <li style="margin-bottom: 8px;"><a href="https://www.pocketcasts.com/submit/" target="_blank" rel="noopener noreferrer">Pocket Casts</a></li>
        <li style="margin-bottom: 8px;"><a href="https://castbox.fm/creator/" target="_blank" rel="noopener noreferrer">Castbox Creator Studio</a></li>
        <li style="margin-bottom: 8px;"><a href="https://podcastaddict.com/submit" target="_blank" rel="noopener noreferrer">Podcast Addict</a></li>
        <!-- Add more platform links as needed -->
      </ul>
      <div class="form-actions" style="text-align: right; margin-top: 20px;">
        <button id="close-rss-feed-popup-btn" class="save-btn">Close</button>
      </div>
    `;
    modal.appendChild(popupContent);
    document.body.appendChild(modal);

    const closePopup = () => document.body.removeChild(modal);
    document.getElementById("close-rss-popup").onclick = closePopup;
    document.getElementById("close-rss-feed-popup-btn").onclick = closePopup;
    
    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            closePopup();
        }
    });

    document.getElementById("copy-rss-url-btn").onclick = () => {
        const urlInput = document.getElementById("rss-feed-url-display");
        urlInput.select();
        urlInput.setSelectionRange(0, 99999); // For mobile devices
        try {
            document.execCommand("copy");
            showNotification("Success", "RSS Feed URL copied to clipboard!", "success");
        } catch (err) {
            showNotification("Error", "Failed to copy URL. Please copy manually.", "error");
            console.error('Failed to copy text: ', err);
        }
    };
  }


  publishNowBtn.addEventListener("click", async () => {
    const episodeId = episodeSelect.value;
    const selectedPlatforms = [];
    platformToggles.forEach((toggle) => {
      if (toggle.checked) {
        selectedPlatforms.push(toggle.dataset.platform);
      }
    });

    if (!episodeId) {
      showNotification("Error", "Please select an episode to publish.", "error");
      addToLog("Publishing failed: No episode selected.");
      return;
    }
    if (selectedPlatforms.length === 0) {
      showNotification("Error", "Please select at least one platform to publish to.", "error");
      addToLog("Publishing failed: No platforms selected.");
      return;
    }

    // Fetch selected podcast and episode objects for validation
    // Ensure _publishPodcastsCache is populated before this.
    const podcast = (window._publishPodcastsCache || []).find(p => p._id === podcastSelect.value);
    let episode = null;
    if (episodeId) { // Only fetch if an episode is selected
        try {
          // Use the globally available episode object if it matches, otherwise fetch
          if (window._currentEpisodePreview && window._currentEpisodePreview._id === episodeId) {
            episode = window._currentEpisodePreview;
          } else {
            episode = await fetchEpisode(episodeId);
            window._currentEpisodePreview = episode; // Cache it
          }
        } catch (e) {
            addToLog(`Error fetching episode details for validation: ${e.message}`);
            showNotification("Error", "Could not retrieve episode details for validation.", "error");
            return;
        }
    }


    // Check for missing required and recommended fields
    const missingFieldsObj = getMissingRequiredFields(podcast, episode, selectedPlatforms);
    
    if (missingFieldsObj.missing.length > 0 || missingFieldsObj.recommended.length > 0) {
      showMissingFieldsModal(missingFieldsObj, podcast, episode, () => {
        // This callback is executed after the modal saves and closes.
        // The 'podcast' and 'episode' objects are updated by the modal itself.
        // We do NOT call doPublish() here.
        // The user must click "Publish Now" again.
        
        // Re-enable the publish button if it was disabled during modal interaction.
        publishNowBtn.disabled = false; 
        publishNowBtn.textContent = "Publish Now";
        addToLog("Missing fields have been updated. Please click 'Publish Now' again to proceed.");
        showNotification("Info", "Details updated. Click 'Publish Now' again to publish.", "info");
        
        // If the episode was updated (e.g., publishDate), refresh its preview
        if (episodeId && episode) { // episode object should be updated by reference
            loadEpisodePreview(episodeId); // Reload preview with potentially new data
        }
      });
      return; // Stop further execution for this click, user needs to click "Publish Now" again
    }

    // If we reach here, it means either:
    // 1. There were no missing fields initially.
    // 2. The modal was shown, user saved, and this is a *new* click on "Publish Now" 
    //    and the missing fields check passed this time.
    await doPublish();

    async function doPublish() {
      publishNowBtn.disabled = true;
      publishNowBtn.textContent = "Publishing...";
      addToLog(`Starting publishing process for episode ID: ${episodeId}`);
      addToLog(`Selected platforms: ${selectedPlatforms.join(", ")}`);

      try {
        const result = await publishEpisode(episodeId, selectedPlatforms, null); // Notes field removed
        if (result.success) {
          addToLog(`Successfully published episode: ${result.message}`);
          showNotification("Success", `Episode published successfully! ${result.message || ''}`, "success");
          episodeDetailsPreview.classList.add("hidden");
          // Reset episode selection and reload episodes for the current podcast
          const currentPodcastId = podcastSelect.value;
          episodeSelect.value = ""; 
          if (currentPodcastId) {
              loadEpisodesForPodcast(currentPodcastId); // Reload to remove published episode
          }
          
          if (result.rssFeedUrl) {
            showRssFeedPopup(result.rssFeedUrl);
          }
        } else {
          addToLog(`Publishing failed: ${result.error || "Unknown error"}`);
          showNotification("Error", `Failed to publish episode. ${result.error || "Unknown error"}`, "error");
        }
      } catch (error) {
        console.error("[publish.js] Error publishing episode:", error);
        addToLog(`Critical error during publishing: ${error.message}`);
        showNotification("Error", `An error occurred during publishing: ${error.message}`, "error");
      } finally {
        publishNowBtn.disabled = false;
        publishNowBtn.textContent = "Publish Now";
      }
    }
  });

  // Initial load
  loadPodcasts();

  // Cache podcasts for validation
  async function cachePodcasts() {
    try {
        const podcastData = await fetchPodcasts();
        // Ensure the structure is { podcast: [...] } or { podcasts: [...] }
        window._publishPodcastsCache = Array.isArray(podcastData.podcast)
          ? podcastData.podcast
          : (podcastData.podcasts && Array.isArray(podcastData.podcasts) ? podcastData.podcasts : []);
        if (!window._publishPodcastsCache || window._publishPodcastsCache.length === 0) {
            console.warn("[publish.js] Podcast cache is empty after fetching.");
        }
    } catch (error) {
        console.error("[publish.js] Failed to cache podcasts:", error);
        window._publishPodcastsCache = [];
    }
  }
  cachePodcasts(); // Call it to ensure cache is populated on page load
});
