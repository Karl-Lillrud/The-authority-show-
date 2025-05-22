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
  const publishNotes = document.getElementById("publish-notes");

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

  publishNowBtn.addEventListener("click", async () => {
    const episodeId = episodeSelect.value;
    const notes = publishNotes.value;
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

    publishNowBtn.disabled = true;
    publishNowBtn.textContent = "Publishing...";
    addToLog(`Starting publishing process for episode ID: ${episodeId}`);
    addToLog(`Selected platforms: ${selectedPlatforms.join(", ")}`);
    if (notes) {
      addToLog(`Publish notes: ${notes}`);
    }

    try {
      // Using the publishEpisode function from publishRequests.js which calls /api/publish_episode/<episode_id>
      const result = await publishEpisode(episodeId, selectedPlatforms, notes); 
      if (result.success) {
        addToLog(`Successfully published episode: ${result.message}`);
        showNotification("Success", `Episode published successfully! ${result.message || ''}`, "success");
        // Optionally, update episode status in the dropdown or reload episodes
        // For now, just clear selection and notes
        episodeDetailsPreview.classList.add("hidden");
        episodeSelect.value = "";
        publishNotes.value = "";
        // Consider reloading episodes for the current podcast to reflect any status changes
        if (podcastSelect.value) {
            loadEpisodesForPodcast(podcastSelect.value);
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
  });

  // Initial load
  loadPodcasts();
});
