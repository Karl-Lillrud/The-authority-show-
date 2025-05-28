import { publishEpisode } from "/static/requests/publishRequests.js";
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

  // Log the raw data received from the template
  console.log('[Publish Page] Raw window.publishPageData:', JSON.stringify(window.publishPageData, null, 2));

  const { podcasts, singlePodcastId } = window.publishPageData || { podcasts: [], singlePodcastId: null };

  // Log parsed data
  console.log('[Publish Page] Parsed podcasts:', JSON.stringify(podcasts, null, 2));
  console.log('[Publish Page] Parsed singlePodcastId:', singlePodcastId, '(type:', typeof singlePodcastId, ')');

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
      let preSelected = false;
      podcasts.forEach((podcast, index) => {
        console.log(`[publish.js] Processing podcast at index ${index}:`, JSON.stringify(podcast, null, 2));
        if (podcast && podcast._id && podcast.podName && typeof podcast.podName === 'string' && podcast.podName.trim() !== '') {
          console.log(`[publish.js] Adding podcast option: ID=${podcast._id}, Name=${podcast.podName}`);
          const option = document.createElement("option");
          option.value = podcast._id;
          option.textContent = podcast.podName;
          podcastSelect.appendChild(option);

          // Pre-select the podcast if it matches singlePodcastId
          if (singlePodcastId && podcast._id === singlePodcastId) {
            console.log(`[publish.js] Match found! Pre-selecting podcast: ID="${podcast._id}", Name="${option.textContent}"`);
            option.selected = true;
            preSelected = true;
          }
        } else {
          console.warn(
            `[publish.js] Skipping invalid podcast object at index ${index}.`,
            `ID: ${podcast ? podcast._id : 'N/A'},`,
            `Name: ${podcast ? podcast.podName : 'N/A'} (Type: ${podcast ? typeof podcast.podName : 'N/A'}),`,
            "Full object:", JSON.stringify(podcast, null, 2)
          );
        }
      });
      console.log("[publish.js] Finished populating podcast dropdown.");

      if (preSelected) {
        // Explicitly set the select's value as well, though option.selected should suffice
        podcastSelect.value = singlePodcastId;
        console.log(`[Publish Page] Podcast ID "${singlePodcastId}" was pre-selected. Dispatching change event.`);
        // Ensure the change event triggers episode loading
        podcastSelect.dispatchEvent(new Event('change', { bubbles: true }));
      } else if (singlePodcastId) {
        console.warn(`[Publish Page] singlePodcastId ("${singlePodcastId}") was provided, but no matching podcast._id was found in the podcasts list.`);
      }
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
    // Use the correct ID for the episode select element from publish.html
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
      const episodesData = await fetchEpisodesByPodcast(podcastId); // Uses /episodes/by_podcast/<podcast_id>
      // Note: fetchEpisodesByPodcast in episodeRequest.js already returns data.episodes if successful
      // So, episodesData should be the array of episodes directly.
      // If it returns { episodes: [...] }, then const episodes = episodesData.episodes;
      const episodes = Array.isArray(episodesData) ? episodesData : (episodesData && Array.isArray(episodesData.episodes) ? episodesData.episodes : []);

      console.log(`[publish.js] fetchEpisodesByPodcast() raw response for podcast ${podcastId}:`, JSON.stringify(episodes, null, 2));
      
      episodeSelectElement.innerHTML = ''; // Clear previous options
      episodeSelectElement.disabled = false;

      if (episodes && episodes.length > 0) {
        // Sort episodes by created_at or createdAt in descending order (newest first)
        episodes.sort((a, b) => {
          const dateA = new Date(a.created_at || a.createdAt || 0); // Fallback to epoch if undefined
          const dateB = new Date(b.created_at || b.createdAt || 0); // Fallback to epoch if undefined
          return dateB - dateA; 
        });

        episodeSelectElement.innerHTML = '<option value="">-- Select an Episode --</option>';
        episodes.forEach(episode => {
          if (episode && episode._id && episode.title) {
            console.log(`[publish.js] Adding episode option: ID=${episode._id}, Title=${episode.title}, Status=${episode.status}`);
            const option = document.createElement("option");
            option.value = episode._id;
            
            // Display status like [Published] or (Status)
            let statusText = '';
            if (episode.status) {
              if (episode.status.toLowerCase() === "published") {
                statusText = " [Published]";
              } else {
                statusText = ` (${episode.status})`;
              }
            }
            option.textContent = `${episode.title}${statusText}`;
            
            // Apply class based on status
            if (episode.status && episode.status.toLowerCase() === "published") {
              option.className = "published";
            } else {
              option.className = "non-published"; // Or a more generic class
            }

            episodeSelectElement.appendChild(option);
          } else {
            console.warn("[publish.js] Skipping invalid episode object:", JSON.stringify(episode, null, 2));
          }
        });
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

    // Add more strict requirements for Apple/Spotify if needed
    // e.g., Apple requires itunes:category, etc.

    let missing = [];
    requiredPodcastFields.forEach(f => {
      if (!podcast || !podcast[f.key] || podcast[f.key].toString().trim() === "") {
        missing.push({ type: "podcast", ...f });
      }
    });
    requiredEpisodeFields.forEach(f => {
      // pubDate may be publishDate in your model
      let val = episode ? (f.key === "pubDate" ? (episode.publishDate || episode.pubDate) : episode[f.key]) : null;
      if (!val || val.toString().trim() === "") {
        missing.push({ type: "episode", ...f });
      }
    });
    return missing;
  }

  // Helper: Show modal to fill missing fields
  function showMissingFieldsModal(missingFields, podcast, episode, onSave) {
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
    formBox.innerHTML = `<h2>Fill Required Details</h2>
      <form id="missing-fields-form">
        ${missingFields.map(f => {
          let inputValue = "";
          let inputType = "text";
          if (f.type === "episode" && f.key === "pubDate") {
            // Pre-fill with current date-time if publishDate is missing
            const now = new Date();
            // Adjust for local timezone offset to get correct ISO string for datetime-local
            const timezoneOffset = now.getTimezoneOffset() * 60000; //offset in milliseconds
            const localISOTime = (new Date(now - timezoneOffset)).toISOString().slice(0, 16);
            inputValue = localISOTime;
            inputType = "datetime-local";
          }
          return `
          <div class="field-group">
            <label>${f.label} (${f.type})</label>
            <input type="${inputType}" name="${f.type}_${f.key}" value="${inputValue}" required />
          </div>
        `}).join("")}
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

    formBox.querySelector("#missing-fields-form").onsubmit = (e) => {
      e.preventDefault();
      // Update podcast/episode objects with new values
      missingFields.forEach(f => {
        const inputElement = formBox.querySelector(`[name='${f.type}_${f.key}']`);
        let val = inputElement.value.trim();
        if (f.type === "episode" && f.key === "pubDate" && inputElement.type === "datetime-local") {
          // Ensure the datetime-local value is converted to ISO string UTC for backend
          val = new Date(val).toISOString();
        }
        
        if (f.type === "podcast") podcast[f.key] = val;
        else if (f.type === "episode") {
          if (f.key === "pubDate") episode.publishDate = val; // Ensure your episode model uses publishDate
          else episode[f.key] = val;
        }
      });
      document.body.removeChild(modal);
      onSave();
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
    const podcast = (window._publishPodcastsCache || []).find(p => p._id === podcastSelect.value);
    let episode = null;
    try {
      episode = await fetchEpisode(episodeId);
    } catch (e) {}

    // Check for missing required fields
    const missingFields = getMissingRequiredFields(podcast, episode, selectedPlatforms);
    if (missingFields.length > 0) {
      showMissingFieldsModal(missingFields, podcast, episode, async () => {
        // After user fills missing fields, proceed to publish
        await doPublish();
      });
      return;
    }

    // Proceed to publish if nothing missing
    await doPublish();

    async function doPublish() {
      publishNowBtn.disabled = true;
      publishNowBtn.textContent = "Publishing...";
      addToLog(`Starting publishing process for episode ID: ${episodeId}`);
      addToLog(`Selected platforms: ${selectedPlatforms.join(", ")}`);

      try {
        const result = await publishEpisode(episodeId, selectedPlatforms, null);
        if (result.success) {
          addToLog(`Successfully published episode: ${result.message}`);
          showNotification("Success", `Episode published successfully! ${result.message || ''}`, "success");
          episodeDetailsPreview.classList.add("hidden");
          episodeSelect.value = "";
          if (podcastSelect.value) {
              loadEpisodesForPodcast(podcastSelect.value);
          }
          // Show RSS feed popup after successful publish
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
    const podcastData = await fetchPodcasts();
    window._publishPodcastsCache = Array.isArray(podcastData.podcast)
      ? podcastData.podcast
      : (Array.isArray(podcastData.podcasts) ? podcastData.podcasts : []);
  }
  cachePodcasts();
});
