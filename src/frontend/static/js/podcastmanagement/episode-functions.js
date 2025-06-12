import {
  registerEpisode,
  fetchEpisode,
  updateEpisode,
  deleteEpisode
} from "../../../static/requests/episodeRequest.js";
import { fetchPodcasts } from "../../../static/requests/podcastRequests.js";
import { fetchGuestsByEpisode } from "../../../static/requests/guestRequests.js";
import { updateEditButtons, shared } from "./podcastmanagement.js";
import { renderPodcastSelection, viewPodcast } from "./podcast-functions.js";
import { renderGuestDetail } from "./guest-functions.js";
import { showNotification, showConfirmationPopup } from "../components/notifications.js";
import { consumeStoreCredits, getCredits } from "../../../static/requests/creditRequests.js";
import { incrementUpdateAccount } from "../../../static/requests/accountRequests.js";
import { showAddGuestPopup } from "./guest-functions.js";
import { createGuestInvitation } from "../../../static/requests/invitationRequests.js";

// Add this function to create a play button with SVG icon
export function createPlayButton(size = "medium") {
  const button = document.createElement("button");
  button.className =
    size === "small" ? "podcast-episode-play" : "episode-play-btn";

  // Play icon SVG
  button.innerHTML = `
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <polygon points="5 3 19 12 5 21 5 3"></polygon>
  </svg>
`;

  return button;
}

// Add this function to handle audio playback
export function playAudio(audioUrl, episodeTitle) {
  // Check if there's an existing audio player in the page
  let audioPlayer = document.getElementById("global-audio-player");

  if (!audioPlayer) {
    // Create a new audio player if one doesn't exist
    audioPlayer = document.createElement("div");
    audioPlayer.id = "global-audio-player";
    audioPlayer.className = "global-audio-player";

    document.body.appendChild(audioPlayer);
  }

  // Update the audio player content
  audioPlayer.innerHTML = `
  <div class="audio-player-header">
    <div class="audio-player-title">${episodeTitle}</div>
    <button id="close-audio-player" class="audio-player-close">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="18" y1="6" x2="6" y2="18"></line>
        <line x1="6" y1="6" x2="18" y2="18"></line>
      </svg>
    </button>
  </div>
  <audio controls autoplay>
    <source src="${audioUrl}" type="audio/mpeg">
    Your browser does not support the audio element.
  </audio>
`;

  // Add error event to the audio element
  const audioEl = audioPlayer.querySelector("audio");
  if (audioEl) {
    audioEl.addEventListener("error", () => {
      showNotification("Error", "Failed to load or play audio.", "error");
    });
  }

  // Add event listener to close button
  document
    .getElementById("close-audio-player")
    .addEventListener("click", () => {
      document.body.removeChild(audioPlayer);
    });
}

