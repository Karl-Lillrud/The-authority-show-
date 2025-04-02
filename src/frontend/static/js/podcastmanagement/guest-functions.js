import {
  fetchGuestsRequest,
  addGuestRequest
} from "../../../static/requests/guestRequests.js";
import {
  fetchEpisodesByPodcast,
  fetchEpisode
} from "../../../static/requests/episodeRequest.js";
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
        // Replace alert with showNotification
        showNotification(
          "Error",
          "Please fill in all required fields.",
          "error"
        );
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

  guestDetailElement.innerHTML = `
<div class="detail-header">
  <button class="back-btn" id="back-to-episode">
    ${shared.svgpodcastmanagement.back}
    Back to episode
  </button>
  <div class="top-right-actions">
    <button class="action-btn edit-btn" id="edit-guest-btn" data-id="${
      guest._id
    }">
      ${shared.svgpodcastmanagement.edit}
    </button>
  </div>
</div>

<div class="podcast-detail-container">
  <!-- Header section with image and basic info -->
  <div class="podcast-header-section">
    <div class="podcast-image-container">
      <div class="detail-image" style="background-image: url('${
        guest.image || "default-guest-image.png"
      }')"></div>
    </div>
    <div class="podcast-basic-info">
      <h1 class="detail-title">${guest.name}</h1>
      <p class="detail-category">${guest.role || "Guest"}</p>
      <div class="podcast-meta-info">
        <div class="meta-item">
          <span class="meta-label">Email:</span>
          <span class="meta-value">${guest.email || "Not specified"}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Phone:</span>
          <span class="meta-value">${guest.phone || "Not specified"}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Company:</span>
          <span class="meta-value">${guest.company || "Not specified"}</span>
        </div>
      </div>
    </div>
  </div>
  
  <!-- About section -->
  <div class="podcast-about-section">
    <h2 class="section-title">About</h2>
    <p class="podcast-description">${guest.bio || "No bio available."}</p>
  </div>
  
  <!-- Social media section -->
  <div class="podcast-social-section">
    <h2 class="section-title">Social Media</h2>
    <div class="social-links">
      ${
        guest.socialMedia?.twitter
          ? `<a href="${guest.socialMedia.twitter}" target="_blank" class="social-link">
              ${shared.svgpodcastmanagement.twitter} Twitter
            </a>`
          : ""
      }
      ${
        guest.socialMedia?.linkedin
          ? `<a href="${guest.socialMedia.linkedin}" target="_blank" class="social-link">
              ${shared.svgpodcastmanagement.linkedin} LinkedIn
            </a>`
          : ""
      }
      ${
        guest.socialMedia?.instagram
          ? `<a href="${guest.socialMedia.instagram}" target="_blank" class="social-link">
              ${shared.svgpodcastmanagement.instagram} Instagram
            </a>`
          : ""
      }
    </div>
  </div>
</div>

<div class="detail-actions">
  <button class="delete-btn" id="delete-guest-btn" data-id="${guest._id}">
    ${shared.svgpodcastmanagement.delete} Delete Guest
  </button>
</div>
`;

  // Back button event listener
  document
    .getElementById("back-to-episode")
    .addEventListener("click", async () => {
      const episodeId = shared.selectedEpisodeId || guest.episodeId; // Fallback to guest.episodeId
      if (episodeId) {
        try {
          // Fetch the episode details
          const episodeResponse = await fetchEpisode(episodeId);
          if (episodeResponse) {
            // Fetch episodes for the podcast
            const podcastEpisodes = await fetchEpisodesByPodcast(
              episodeResponse.podcast_id || episodeResponse.podcastId
            );

            // Render the episode details
            renderEpisodeDetail({
              ...episodeResponse,
              episodes: podcastEpisodes // Include episodes in the render
            });
          } else {
            console.error("Failed to fetch episode details.");
            showNotification(
              "Error",
              "Failed to fetch episode details.",
              "error"
            );
          }
        } catch (error) {
          console.error("Error fetching episode details:", error);
          showNotification(
            "Error",
            "Failed to fetch episode details.",
            "error"
          );
        }
      } else {
        console.error(
          "Episode ID is missing. Cannot navigate back to the episode."
        );
        showNotification(
          "Error",
          "Episode ID is missing. Cannot navigate back.",
          "error"
        );
      }
    });

  // Edit button event listener
  document.getElementById("edit-guest-btn").addEventListener("click", () => {
    // Logic to open the guest edit form
    console.log("Edit guest:", guest._id);
  });

  // Delete button event listener
  document.getElementById("delete-guest-btn").addEventListener("click", () => {
    if (confirm("Are you sure you want to delete this guest?")) {
      // Logic to delete the guest
      console.log("Delete guest:", guest._id);
    }
  });
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

          // Navigate to episode details and scroll to the "Guests" section
          renderEpisodeDetail({
            _id: episodeId,
            podcast_id: shared.selectedPodcastId
          });
          setTimeout(() => {
            const guestsSection = document.querySelector(
              ".podcast-about-section h2.section-title"
            );
            if (guestsSection) {
              guestsSection.scrollIntoView({ behavior: "smooth" });
            }
          }, 500);
        } catch (error) {
          console.error("Error adding guest:", error);
          showNotification("Error", "Failed to add guest.", "error");
        }
      } else {
        // Replace alert with notification
        showNotification(
          "Error",
          "Please fill in all required fields.",
          "error"
        );
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
