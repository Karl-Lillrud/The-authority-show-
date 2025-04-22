import {
  registerEpisode,
  fetchEpisodesByPodcast,
  updateEpisode,
  deleteEpisode,
  fetchEpisode
} from "../../../static/requests/episodeRequest.js";
import { fetchPodcasts } from "../../../static/requests/podcastRequests.js";
import { fetchGuestsByEpisode } from "../../../static/requests/guestRequests.js";
import {
  updateEditButtons,
  shared
} from "./podcastmanagement.js";
import { renderPodcastSelection, viewPodcast } from "./podcast-functions.js";
import { renderGuestDetail } from "./guest-functions.js";
import { showNotification } from "../components/notifications.js";

// Function to play audio or video
export function playMedia(mediaUrl, title) {
  const mediaPopup = document.createElement("div");
  mediaPopup.className = "media-popup";

  mediaPopup.innerHTML = `
    <div class="media-popup-content">
      <span class="close-media-popup">&times;</span>
      <h2>${title}</h2>
      ${
        mediaUrl.endsWith(".mp4")
          ? `<video controls autoplay>
               <source src="${mediaUrl}" type="video/mp4">
               Your browser does not support the video tag.
             </video>`
          : `<audio controls autoplay>
               <source src="${mediaUrl}" type="audio/mpeg">
               Your browser does not support the audio element.
             </audio>`
      }
    </div>
  `;

  document.body.appendChild(mediaPopup);

  // Close popup event
  mediaPopup
    .querySelector(".close-media-popup")
    .addEventListener("click", () => {
      document.body.removeChild(mediaPopup);
    });
}

// Function to create a play button
export function createPlayButton(size = "small") {
  const playButton = document.createElement("button");
  playButton.className = `play-btn ${size}`;
  playButton.innerHTML = `
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="5 3 19 12 5 21 5 3"></polygon>
    </svg>
  `;
  return playButton;
}

