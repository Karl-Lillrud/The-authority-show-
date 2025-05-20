import {
  fetchGuestsRequest,
  addGuestRequest,
  deleteGuestRequest
} from "../../../static/requests/guestRequests.js";
import {
  fetchEpisodesByPodcast,
  fetchEpisode
} from "../../../static/requests/episodeRequest.js";
import { fetchPodcasts } from "../../../static/requests/podcastRequests.js";
import {
  updateEditButtons,
  shared
} from "./podcastmanagement.js";
import { renderEpisodeDetail } from "./episode-functions.js";
import { showNotification } from "../components/notifications.js";

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
      <div class="field-group full-width">
        <label for="manual-guest-calendar">Google Calendar Event Link (Optional)</label>
        <input type="url" id="manual-guest-calendar" name="guestCalendar" placeholder="Enter Google Calendar event link (optional)" />
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

  // Manual guest form submission
  popup
    .querySelector("#manual-guest-form")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      const guestName = document.getElementById("manual-guest-name").value.trim();
      const guestEmail = document.getElementById("manual-guest-email").value.trim();
      const guestCalendar = document.getElementById("manual-guest-calendar").value.trim();
      const podcastId =
        shared.selectedPodcastId ||
        document.getElementById("podcast-select")?.value;

      console.log("Guest Name:", guestName);
      console.log("Guest Email:", guestEmail);
      console.log("Google Calendar Link:", guestCalendar || "Not provided");
      console.log("Podcast ID:", podcastId);

      if (guestName && guestEmail && podcastId) {
        try {
          const guestData = {
            name: guestName,
            email: guestEmail,
            podcastId,
            calendarLink: guestCalendar || null, // Include optional calendar link
          };

          const guest = await addGuestRequest(guestData);

          if (guest && guest.message === "Guest added successfully") {
            document.body.removeChild(popup);
            await renderGuestSelection(selectElement, guest.guest_id);
            showNotification("Success", "Guest added successfully!", "success");
          } else {
            showNotification(
              "Error",
              guest.error || "Failed to add guest.",
              "error"
            );
          }
        } catch (error) {
          console.error("Error adding guest:", error);
          showNotification("Error", "Failed to add guest.", "error");
        }
      } else {
        showNotification(
          "Error",
          "Please fill in all required fields (Name, Email, Podcast).",
          "error"
        );
      }
    });
}

async function showAddGuestPopup() {
  console.log("%c[guest-functions.js] showAddGuestPopup() CALLED.", "color: blue; font-weight: bold;");
  const popup = document.getElementById("guest-popup");

  if (!popup) {
    console.error("[guest-functions.js] #guest-popup element NOT FOUND.");
    return;
  }

  // Ensure the popup has the 'popup' class if it was removed during debugging.
  if (!popup.classList.contains("popup")) {
    popup.classList.add("popup");
  }
  
  // Ensure popup is a direct child of body (it might have been moved during debugging)
  // This is generally good practice for fixed position popups.
  if (popup.parentElement !== document.body) {
    console.log("[guest-functions.js] #guest-popup is not a direct child of document.body. Moving it.");
    document.body.appendChild(popup); 
  }

  // Make the popup visible
  popup.style.display = "flex"; 
  // The CSS transitions for opacity and transform will handle the smooth appearance.

  console.log("[guest-functions.js] #guest-popup display set to flex.");

  // Restore original logic to populate dropdowns
  try {
    console.log("[guest-functions.js] Starting to populate dropdowns...");
    const podcastSelect = document.getElementById("podcast-select-guest");
    const episodeSelect = document.getElementById("episode-id");

    if (!podcastSelect || !episodeSelect) {
      console.error("[guest-functions.js] Podcast or Episode select element not found in guest popup.");
      showNotification("Error", "Guest popup form is incomplete.", "error");
      closeAddGuestPopup(); 
      return;
    }

    podcastSelect.innerHTML = '<option value="">Loading Podcasts...</option>';
    episodeSelect.innerHTML = '<option value="">Select Podcast First</option>';
    episodeSelect.disabled = true;

    const podcastData = await fetchPodcasts();
    if (podcastData && podcastData.podcast && podcastData.podcast.length > 0) {
      podcastSelect.innerHTML = '<option value="">Select Podcast</option>'; 
      podcastData.podcast.forEach((podcast) => {
        const option = document.createElement("option");
        option.value = podcast._id;
        option.textContent = podcast.podName;
        podcastSelect.appendChild(option);
      });

      if (shared.selectedPodcastId) {
        podcastSelect.value = shared.selectedPodcastId;
        await loadEpisodesForPodcast(shared.selectedPodcastId, episodeSelect);
      }
    } else {
      podcastSelect.innerHTML = '<option value="">No Podcasts Found</option>';
      showNotification("Info", "No podcasts available to assign guest.", "info");
    }

    // Remove previous listener to avoid duplicates if popup is opened multiple times
    podcastSelect.removeEventListener("change", handlePodcastSelectChange);
    podcastSelect.addEventListener("change", handlePodcastSelectChange);

  } catch (error) {
    console.error("[guest-functions.js] Error populating dropdowns in guest popup:", error);
    showNotification("Error", "Could not load data for guest form.", "error");
  }
  console.log("%c[guest-functions.js] showAddGuestPopup() COMPLETED.", "color: blue; font-weight: bold;");
}

