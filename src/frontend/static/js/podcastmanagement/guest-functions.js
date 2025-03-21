import {
  fetchGuestsRequest,
  addGuestRequest
} from "../../../static/requests/guestRequests.js";
import { fetchEpisodesByPodcast } from "../../../static/requests/episodeRequest.js";
import { fetchPodcasts } from "../../../static/requests/podcastRequests.js";
import {
  showNotification,
  updateEditButtons,
  shared
} from "./podcastmanagement.js";
import { renderEpisodeDetail } from "./episode-functions.js";

/// New function to fetch and render guest options into a select element
export async function renderGuestSelection(
  selectElement,
  selectedGuestId = ""
) {
  try {
    const guests = await fetchGuestsRequest(); // Use guestRequests for fetching guests
    selectElement.innerHTML = "";
    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = "Select Guest"; // Changed text
    selectElement.appendChild(defaultOption);
    guests.forEach((guest) => {
      const option = document.createElement("option");
      option.value = guest.id || guest._id;
      option.textContent = guest.name;
      if ((guest.id || guest._id) === selectedGuestId) {
        option.selected = true;
      }
      selectElement.appendChild(option);
    });
    // Remove any existing manual guest button if present
    let manualField = selectElement.parentElement.querySelector(
      ".manual-guest-field"
    );
    if (manualField) {
      manualField.remove();
    }
    // Append a separate field below the dropdown for manual guest entry.
    manualField = document.createElement("div");
    manualField.className = "manual-guest-field";
    manualField.innerHTML = `
    <label for="manual-guest">Add Guest Manually</label>
    <input type="text" id="manual-guest" placeholder="Click to add guest manually" readonly />
  `;
    // Append the field after the select element.
    selectElement.parentElement.appendChild(manualField);
    manualField.addEventListener("click", () => {
      showManualGuestPopup(selectElement);
    });
  } catch (error) {
    console.error("Error fetching guests:", error);
  }
}

function showManualGuestPopup(selectElement) {
  const popup = document.createElement("div");
  popup.className = "popup";
  popup.style.display = "flex";

  const popupContent = document.createElement("div");
  popupContent.className = "form-box";
  popupContent.innerHTML = `
  <span id="close-manual-guest-popup" class="close-btn">&times;</span>
  <h2 class="form-title">Add Guest Manually</h2>
  <form id="manual-guest-form">
    <div class="field-group full-width">
      <label for="manual-guest-name">Guest Name</label>
      <input type="text" id="manual-guest-name" name="guestName" required />
    </div>
    <div class="field-group full-width">
      <label for="manual-guest-email">Guest Email</label>
      <input type="email" id="manual-guest-email" name="guestEmail" required />
    </div>
    <div class="form-actions">
      <button type="button" id="cancel-manual-guest" class="cancel-btn">Cancel</button>
      <button type="submit" class="save-btn">Add Guest</button>
    </div>
  </form>
`;
  popup.appendChild(popupContent);
  document.body.appendChild(popup);

  // Close popup events
  popup
    .querySelector("#close-manual-guest-popup")
    .addEventListener("click", () => {
      document.body.removeChild(popup);
    });
  popup.querySelector("#cancel-manual-guest").addEventListener("click", () => {
    document.body.removeChild(popup);
  });

  // Manual guest form submission using addGuestRequest
  popup
    .querySelector("#manual-guest-form")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      const guestName = document
        .getElementById("manual-guest-name")
        .value.trim();
      const guestEmail = document
        .getElementById("manual-guest-email")
        .value.trim();
      const podcastId =
        shared.selectedPodcastId ||
        document.getElementById("podcast-select")?.value; // Use selectedPodcastId if available

      console.log("Guest Name:", guestName); // Log guest name
      console.log("Guest Email:", guestEmail); // Log guest email
      console.log("Podcast ID:", podcastId); // Log podcast ID

      if (guestName && guestEmail && podcastId) {
        try {
          const guest = await addGuestRequest({
            name: guestName,
            email: guestEmail,
            podcastId
          });
          document.body.removeChild(popup);
          // Fetch and render the updated guest list
          await renderGuestSelection(selectElement, guest.guest_id);
          showNotification("Success", "Guest added successfully!", "success"); // Show success notification
        } catch (error) {
          console.error("Error adding guest:", error);
          showNotification("Error", "Failed to add guest.", "error"); // Show error notification
        }
      } else {
        alert("Please fill in all required fields.");
      }
    });
}