// Function to render episode detail
export function renderEpisodeDetail(episode) {
  const episodeDetailElement = document.getElementById("podcast-detail");
  const publishDate = episode.publishDate
    ? new Date(episode.publishDate).toLocaleString()
    : "Not specified";

  // Convert duration from seconds to minutes and seconds
  const durationMinutes = Math.floor(episode.duration / 60);
  const durationSeconds = episode.duration % 60;
  const formattedDuration = `${durationMinutes}m ${durationSeconds}s`;

  const episodeType = episode.episodeType || "Unknown";
  const link = episode.link || "No link available";
  const host = episode.author || "Unknown"; // Changed "author" to "host"
  const fileSize = episode.fileSize || "Unknown";
  const fileType = episode.fileType || "Unknown";

  episodeDetailElement.innerHTML = `
  <div class="detail-header">
    <button class="back-btn" id="back-to-podcast">
      ${shared.svgpodcastmanagement.back}
      Back to podcast
    </button>
    <div class="top-right-actions">
      <button class="action-btn edit-btn" id="edit-episode-btn" data-id="${
        episode._id
      }" data-tooltip="Edit">
        ${shared.svgpodcastmanagement.edit}
      </button>
      ${
        episode.status !== "Published"
          ? `<button class="action-btn publish-btn" id="publish-episode-btn" data-id="${episode._id}" data-tooltip="Publish">
               ${shared.svgpodcastmanagement.upload}
             </button>`
          : `<span class="published-label">Published</span>`
      }
    </div>
  </div>
  <div class="detail-content">
    <div class="detail-image" style="background-image: url('${
      episode.image || "default-image.png"
    }')"></div>
    <div class="detail-info">
      <h1 class="detail-title">${episode.title}</h1>
      <p class="detail-category">${episode.status || "Uncategorized"}</p>
      <div class="detail-section">
        <h2>About</h2>
        <p>${episode.description || "No description available."}</p>
        <!-- Media player -->
        ${
          episode.audioUrl
            ? `<div class="media-player-container">
                ${
                  episode.audioUrl.endsWith(".mp4")
                    ? `<video controls>
                        <source src="${episode.audioUrl}" type="video/mp4">
                        Your browser does not support the video element.
                      </video>`
                    : `<audio controls>
                        <source src="${episode.audioUrl}" type="audio/mpeg">
                        Your browser does not support the audio element.
                      </audio>`
                }
              </div>`
            : "<p>No media available for this episode.</p>"
        }
      </div>
      <div class="separator"></div>
      <div class="detail-grid">
        <div class="detail-item">
          <h3>Episode Type</h3>
          <p>${episodeType}</p>
        </div>
        <div class="detail-item">
          <h3>File Size</h3>
          <p>${fileSize}</p>
        </div>
        <div class="detail-item">
          <h3>File Type</h3>
          <p>${fileType}</p>
        </div>
        <div class="detail-item">
          <h3>Link</h3>
          ${
            link !== "No link available"
              ? `<a href="${link}" target="_blank">${link}</a>`
              : `<p>${link}</p>`
          }
        </div>
      </div>
    </div>
  </div>
  
  <!-- Guests section -->
  <div class="podcast-about-section">
    <h2 class="section-title">Guests</h2>
    <div id="guests-list"></div>
  </div>
</div>

<div class="detail-actions">
  <button class="delete-btn" id="delete-episode-btn" data-id="${episode._id}">
    ${shared.svgpodcastmanagement.delete} Delete Episode
  </button>
</div>
`;

  // Define the episodeActions container
  const episodeActions = document.getElementById("episode-actions");

  // Publish button event listener
  document
    .getElementById("publish-episode-btn")
    .addEventListener("click", async () => {
      const episodeId = document
        .getElementById("publish-episode-btn")
        .getAttribute("data-id");
      try {
        const response = await fetch(`/publish/${episodeId}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          }
        });

        const data = await response.json();
        if (response.ok) {
          showNotification("Success", "Published successfully!", "success");

          // Update the status to "Published"
          const statusElement = document.querySelector(".detail-category");
          if (statusElement) {
            statusElement.textContent = "Published";
          }
        } else {
          showNotification(
            "Error",
            `Failed to publish episode: ${data.error}`,
            "error"
          );
        }
      } catch (error) {
        console.error("Error publishing episode:", error);
        showNotification(
          "Error",
          "An unexpected error occurred while publishing the episode.",
          "error"
        );
      }
    });

  // Back button event listener
  const backButton = document.getElementById("back-to-podcast");
  if (backButton) {
    backButton.addEventListener("click", () => {
      if (!shared.selectedPodcastId) {
        shared.selectedPodcastId = episode.podcast_id || episode.podcastId;
      }
      if (shared.selectedPodcastId) {
        viewPodcast(shared.selectedPodcastId);
      } else {
        console.error(
          "Podcast ID is missing. Cannot navigate back to podcast."
        );
        showNotification(
          "Error",
          "Podcast ID is missing. Cannot navigate back.",
          "error"
        );
      }
    });
  }

  // Edit button event listener
  const editButton = document.getElementById("edit-episode-btn");
  if (editButton) {
    editButton.addEventListener("click", async () => {
      try {
        const episodeId = editButton.getAttribute("data-id");
        const response = await fetchEpisode(episodeId);
        showEpisodePopup(response);
      } catch (error) {
        showNotification("Error", "Failed to fetch episode details", "error");
      }
    });
  }

  // Delete button event listener
  const deleteButton = document.getElementById("delete-episode-btn");
  if (deleteButton) {
    deleteButton.addEventListener("click", async () => {
      if (confirm("Are you sure you want to delete this episode?")) {
        try {
          await deleteEpisode(episode._id);
          showNotification(
            "Success",
            "Episode deleted successfully!",
            "success"
          );
          viewPodcast(episode.podcast_id);
        } catch (error) {
          showNotification("Error", "Failed to delete episode.", "error");
        }
      }
    });
  }

  // Fetch and display guests for the episode
  fetchGuestsByEpisode(episode._id)
    .then((guests) => {
      const guestsListEl = document.getElementById("guests-list");
      if (guestsListEl) {
        guestsListEl.innerHTML = "";
        if (guests && guests.length) {
          const guestsContainer = document.createElement("div");
          guestsContainer.className = "guests-container";
          guests.forEach((guest) => {
            const guestCard = document.createElement("div");
            guestCard.className = "guest-card";
            const initials = guest.name
              .split(" ")
              .map((word) => word[0])
              .join("")
              .substring(0, 2)
              .toUpperCase();
            const contentDiv = document.createElement("div");
            contentDiv.className = "guest-info";
            const avatarDiv = document.createElement("div");
            avatarDiv.className = "guest-avatar";
            avatarDiv.textContent = initials;
            const infoDiv = document.createElement("div");
            infoDiv.className = "guest-content";
            const nameDiv = document.createElement("div");
            nameDiv.className = "guest-name";
            nameDiv.textContent = guest.name;
            const emailDiv = document.createElement("div");
            emailDiv.className = "guest-email";
            emailDiv.textContent = guest.email;
            infoDiv.appendChild(nameDiv);
            infoDiv.appendChild(emailDiv);
            const viewProfileBtn = document.createElement("button");
            viewProfileBtn.className = "view-profile-btn";
            viewProfileBtn.textContent = "View Profile";
            viewProfileBtn.addEventListener("click", (e) => {
              e.stopPropagation();
              renderGuestDetail(guest);
            });
            guestCard.addEventListener("click", () => {
              renderGuestDetail(guest);
            });
            contentDiv.appendChild(avatarDiv);
            contentDiv.appendChild(infoDiv);
            guestCard.appendChild(contentDiv);
            guestCard.appendChild(viewProfileBtn);
            guestsContainer.appendChild(guestCard);
          });
          guestsListEl.appendChild(guestsContainer);
        } else {
          const noGuests = document.createElement("p");
          noGuests.className = "no-guests-message";
          noGuests.textContent = "No guests available for this episode.";
          guestsListEl.appendChild(noGuests);
        }
      }
    })
    .catch((error) => {
      console.error("Error fetching guests:", error);
      const guestsListEl = document.getElementById("guests-list");
      if (guestsListEl) {
        const errorMsg = document.createElement("p");
        errorMsg.className = "error-message";
        errorMsg.textContent = "This episode has no guests.";
        guestsListEl.appendChild(errorMsg);
      }
    });

  // Update edit buttons after rendering
  updateEditButtons();
}
// New function to display the episode popup for viewing/updating an episode
async function showEpisodePopup(episode) {
  const popup = document.createElement("div");
  popup.className = "popup";
  popup.style.display = "flex";

  const popupContent = document.createElement("div");
  popupContent.className = "form-box";
  popupContent.innerHTML = `
  <span id="close-episode-popup" class="close-btn">&times;</span>
  <h2 class="form-title">Edit Episode</h2>
  <form id="update-episode-form">
    <div class="field-group full-width">
      <label for="upd-episode-title">Episode Title</label>
      <input type="text" id="upd-episode-title" name="title" value="${
        episode.title
      }" required />
    </div>
    <div class="field-group full-width">
      <label for="upd-episode-description">Description</label>
      <textarea id="upd-episode-description" name="description" rows="3">${
        episode.description || ""
      }</textarea>
    </div>
    <div class="field-group">
      <label for="upd-publish-date">Publish Date</label>
      <input type="datetime-local" id="upd-publish-date" name="publishDate" value="${
        episode.publishDate
          ? new Date(episode.publishDate).toISOString().slice(0, 16)
          : ""
      }" required />
    </div>
    <div class="field-group">
      <label for="upd-duration">Duration (minutes)</label>
      <input type="number" id="upd-duration" name="duration" value="${
        episode.duration || ""
      }" />
    </div>
    <div class="field-group">
      <label for="upd-status">Status</label>
      <input type="text" id="upd-status" name="status" value="${
        episode.status || ""
      }" />
    </div>
    <div class="form-actions">
      <button type="button" id="cancel-episode-update" class="cancel-btn">Cancel</button>
      <button type="submit" class="save-btn">Update Episode</button>
    </div>
  </form>
`;
  popup.appendChild(popupContent);
  document.body.appendChild(popup);

  // Close popup events
  popup.querySelector("#close-episode-popup").addEventListener("click", () => {
    document.body.removeChild(popup);
  });
  popup
    .querySelector("#cancel-episode-update")
    .addEventListener("click", () => {
      document.body.removeChild(popup);
    });

  // Update episode form submission
  popup
    .querySelector("#update-episode-form")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      const updatedData = {
        title: document.getElementById("upd-episode-title").value.trim(),
        description: document
          .getElementById("upd-episode-description")
          .value.trim(),
        publishDate: document.getElementById("upd-publish-date").value,
        duration: document.getElementById("upd-duration").value,
        status: document.getElementById("upd-status").value.trim()
      };
      Object.keys(updatedData).forEach((key) => {
        if (!updatedData[key]) delete updatedData[key];
      });

      if (updatedData.duration) {
        if (updatedData.duration < 0) {
          showNotification(
            "Invalid duration",
            "Please provide a positive integer for duration",
            "error"
          );
          return;
        }
      }

      try {
        const result = await updateEpisode(episode._id, updatedData); // Use updateEpisode from episodeRequest.js
        if (result.message) {
          showNotification(
            "Success",
            "Episode updated successfully!",
            "success"
          );
          document.body.removeChild(popup);
          // Update the episode details in the DOM
          renderEpisodeDetail({ ...episode, ...updatedData });
        } else {
          showNotification("Error", result.error || "Update failed", "error");
        }
      } catch (error) {
        showNotification("Error", "Failed to update episode.", "error");
      }
    });
}

// Initialize episode functions
export function initEpisodeFunctions() {
  // Show form for creating a new episode
  document
    .getElementById("create-episode-btn")
    .addEventListener("click", async () => {
      try {
        const response = await fetchPodcasts();
        const podcasts = response.podcast;

        if (!podcasts || podcasts.length === 0) {
          showNotification(
            "No Podcasts",
            "You need to create a podcast first before adding episodes.",
            "info"
          );
          return;
        }

        renderPodcastSelection(podcasts);
        document.getElementById("episode-form-popup").style.display = "flex";
      } catch (error) {
        console.error("Error fetching podcasts:", error);
        showNotification(
          "Error",
          "Failed to load podcasts for episode creation.",
          "error"
        );
      }
    });
  // Close the episode form popup
  document
    .getElementById("close-episode-form-popup")
    .addEventListener("click", () => {
      document.getElementById("episode-form-popup").style.display = "none";
    });

  // Cancel button in episode form
  document
    .getElementById("cancel-episode-form-btn")
    .addEventListener("click", () => {
      document.getElementById("episode-form-popup").style.display = "none";
    });

  // Update the episode creation form to include recordingAt
  /* document.getElementById("create-episode-form").innerHTML += `
    <div class="field-group">
      <label for="recording-at">Recording Date</label>
      <input type="datetime-local" id="recording-at" name="recordingAt" />
    </div>
  `; */

  // Assuming you are getting the episode data from the backend or checking a condition
  function loadEpisodeDetails(episodeData) {
    const episodeInput = document.getElementById("episode-id");

    // Check if the episode is created
    if (episodeData && episodeData.isCreated) {
      // Disable the input field and apply greyed-out styles
      episodeInput.disabled = true;
      episodeInput.style.backgroundColor = "#d3d3d3"; // Grey out the background
      episodeInput.style.color = "#a9a9a9"; // Grey out the text
    } else {
      // Enable the input field if the episode is not created
      episodeInput.disabled = false;
      episodeInput.style.backgroundColor = ""; // Reset background color
      episodeInput.style.color = ""; // Reset text color
    }
  }

  // Example usage when the episode data is available
  const episodeData = {
    isCreated: true // Example flag, replace with actual check
  };
  loadEpisodeDetails(episodeData);

  // Episode form submission
  document
    .getElementById("create-episode-form")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      const data = Object.fromEntries(formData.entries());

      // Ensure recordingAt is in the correct format
      if (data.recordingAt === '') {
        data.recordingAt = null; // Set to null if no date is provided
      } else if (data.recordingAt) {
        const recordingAt = new Date(data.recordingAt);
        if (isNaN(recordingAt.getTime())) {
          showNotification(
            "Invalid Date",
            "Please provide a valid recording date.",
            "error"
          );
          return;
        }
      }

      // Check for missing required fields
      if (!data.podcastId || !data.title || !data.publishDate) {
        showNotification(
          "Missing Fields",
          "Please fill in all required fields.",
          "error"
        );
        return;
      }

      // Ensure publishDate is in the correct format
      const publishDate = new Date(data.publishDate);
      if (isNaN(publishDate.getTime())) {
        showNotification(
          "Invalid Date",
          "Please provide a valid publish date.",
          "error"
        );
        return;
      }
      if (data.duration) {
        if (data.duration < 0) {
          showNotification(
            "Invalid duration",
            "Please provide a positive integer for duration",
            "error"
          );
          return;
        }
      }

      try {
        const result = await registerEpisode(data);
        console.log("Result from registerEpisode:", result);
        if (result.message) {
          showNotification(
            "Success",
            "Episode created successfully!",
            "success"
          );
          document.getElementById("episode-form-popup").style.display = "none";
          document.getElementById("create-episode-form").reset();
          // Refresh the episode list without refreshing the page
          viewPodcast(data.podcastId);
        } else {
          showNotification("Error", result.error, "error");
        }
      } catch (error) {
        console.error("Error creating episode:", error);
        showNotification("Error", "Failed to create episode.", "error");
      }
    });
}