// Event handler for podcast select change, to be properly managed
async function handlePodcastSelectChange(event) {
    const episodeSelect = document.getElementById("episode-id");
    const selectedPodcastId = event.target.value;
    if (selectedPodcastId) {
        await loadEpisodesForPodcast(selectedPodcastId, episodeSelect);
    } else {
        episodeSelect.innerHTML = '<option value="">Select Podcast First</option>';
        episodeSelect.disabled = true;
    }
}

async function loadEpisodesForPodcast(podcastId, episodeSelectElement) {
  if (!podcastId || !episodeSelectElement) return;

  episodeSelectElement.innerHTML = '<option value="">Loading Episodes...</option>';
  episodeSelectElement.disabled = true;
  try {
    const episodes = await fetchEpisodesByPodcast(podcastId);
    if (episodes && episodes.length > 0) {
      // Sort episodes by created_at or createdAt (handle both cases)
      episodes.sort((a, b) => {
        const dateA = new Date(a.created_at || a.createdAt);
        const dateB = new Date(b.created_at || b.createdAt);
        return dateB - dateA; // Sort in descending order (newest first)
      });

      episodeSelectElement.innerHTML = '<option value="">Select Episode</option>';
      episodes.forEach((episode) => {
        const option = document.createElement("option");
        option.value = episode._id;
        option.textContent = episode.title;
        // Apply styling based on status
        if (episode.status && episode.status.toLowerCase() !== "published") {
          option.style.color = "inherit"; // Ensure non-published episodes are not greyed out
        } else {
          option.style.color = "#888"; // Grey out published episodes (optional, adjust as needed)
        }
        episodeSelectElement.appendChild(option);
      });
      episodeSelectElement.disabled = false;
    } else {
      episodeSelectElement.innerHTML = '<option value="">No Episodes Found for this Podcast</option>';
      episodeSelectElement.disabled = true;
    }
  } catch (error) {
    console.error(`[guest-functions.js] Error fetching episodes for podcast ${podcastId}:`, error);
    episodeSelectElement.innerHTML = '<option value="">Error Loading Episodes</option>';
    episodeSelectElement.disabled = true;
    showNotification("Error", "Could not load episodes.", "error");
  }
}


// Function to close the Add Guest popup
function closeAddGuestPopup() {
  const popup = document.getElementById("guest-popup");
  if (popup) {
    popup.style.display = "none";
    console.log("[guest-functions.js] #guest-popup display set to none.");

    const addGuestForm = document.getElementById("add-guest-form");
    if (addGuestForm) {
      addGuestForm.reset(); 
      const podcastSelect = document.getElementById("podcast-select-guest");
      const episodeSelect = document.getElementById("episode-id");
      if (podcastSelect) {
        podcastSelect.selectedIndex = 0;
      }
      if (episodeSelect) {
        episodeSelect.innerHTML = '<option value="">Select Podcast First</option>';
        episodeSelect.disabled = true;
      }
       console.log("[guest-functions.js] #add-guest-form reset.");
    }
  } else {
    console.error("[guest-functions.js] #guest-popup not found during close.");
  }
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
  <button class="delete-btn" id="delete-guest-btn" data-id="${guest.id}">
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
  document.getElementById("delete-guest-btn").addEventListener("click", async () => {
    if (confirm("Are you sure you want to delete this guest?")) {
      try {
        const response = await deleteGuestRequest(guest.id);
        if (response && response.message === "Guest deleted successfully") {
          console.log("Guest deleted:", guest.id);
          showNotification("Success", "Guest deleted successfully!", "success");
          // Optionally, refresh the guest list or navigate away
        } else {
          console.error("Failed to delete guest:", response.error || "Unknown error");
          showNotification("Error", response.error || "Failed to delete guest.", "error");
        }
      } catch (error) {
        console.error("Error deleting guest:", error);
        showNotification("Error", "An error occurred while deleting the guest.", "error");
      }
    }
  });
}