export function renderEpisodeDetail(episode) {
  sessionStorage.setItem("selected_episode_id", episode._id);
  const episodeDetailElement = document.getElementById("podcast-detail");
  const publishDate = episode.publishDate
    ? new Date(episode.publishDate).toLocaleString()
    : "Not specified";

  // Convert duration from seconds to minutes and seconds
  const durationMinutes = Math.floor(episode.duration / 60);
  const durationSeconds = episode.duration % 60;
  const formattedDuration = `${durationMinutes}m ${durationSeconds}s`;

  const episodeType = episode.episodeType ? episode.episodeType : '<em>Edit episode to choose "type"</em>';
  const link = episode.link ? episode.link : "<em>Your RSS Feed URL when published</em>";
  const host = episode.author || "Unknown"; // Changed "author" to "host"
  const fileSize = episode.fileSize ? episode.fileSize : "<em>Upload or Record media</em>";
  const fileType = episode.fileType ? episode.fileType : "<em>Upload or Record media</em>";

  episodeDetailElement.innerHTML = `
<div class="detail-header">
  <button class="back-btn" id="back-to-podcast">
    ${shared.svgpodcastmanagement.back}
    Back to podcast
  </button>
  <div class="top-right-actions">
    <!-- Studio Button -->
    ${(() => {
      const now = new Date();
      let isStudioEnabled = false;
      let timeLeft = "";
      if (episode.recordingAt) {
        const recordingTime = new Date(episode.recordingAt);
        if (recordingTime > now) {
          const diffMs = recordingTime - now;
          const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
          const diffMin = Math.floor((diffMs / (1000 * 60)) % 60);
          timeLeft = `${diffHrs}h ${diffMin}m left`;
        } else {
          isStudioEnabled = true;
        }
      }
      if (isStudioEnabled) {
        return `<button class="studio-btn studio-btn-on" id="studio-btn" style="border: 1px solid #d219b9" data-podcast-id="${episode.podcastId || episode.podcast_id}" data-episode-id="${episode._id}">
          <svg width="20px" height="20px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M19 10V12C19 15.866 15.866 19 12 19M5 10V12C5 15.866 8.13401 19 12 19M12 19V22M8 22H16M15 6H13M15 10H13M12 15C10.3431 15 9 13.6569 9 12V5C9 3.34315 10.3431 2 12 2C13.6569 2 15 3.34315 15 5V12C15 13.6569 13.6569 15 12 15Z" stroke="#d219b9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> </g></svg>
        </button>`;
      } else {
        return `<button class="studio-btn studio-btn-off" id="studio-btn" style="cursor: not-allowed; border: 1px solid #616161" disabled>
          <svg width="20px" height="20px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M15 9.4V5C15 3.34315 13.6569 2 12 2C10.8224 2 9.80325 2.67852 9.3122 3.66593M12 19V22M8 22H16M3 3L21 21M5.00043 10C5.00043 10 3.50062 19 12.0401 19C14.51 19 16.1333 18.2471 17.1933 17.1768M19.0317 13C19.2365 11.3477 19 10 19 10M15 6H13M12 15C10.3431 15 9 13.6569 9 12V9L14.1226 14.12C13.5796 14.6637 12.8291 15 12 15Z" stroke="#616161" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> </g></svg>
        </button>`;
      }
    })()}
    ${
      !episode.isImported
        ? `
    <button class="save-btn" id="ai-edit-episode-btn" data-id="${episode._id}">
    <svg width="20px" height="20px" viewBox="-1.2 -1.2 26.40 26.40" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M9 15C8.44771 15 8 15.4477 8 16C8 16.5523 8.44771 17 9 17C9.55229 17 10 16.5523 10 16C10 15.4477 9.55229 15 9 15Z" fill="#0091ff"></path> <path d="M14 16C14 15.4477 14.4477 15 15 15C15.5523 15 16 15.4477 16 16C16 16.5523 15.5523 17 15 17C14.4477 17 14 16.5523 14 16Z" fill="#0091ff"></path> <path fill-rule="evenodd" clip-rule="evenodd" d="M12 1C10.8954 1 10 1.89543 10 3C10 3.74028 10.4022 4.38663 11 4.73244V7H6C4.34315 7 3 8.34315 3 10V20C3 21.6569 4.34315 23 6 23H18C19.6569 23 21 21.6569 21 20V10C21 8.34315 19.6569 7 18 7H13V4.73244C13.5978 4.38663 14 3.74028 14 3C14 1.89543 13.1046 1 12 1ZM5 10C5 9.44772 5.44772 9 6 9H7.38197L8.82918 11.8944C9.16796 12.572 9.86049 13 10.618 13H13.382C14.1395 13 14.832 12.572 15.1708 11.8944L16.618 9H18C18.5523 9 19 9.44772 19 10V20C19 20.5523 18.5523 21 18 21H6C5.44772 21 5 20.5523 5 20V10ZM13.382 11L14.382 9H9.61803L10.618 11H13.382Z" fill="#0091ff"></path> <path d="M1 14C0.447715 14 0 14.4477 0 15V17C0 17.5523 0.447715 18 1 18C1.55228 18 2 17.5523 2 17V15C2 14.4477 1.55228 14 1 14Z" fill="#0091ff"></path> <path d="M22 15C22 14.4477 22.4477 14 23 14C23.5523 14 24 14.4477 24 15V17C24 17.5523 23.5523 18 23 18C22.4477 18 22 17.5523 22 17V15Z" fill="#0091ff"></path> </g></svg>
    </button>\n    `
        : ""
    }
    <button class="action-btn edit-btn" id="edit-episode-btn" data-id="${episode._id}">\n      ${shared.svgpodcastmanagement.edit}\n    </button>\n    <button class="action-btn delete-btn" id="delete-episode-btn" data-id="${episode._id}">\n      <span class="icon">${shared.svgpodcastmanagement.delete}</span>\n    </button>\n  </div>
</div>

<div class="podcast-detail-container">
  <!-- Header section with image and basic info -->
  <div class="podcast-header-section">
    <div class="podcast-image-container">
      <div class="detail-image" style="background-image: url('${episode.image || episode.imageUrl || "/static/images/default-image.png"}')"></div>
    </div>
    <div class="podcast-basic-info">
      <h1 class="detail-title">${episode.title}</h1>
      ${episode.status ? `<p class="detail-category">${episode.status}</p>` : ""}
      <div class="podcast-meta-info">
        <div class="meta-item">
          <span class="meta-label">Publish Date:</span>
          <span class="meta-value">${publishDate}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Duration:</span>
          <span class="meta-value">${formattedDuration}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Host:</span>
          <span class="meta-value">${host}</span>
        </div>
      </div>
    </div>
  </div>
  
  <!-- About section -->
  <div class="podcast-about-section">
    <h2 class="section-title section-description-title">Description</h2>
    <p class="podcast-description">${episode.description || "No description available."}</p>
    
    <!-- Audio Section Wrapper - Only contains the main player now -->
    <div class="audio-section-wrapper" style="margin-top: 1.5rem;">
      <!-- Main Media Player -->
      <div class="main-media-player">
        <h3>Media Player</h3>
        ${
          episode.audioUrl
            ? `<audio controls style="width: 20%;">
                 <source src="${episode.audioUrl}" type="${fileType || "audio/mpeg"}">
                 Your browser does not support the audio element.
               </audio>`
            : "<p><em>Upload or Record media</em></p>"
        }
      </div>
    </div>

    <!-- Saved Media Edits -->
    ${
      episode.audioEdits && episode.audioEdits.length > 0
        ? `<div class="audio-edits" style="margin-top: 1.5rem;">
            <h3>🎧 Saved Edits</h3>
            ${episode.audioEdits
              .map((edit) => {
                const blobUrl = edit.metadata?.blob_url;
                const label = edit.metadata?.edit_type || edit.edit_type || "Unknown Type";
                return `
                <div class="edit-entry" style="margin-bottom: 1rem;">
                  <p style="margin-bottom: 0.25rem;"><strong>${label}</strong> – ${edit.filename}</p>
                  ${
                    blobUrl
                      ? `<audio controls style="width: 100%;">
                          <source src="${blobUrl}" type="audio/wav">
                          Your browser does not support the audio element.
                        </audio>`
                      : `<p style="color: red;">❌ No audio URL available</p>`
                  }
                </div>`;
              })
              .join("")}
          </div>`
        : ""
    }
  </div>

  <!-- Episode Details section -->
  <div class="podcast-about-section">
    <h2 class="section-title">Episode Details</h2>
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
        ${link !== "<em>Your RSS Feed URL when published</em>" && link !== "No link available" ? `<a href="${link}" target="_blank">${link}</a>` : `<p>${link}</p>`}
      </div>
    </div>
  </div>
  
  <!-- Guests section -->
  <div class="podcast-about-section">
    <h2 class="section-title">Guests</h2>
    <div id="guests-list"></div>
  </div>
</div>
`;

  // Add event listener for the Studio button
const studioButton = document.getElementById("studio-btn");
if (studioButton && !studioButton.disabled) {
    studioButton.addEventListener("click", () => {
        const podcastId = studioButton.getAttribute("data-podcast-id");
        const episodeId = studioButton.getAttribute("data-episode-id");
        if (!podcastId || !episodeId) {
            console.error('Missing podcastId or episodeId on studio button');
            showNotification('Error: Invalid podcast or episode.', 'error');
            return;
        }
        // Navigate to studio page with room parameter
        window.location.href = `/studio?podcastId=${podcastId}&episodeId=${episodeId}&room=${episodeId}`;
        console.log(`Studio button clicked for podcast ${podcastId}, episode ${episodeId}, room ${episodeId}`);
    });
}

  // Add event listener for the AI Edit button
  const aiEditButton = document.getElementById("ai-edit-episode-btn");
  if (aiEditButton) {
    aiEditButton.addEventListener("click", () => {
      const episodeId = aiEditButton.getAttribute("data-id");
      // Redirect to the Episode To-Do page, opening the AI Workspace tab.
      // The episode-to-do page should handle the episodeId and openTab parameters.
      const aiWorkspaceUrl = `/episode-to-do?episodeId=${episodeId}&openTab=workspace`;
      window.location.href = aiWorkspaceUrl;
    });
  }

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
        console.error("Podcast ID is missing. Cannot navigate back to podcast.");
        showNotification("Error", "Podcast ID is missing. Cannot navigate back.", "error");
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
    deleteButton.addEventListener("click", () => {
      showConfirmationPopup(
        "Delete Episode",
        "Are you sure you want to delete this episode? This action cannot be undone.",
        async () => {
          try {
            await deleteEpisode(episode._id);
            showNotification("Success", "Episode deleted successfully!", "success");
            viewPodcast(episode.podcast_id);
          } catch (error) {
            showNotification("Error", "Failed to delete episode.", "error");
          }
        },
        () => {
          showNotification("Info", "Episode deletion canceled.", "info");
        }
      );
    });
  }

  fetchGuestsByEpisode(episode._id)
    .then((guests) => {
      const guestsListEl = document.getElementById("guests-list");
      if (guestsListEl) {
        guestsListEl.innerHTML = "";
        if (guests && guests.length) {
          console.log("Guests fetched:", JSON.stringify(guests, null, 2));
          const guestsContainer = document.createElement("div");
          guestsContainer.className = "guests-container";

          if (!episode._id) {
            console.error("Episode ID is undefined or missing:", episode);
            showNotification("Failed to send invitation: Episode ID is missing", "error");
            return;
          }

          guests.forEach((guest) => {
            const guestCard = document.createElement("div");
            guestCard.className = "guest-card";

            const initials = guest.name
              ? guest.name
                  .split(" ")
                  .map((word) => word[0])
                  .join("")
                  .substring(0, 2)
                  .toUpperCase()
              : "NA";

            const contentDiv = document.createElement("div");
            contentDiv.className = "guest-info";

            const avatarDiv = document.createElement("div");
            avatarDiv.className = "guest-avatar";
            avatarDiv.textContent = initials;

            const infoDiv = document.createElement("div");
            infoDiv.className = "guest-content";

            const nameDiv = document.createElement("div");
            nameDiv.className = "guest-name";
            nameDiv.textContent = guest.name || "Unknown";

            const emailDiv = document.createElement("div");
            emailDiv.className = "guest-email";
            emailDiv.textContent = guest.email || "No email";

            infoDiv.appendChild(nameDiv);
            infoDiv.appendChild(emailDiv);

            const buttonContainer = document.createElement("div");
            buttonContainer.className = "guest-buttons";

            const viewProfileBtn = document.createElement("button");
            viewProfileBtn.className = "view-profile-btn";
            viewProfileBtn.textContent = "View Profile";

            viewProfileBtn.addEventListener("click", (e) => {
              e.stopPropagation();
              renderGuestDetail(guest);
            });

            const guestId = guest._id || guest.id || guest.guestId;
            if (guestId) {
              const inviteGuestBtn = document.createElement("button");
              inviteGuestBtn.className = "view-profile-btn";
              inviteGuestBtn.textContent = "Invite Guest";
              inviteGuestBtn.addEventListener("click", async (e) => {
                e.stopPropagation();
                try {
                  console.log("Sending invitation for episode:", episode._id, "guest:", guestId);
                  const result = await createGuestInvitation(episode._id, guestId);
                  showNotification(`Invitation sent to ${guest.name || "Guest"}!`, "success");
                } catch (error) {
                  console.error("Error sending invitation:", error);
                  showNotification(`Failed to send invitation: ${error.message}`, "error");
                }
              });
              buttonContainer.appendChild(inviteGuestBtn);
            } else {
              console.warn("No valid guest ID found for guest:", JSON.stringify(guest, null, 2));
              const errorMsg = document.createElement("span");
              errorMsg.className = "guest-error";
              errorMsg.textContent = "Cannot invite: No ID";
              errorMsg.style.color = "red";
              errorMsg.style.fontSize = "0.8em";
              buttonContainer.appendChild(errorMsg);
            }

            guestCard.addEventListener("click", () => {
              renderGuestDetail(guest);
            });

            contentDiv.appendChild(avatarDiv);
            contentDiv.appendChild(infoDiv);
            buttonContainer.appendChild(viewProfileBtn);
            guestCard.appendChild(contentDiv);
            guestCard.appendChild(buttonContainer);
            guestsContainer.appendChild(guestCard);
          });

          guestsListEl.appendChild(guestsContainer);
        } else {
          console.log("No guests found for episode:", episode._id);
          const noGuestsContainer = document.createElement("div");
          noGuestsContainer.className = "no-guests-container";

          const noGuestsMsg = document.createElement("p");
          noGuestsMsg.className = "no-guests-message";
          noGuestsMsg.textContent = "No guests to display.";

          const addGuestBtn = document.createElement("button");
          addGuestBtn.className = "save-btn guest-btn";
          addGuestBtn.textContent = "Add Guest";
          addGuestBtn.onclick = function () {
            showAddGuestPopup();
          };

          noGuestsContainer.appendChild(noGuestsMsg);
          noGuestsContainer.appendChild(addGuestBtn);
          guestsListEl.appendChild(noGuestsContainer);
        }
      }
    })
    .catch((error) => {
      console.error("Error fetching guests:", error);
      const guestsListEl = document.getElementById("guests-list");
      if (guestsListEl) {
        const errorMsg = document.createElement("p");
        errorMsg.className = "error-message";
        errorMsg.textContent = "No guests to display.";
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

  // Determine if the file input should be disabled: Disable if episode IS imported
  const isAudioUploadDisabled = episode.isImported === true;

const popupContent = document.createElement("div");
popupContent.className = "form-box";
popupContent.innerHTML = `
  <span id="close-episode-popup" class="close-btn">×</span>
  <h2 class="form-title">Edit Episode</h2>
  <form id="update-episode-form" enctype="multipart/form-data"> 
    <div class="field-group full-width">
      <label for="upd-episode-title">Episode Title</label>
      <input type="text" id="upd-episode-title" name="title" value="${episode.title || ""}" placeholder="Enter episode title" />
    </div>

    <div class="field-group full-width">
      <label for="upd-episode-description">Description</label>
      <textarea id="upd-episode-description" name="description" rows="3" placeholder="Describe what this episode is about">${episode.description || ""}</textarea>
    </div>

    <div class="field-group full-width">
      <label for="upd-summary">Episode Summary</label>
      <textarea id="upd-summary" name="summary" rows="2" placeholder="Summary of the episode...">${episode.summary || ""}</textarea>
    </div>

    <div class="field-group">
      <label for="upd-author">Author</label>
      <input type="text" id="upd-author" name="author" value="${episode.author || ""}" placeholder="e.g. Jane Doe" pattern="[A-Za-z\\s\\-\\.]{1,100}" title="Author name can only contain letters, spaces, hyphens, and periods" />
    </div>

    <h3 class="form-section-heading">Publishing Details</h3>
    <div class="field-group">
      <label for="upd-publish-date">Publish Date</label>
      <input type="datetime-local" id="upd-publish-date" name="publishDate" value="${
        episode.publishDate ? new Date(episode.publishDate).toISOString().slice(0, 16) : ""
      }" />
    </div>

    <div class="field-group">
      <label for="upd-status">Status</label>
      <select id="upd-status" name="status">
        <option value="">-- Select status --</option>
        ${["Not Recorded", "Published", "Recorded", "Edited", "Not Scheduled"]
          .map(
            (status) =>
              `<option value="${status}" ${episode.status === status ? "selected" : ""}>${status}</option>`
          )
          .join("")}
      </select>
    </div>

    <div class="field-group">
      <label for="upd-duration">Duration (minutes)</label>
      <input 
        type="number" 
        id="upd-duration" 
        name="duration_minutes" 
        value="${episode.duration ? Math.floor(episode.duration / 60) : ''}" 
        readonly 
        style="background-color: #f5f5f5; cursor: not-allowed;"
      />
      <small style="font-size: 0.8em; color: #666;">Automatically calculated from audio file</small>
    </div>

    <div class="field-group">
      <label for="upd-recording-at">Recording Date</label>
      <input type="datetime-local" id="upd-recording-at" name="recordingAt" value="${
        episode.recordingAt ? new Date(episode.recordingAt).toISOString().slice(0, 16) : ""
      }" />
    </div>

    <h3 class="form-section-heading">Episode Metadata</h3>
    <div class="field-group">
      <label for="upd-season">Season</label>
      <input type="number" id="upd-season" name="season" value="${episode.season || ""}" placeholder="e.g. 1" min="0" step="1" />
    </div>

    <div class="field-group">
      <label for="upd-episode">Episode Number</label>
      <input type="number" id="upd-episode" name="episode" value="${episode.episode || ""}" placeholder="e.g. 5" min="0" step="1" />
    </div>

    <div class="field-group">
      <label for="upd-episode-type">Episode Type</label>
      <select id="upd-episode-type" name="episodeType">
        ${["", "full", "trailer", "bonus"]
          .map(
            (type) =>
              `<option value="${type}" ${episode.episodeType === type ? "selected" : ""}>${type || "-- Select Type --"}</option>`
          )
          .join("")}
      </select>
    </div>

    <div class="field-group">
      <label for="upd-explicit">Contains Explicit Content?</label>
      <select id="upd-explicit" name="explicit">
        <option value="" ${episode.explicit === null || episode.explicit === undefined ? "selected" : ""}>-- Select --</option>
        <option value="true" ${String(episode.explicit) === "true" ? "selected" : ""}>Yes</option>
        <option value="false" ${String(episode.explicit) === "false" ? "selected" : ""}>No</option>
      </select>
    </div>

    <h3 class="form-section-heading">Media</h3>
    <div class="field-group full-width">
      <label for="upd-episode-audio" ${isAudioUploadDisabled ? 'style="color: #aaa;"' : ""}>
        Upload New Media (Optional)
      </label>
      <input type="file" id="upd-episode-audio" name="audioFile" accept="audio/mp3,audio/wav,audio/mpeg,video/mp4" ${
        isAudioUploadDisabled ? 'disabled style="background-color: #eee;"' : ""
      }>
      ${
        isAudioUploadDisabled
          ? '<p style="font-size: 0.8em; color: #888; margin-top: 5px;">Media upload disabled for imported episodes.</p>'
          : episode.audioUrl
            ? `<p style="font-size: 0.8em; margin-top: 5px;">Current media: <a href="${episode.audioUrl}" target="_blank">Listen</a></p>`
            : '<p style="font-size: 0.8em; margin-top: 5px;">No current media file.</p>'
      }
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
popup.querySelector("#cancel-episode-update").addEventListener("click", () => {
  document.body.removeChild(popup);
});

// Update episode form submission
popup.querySelector("#update-episode-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const formData = new FormData(form);

  // Validation functions
  const validateTitle = (title) => {
    if (title && (title.trim().length < 2 || title.length > 200)) {
      return "Title must be between 2 and 200 characters if provided";
    }
    return null;
  };

  const validateDescription = (desc) => {
    if (desc && desc.length > 4000) {
      return "Description cannot exceed 4000 characters";
    }
    return null;
  };

  const validateSummary = (summary) => {
    if (summary && summary.length > 1000) {
      return "Summary cannot exceed 1000 characters";
    }
    return null;
  };

  const validateAuthor = (author) => {
    if (author && !/^[A-Za-z\s\-\.]{1,100}$/.test(author)) {
      return "Author name can only contain letters, spaces, hyphens, and periods (max 100 characters)";
    }
    return null;
  };

  const validateDate = (dateStr, fieldName) => {
    if (dateStr) {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) {
        return `Invalid ${fieldName} date`;
      }
    }
    return null;
  };

  const validateSeason = (season) => {
    if (season) {
      const num = parseInt(season);
      if (isNaN(num) || num < 0 || num > 100) {
        return "Season must be a number between 0 and 100 if provided";
      }
    }
    return null;
  };

  const validateEpisode = (episodeNum) => {
    if (episodeNum) {
      const num = parseInt(episodeNum);
      if (isNaN(num) || num < 0 || num > 1000) {
        return "Episode number must be a number between 0 and 1000 if provided";
      }
    }
    return null;
  };

  const validateAudioFile = (file) => {
    // Skip validation if no file is provided or audio upload is disabled
    if (!file || file.size === 0 || isAudioUploadDisabled) {
      return null;
    }
    const validTypes = ['audio/mp3', 'audio/wav', 'audio/mpeg', 'video/mp4'];
    if (!validTypes.includes(file.type)) {
      return "Media is not a valid file type. (Allowed types: mp3, wav, mpeg, mp4)";
    }
    const maxSize = 500 * 1024 * 1024; // 500MB
    if (file.size > maxSize) {
      return "Media file size cannot exceed 500MB";
    }
    return null;
  };

  // Perform validations
  const titleError = validateTitle(formData.get("title"));
  if (titleError) {
    showNotification("Invalid Title", titleError, "error");
    return;
  }

  const descriptionError = validateDescription(formData.get("description"));
  if (descriptionError) {
    showNotification("Invalid Description", descriptionError, "error");
    return;
  }

  const summaryError = validateSummary(formData.get("summary"));
  if (summaryError) {
    showNotification("Invalid Summary", summaryError, "error");
    return;
  }

  const authorError = validateAuthor(formData.get("author"));
  if (authorError) {
    showNotification("Invalid Author", authorError, "error");
    return;
  }

  const publishDateError = validateDate(formData.get("publishDate"), "Publish");
  if (publishDateError) {
    showNotification("Invalid Date", publishDateError, "error");
    return;
  }

  const recordingDateError = validateDate(formData.get("recordingAt"), "Recording");
  if (recordingDateError) {
    showNotification("Invalid Date", recordingDateError, "error");
    return;
  }

  const seasonError = validateSeason(formData.get("season"));
  if (seasonError) {
    showNotification("Invalid Season", seasonError, "error");
    return;
  }

  const episodeError = validateEpisode(formData.get("episode"));
  if (episodeError) {
    showNotification("Invalid Episode Number", episodeError, "error");
    return;
  }

  const audioFileError = validateAudioFile(formData.get("audioFile"));
  if (audioFileError) {
    showNotification("Invalid Audio File", audioFileError, "error");
    return;
  }

  const status = formData.get("status");
  if (status && !["Not Recorded", "Published", "Recorded", "Edited", "Not Scheduled"].includes(status)) {
    showNotification("Invalid Status", "Please select a valid status if provided", "error");
    return;
  }

  const episodeType = formData.get("episodeType");
  if (episodeType && !["full", "trailer", "bonus"].includes(episodeType)) {
    showNotification("Invalid Episode Type", "Please select a valid episode type if provided", "error");
    return;
  }

  const explicitValue = formData.get("explicit");
  if (explicitValue && !["true", "false"].includes(explicitValue)) {
    showNotification("Invalid Explicit Content", "Please select a valid explicit content option if provided", "error");
    return;
  }

  // Process form data
  const durationMinutes = formData.get("duration_minutes");
  if (durationMinutes) {
    const durationSeconds = Math.round(parseFloat(durationMinutes) * 60);
    if (durationSeconds < 0 || isNaN(durationSeconds)) {
      showNotification("Invalid Duration", "Please provide a non-negative number if provided", "error");
      return;
    }
    formData.set("duration", durationSeconds.toString());
  }
  formData.delete("duration_minutes");

  const season = formData.get("season");
  formData.delete("season");
  if (season) {
    formData.set("season", parseInt(season).toString());
  }

  const episodeNumber = formData.get("episode");
  formData.delete("episode");
  if (episodeNumber) {
    formData.set("episode", parseInt(episodeNumber).toString());
  }

  const recordingAt = formData.get("recordingAt");
  formData.delete("recordingAt");
  if (recordingAt) {
    formData.set("recordingAt", new Date(recordingAt).toISOString());
  }

  const publishDate = formData.get("publishDate");
  formData.delete("publishDate");
  if (publishDate) {
    formData.set("publishDate", new Date(publishDate).toISOString());
  }

  if (explicitValue) {
    formData.set("explicit", explicitValue === "true");
  } else {
    formData.delete("explicit");
  }

  if (isAudioUploadDisabled || !formData.get("audioFile") || formData.get("audioFile").size === 0) {
    formData.delete("audioFile");
  }

  // Remove empty or null values
  for (const [key, value] of formData.entries()) {
    if (value === "" || value === null || value === undefined) {
      formData.delete(key);
    }
  }

  const submitButton = form.querySelector("button[type='submit']");
  submitButton.disabled = true;
  submitButton.textContent = "Updating...";

  try {
    const result = await updateEpisode(episode._id, formData);
    if (result.message) {
      showNotification("Success", "Episode updated successfully!", "success");
      document.body.removeChild(popup);
      const updatedEpisodeData = await fetchEpisode(episode._id);
      renderEpisodeDetail(updatedEpisodeData);
    } else {
      showNotification("Error", result.error || "Update failed", "error");
    }
  } catch (error) {
    showNotification("Error", `Failed to update episode: ${error.message || error}`, "error");
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Update Episode";
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

  // Episode form submission - DENNA ÄR KORREKT OCH HAR LOGIK FÖR ATT FÖRHINDRA DUBBELINLÄMNING
  document
    .getElementById("create-episode-form")
    .addEventListener("submit", async (e) => {
      e.preventDefault();

      // Förhindra dubbelinlämning
      const submitButton = e.target.querySelector("button[type='submit']");
      if (submitButton.disabled) return; // Om knappen redan är inaktiverad, avbryt

      submitButton.disabled = true; // Inaktivera knappen för att förhindra dubbelinlämning

      try {
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());

        // Ensure recordingAt is in the correct format
        if (data.recordingAt === "") {
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
        if (!data.podcastId || !data.title ) {
          showNotification(
            "Missing Fields",
            "Please fill in all required fields.",
            "error"
          );
          return;
        }

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
          // Visa popup för episodgräns om det är felet
          if (result.error === "Episode limit reached") {
            showEpisodeLimitPopup();
          } else {
            showNotification("Error", result.error, "error");
          }
        }
      } catch (error) {
        console.error("Error creating episode:", error);
        // Kontrollera om felet är specifikt för episodgränsen
        if (error.message === "Episode limit reached") {
          showEpisodeLimitPopup();
        } else {
          showNotification("Error", "Failed to create episode.", "error");
        }
      } finally {
        submitButton.disabled = false; // Återaktivera knappen efter att processen är klar
      }
    });

  // Funktion för att visa popup när episodgränsen nås
  async function showEpisodeLimitPopup() {
    const popup = document.getElementById("episode-limit-popup");
    popup.style.display = "flex";

    // Close popup
    document
      .getElementById("close-limit-popup")
      .addEventListener("click", () => {
        popup.style.display = "none";
      });

    const credits_button = document.getElementById("buy-credits-btn-popup");
    // Set the button content with only the unlocked lock icon
    credits_button.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;">
        <rect width="18" height="11" x="3" y="11" rx="2" ry="2"></rect>
        <path d="M7 11V7a5 5 0 0 1 9.9-1"></path>
      </svg>
      Unlock for 5,000 credits
    `;

    // Navigate to store
    credits_button
      .addEventListener("click", async () => {
        const credits = await getCredits();
        const extra_episode_cost = 5000;
        if (credits >= extra_episode_cost) {
          try {
            await consumeStoreCredits("episode_pack");
            const updateData = {
              'unlockedExtraEpisodeSlots': 1 // Increment the extra episode slots by 1
            };
            incrementUpdateAccount(updateData);

            showNotification(
              "Success",
              "Increased episode slots!",
              "success"
            );

            popup.style.display = "none";
          } catch (error) {
            console.log(error);
          }
        } else {
          window.location.href = "/store";
        }
      });
  }
}