// Updated showAddGuestPopup function to clear the episode dropdown before populating
async function showAddGuestPopup() {
  const popup = document.getElementById("guest-popup");
  popup.style.display = "flex";

  // Populate the Podcast selection dropdown
  const podcastSelect = document.getElementById("podcast-select-guest");
  podcastSelect.innerHTML = "";
  try {
    const response = await fetchPodcasts();
    const podcasts = response.podcast;
    podcasts.forEach((podcast) => {
      const opt = document.createElement("option");
      opt.value = podcast._id;
      opt.textContent = podcast.podName;
      podcastSelect.appendChild(opt);
    });
  } catch (error) {
    console.error("Error fetching podcasts:", error);
  }

  // Remove existing event listener before adding a new one
  const episodeSelect = document.getElementById("episode-id");
  const newPodcastSelect = podcastSelect.cloneNode(true);
  podcastSelect.parentNode.replaceChild(newPodcastSelect, podcastSelect);

  // When a podcast is selected, fetch episodes for that podcast using fetchEpisodesByPodcast
  newPodcastSelect.addEventListener("change", async () => {
    const selectedPodcast = newPodcastSelect.value;
    episodeSelect.innerHTML = ""; // Clear the dropdown before populating
    try {
      const episodes = await fetchEpisodesByPodcast(selectedPodcast);
      episodes.forEach((episode) => {
        const option = document.createElement("option");
        option.value = episode._id;
        option.textContent = episode.title;
        episodeSelect.appendChild(option);
      });
    } catch (error) {
      console.error("Error fetching episodes for podcast:", error);
    }
  });
  // Trigger the change event to populate episodes initially
  newPodcastSelect.dispatchEvent(new Event("change"));
}

// Function to close the Add Guest popup
function closeAddGuestPopup() {
  const popup = document.getElementById("guest-popup");
  popup.style.display = "none";
}

// Function to render guest detail
export function renderGuestDetail(guest) {
  const guestDetailElement = document.getElementById("podcast-detail");

  // Get initials from guest name for avatar
  const initials = guest.name
    .split(" ")
    .map((word) => word[0])
    .join("")
    .substring(0, 2)
    .toUpperCase();

  guestDetailElement.innerHTML = `
  <div class="detail-header">
    <button class="back-btn" id="back-to-episode">
      ${shared.svgpodcastmanagement.back}
      Back to episode
    </button>
    
    <!-- Add top-right action buttons -->
    <div class="top-right-actions">
      <button class="action-btn edit-btn" id="edit-guest-btn" data-id="${
        guest._id || guest.id
      }">
        ${shared.svgpodcastmanagement.edit}
      </button>
    </div>
  </div>
  <div class="detail-content">
    <div class="detail-info">
      <div class="guest-detail-header">
        <div class="guest-detail-avatar">${initials}</div>
        <div class="guest-detail-info">
          <h1 class="guest-detail-name">${guest.name}</h1>
          <p class="guest-detail-email">${
            guest.email || "No email provided"
          }</p>
        </div>
      </div>
      
      <div class="detail-section">
        <h2>About</h2>
        <p>${guest.bio || guest.description || "No bio available."}</p>
      </div>
      
      <div class="separator"></div>
      
      <div class="guest-detail-section">
        <h3>Contact Information</h3>
        <div class="detail-grid">
          <div class="detail-item">
            <h4>Email</h4>
            <p><a href="mailto:${guest.email}" class="guest-email-link">${
    guest.email
  }</a></p>
          </div>
          ${
            guest.phone
              ? `
          <div class="detail-item">
            <h4>Phone</h4>
            <p>${guest.phone}</p>
          </div>
          `
              : ""
          }
        </div>
      </div>
      
      <div class="separator"></div>
      
      <div class="guest-detail-section">
        <h3>Social Media</h3>
        <div>
          ${
            guest.linkedin
              ? `
          <a href="${guest.linkedin}" target="_blank" class="guest-social-link">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path>
              <rect x="2" y="9" width="4" height="12"></rect>
              <circle cx="4" cy="4" r="2"></circle>
            </svg>
            LinkedIn Profile
          </a>
          `
              : ""
          }
          
          ${
            guest.twitter
              ? `
          <a href="${guest.twitter}" target="_blank" class="guest-social-link">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z"></path>
            </svg>
            Twitter Profile
          </a>
          `
              : ""
          }
          
          ${
            !guest.linkedin && !guest.twitter
              ? "<p>No social media profiles available.</p>"
              : ""
          }
        </div>
      </div>
      
      ${
        guest.areasOfInterest && guest.areasOfInterest.length
          ? `
      <div class="separator"></div>
      <div class="guest-detail-section">
        <h3>Areas of Interest</h3>
        <div class="guest-tags">
          ${guest.areasOfInterest
            .map((area) => `<span class="guest-tag">${area}</span>`)
            .join("")}
        </div>
      </div>
      `
          : ""
      }
      
      ${
        guest.tags && guest.tags.length
          ? `
      <div class="separator"></div>
      <div class="guest-detail-section">
        <h3>Tags</h3>
        <div class="guest-tags">
          ${guest.tags
            .map((tag) => `<span class="guest-tag">${tag}</span>`)
            .join("")}
        </div>
      </div>
      `
          : ""
      }
    </div>
  </div>
`;

  // Back button event listener
  document.getElementById("back-to-episode").addEventListener("click", () => {
    fetch(`/get_episodes/${guest.episodeId}`)
      .then((response) => response.json())
      .then((episode) => {
        renderEpisodeDetail(episode);
      })
      .catch((error) => {
        console.error("Error fetching episode:", error);
        showNotification("Error", "Failed to return to episode view", "error");
      });
  });

  // Add event listeners for the edit guest button
  document
    .getElementById("edit-guest-btn")
    .addEventListener("click", async () => {
      try {
        // Implement guest editing functionality here
        showNotification(
          "Info",
          "Guest editing functionality coming soon",
          "info"
        );
      } catch (error) {
        showNotification("Error", "Failed to edit guest", "error");
      }
    });

  // Update edit buttons after rendering
  updateEditButtons();
}