// Initialize guest functions
export function initGuestFunctions() {
  console.log("[guest-functions.js] initGuestFunctions() called.");

  const addGuestBtn = document.getElementById("add-guest-btn");
  if (addGuestBtn) {
    console.log("[guest-functions.js] #add-guest-btn found. Attaching listener.");
    // Remove existing listener before adding, to prevent duplicates if init is called multiple times
    addGuestBtn.removeEventListener("click", showAddGuestPopup); 
    addGuestBtn.addEventListener("click", showAddGuestPopup);
  } else {
    console.error("[guest-functions.js] #add-guest-btn not found.");
  }

  const closeGuestPopupBtn = document.getElementById("close-guest-popup");
  if (closeGuestPopupBtn) {
    console.log("[guest-functions.js] #close-guest-popup found. Attaching listener.");
    closeGuestPopupBtn.removeEventListener("click", closeAddGuestPopup);
    closeGuestPopupBtn.addEventListener("click", closeAddGuestPopup);
  } else {
    console.error("[guest-functions.js] #close-guest-popup not found.");
  }

  const cancelGuestBtn = document.getElementById("cancel-guest-btn");
  if (cancelGuestBtn) {
    console.log("[guest-functions.js] #cancel-guest-btn found. Attaching listener.");
    cancelGuestBtn.removeEventListener("click", closeAddGuestPopup);
    cancelGuestBtn.addEventListener("click", closeAddGuestPopup);
  } else {
    console.error("[guest-functions.js] #cancel-guest-btn not found.");
  }

  const addGuestForm = document.getElementById("add-guest-form");
  if (addGuestForm) {
    console.log("[guest-functions.js] #add-guest-form found. Setting up submit handler.");
    const handleFormSubmit = async (e) => {
      e.preventDefault();
      console.log("[guest-functions.js] Add Guest form submitted.");
      const episodeId = document.getElementById("episode-id").value.trim();
      const guestName = document.getElementById("guest-name").value.trim();
      const guestDescription = document.getElementById("guest-description").value.trim();
      const guestAreas = document.getElementById("guest-areas").value.split(",").map((area) => area.trim()).filter(Boolean);
      const guestEmail = document.getElementById("guest-email").value.trim();

      if (guestName && guestEmail && episodeId) {
        try {
          const guest = await addGuestRequest({
            episodeId,
            name: guestName,
            description: guestDescription,
            areasOfInterest: guestAreas,
            email: guestEmail,
          });
          if (guest.error) {
            showNotification("Error", guest.error, "error");
            return;
          }
          closeAddGuestPopup();
          showNotification("Success", "Guest added successfully!", "success");
          if (shared.selectedPodcastId && episodeId) { 
            renderEpisodeDetail({ _id: episodeId, podcast_id: shared.selectedPodcastId });
            setTimeout(() => {
              const guestsSection = document.querySelector(".podcast-about-section h2.section-title");
              if (guestsSection) {
                guestsSection.scrollIntoView({ behavior: "smooth" });
              }
            }, 500);
          } else {
            console.warn("[guest-functions.js] Cannot refresh episode detail, selectedPodcastId or episodeId missing.");
            // Attempt to refresh the main podcast list or dashboard as a fallback if appropriate
          }
        } catch (error) {
          console.error("[guest-functions.js] Error during addGuestRequest or subsequent actions:", error);
          showNotification("Error", "Failed to add guest due to an unexpected error.", "error");
        }
      } else {
        showNotification("Validation Error", "Please fill in all required fields (Guest Name, Email, and select an Episode).", "warning");
      }
    };
    
    if (addGuestForm._submitHandler) {
        addGuestForm.removeEventListener("submit", addGuestForm._submitHandler);
        console.log("[guest-functions.js] Removed old submit handler from #add-guest-form.");
    }
    addGuestForm._submitHandler = handleFormSubmit; 
    addGuestForm.addEventListener("submit", addGuestForm._submitHandler);
    console.log("[guest-functions.js] Attached new submit handler to #add-guest-form.");

  } else {
    console.error("[guest-functions.js] #add-guest-form not found.");
  }
}