// Initialize guest functions
export function initGuestFunctions() {
  // Event listener for Add Guest button
  document
    .getElementById("add-guest-btn")
    .addEventListener("click", showAddGuestPopup);

  // Event listener for closing the Add Guest popup
  document
    .getElementById("close-guest-popup")
    .addEventListener("click", closeAddGuestPopup);

  // Event listener for cancel button in Add Guest form
  document
    .getElementById("cancel-guest-btn")
    .addEventListener("click", closeAddGuestPopup);

  // Event listener for Add Guest form submission
  document
    .getElementById("add-guest-form")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      const episodeId = document.getElementById("episode-id").value.trim();
      const guestName = document.getElementById("guest-name").value.trim();
      const guestDescription = document
        .getElementById("guest-description")
        .value.trim();
      const guestTags = document
        .getElementById("guest-tags")
        .value.split(",")
        .map((tag) => tag.trim())
        .filter(Boolean);
      const guestAreas = document
        .getElementById("guest-areas")
        .value.split(",")
        .map((area) => area.trim())
        .filter(Boolean);
      const guestEmail = document.getElementById("guest-email").value.trim();
      const guestLinkedIn = document
        .getElementById("guest-linkedin")
        .value.trim();
      const guestTwitter = document
        .getElementById("guest-twitter")
        .value.trim();

      if (guestName && guestEmail && episodeId) {
        try {
          const guest = await addGuestRequest({
            episodeId, // Ensure episodeId is correctly set
            name: guestName,
            description: guestDescription,
            tags: guestTags,
            areasOfInterest: guestAreas,
            email: guestEmail,
            linkedin: guestLinkedIn,
            twitter: guestTwitter
          });
          closeAddGuestPopup();
          showNotification("Success", "Guest added successfully!", "success");
          // Refresh the guest list in episode details without refreshing the page
          renderEpisodeDetail({
            _id: episodeId,
            podcast_id: shared.selectedPodcastId
          });
        } catch (error) {
          console.error("Error adding guest:", error);
          showNotification("Error", "Failed to add guest.", "error");
        }
      } else {
        alert("Please fill in all required fields.");
      }
    });
}

export async function fetchGuestsByEpisode(episodeId) {
  try {
    const response = await fetch(`/get_guests_by_episode/${episodeId}`);
    if (!response.ok) {
      throw new Error("Failed to fetch guests");
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching guests:", error);
    throw error;
  }
}
