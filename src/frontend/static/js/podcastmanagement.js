import {
  addPodcast,
  fetchPodcasts,
  fetchPodcast,
  updatePodcast,
  deletePodcast
} from "../requests/podcastRequests.js";
import {
  registerEpisode,
  fetchEpisodesByPodcast
} from "../requests/episodeRequest.js"; // Updated import
import { svgpodcastmanagement } from "../svg/svgpodcastmanagement.js"; // Updated import path
import {
  fetchGuestsRequest,
  addGuestRequest,
  fetchGuestsByEpisode
} from "../requests/guestRequests.js"; // Added import for fetchGuestsByEpisode

console.log("podcastmanagement.js loaded");

// Notification system
function showNotification(title, message, type = "info") {
  // Remove any existing notification
  const existingNotification = document.querySelector(".notification");
  if (existingNotification) {
    existingNotification.remove();
  }

  // Create notification elements
  const notification = document.createElement("div");
  notification.className = `notification ${type}`;

  // Icon based on type
  let iconSvg = "";
  if (type === "success") {
    iconSvg = svgpodcastmanagement.success;
  } else if (type === "error") {
    iconSvg = svgpodcastmanagement.error;
  } else {
    iconSvg = svgpodcastmanagement.defaultIcon;
  }

  notification.innerHTML = `
    <div class="notification-icon">${iconSvg}</div>
    <div class="notification-content">
      <div class="notification-title">${title}</div>
      <div class="notification-message">${message}</div>
    </div>
    <div class="notification-close">
      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="18" y1="6" x2="6" y2="18"></line>
        <line x1="6" y1="6" x2="18" y2="18"></line>
      </svg>
    </div>
  `;

  // Add to DOM
  document.body.appendChild(notification);

  // Add event listener to close button
  notification
    .querySelector(".notification-close")
    .addEventListener("click", () => {
      notification.classList.remove("show");
      setTimeout(() => {
        notification.remove();
      }, 500);
    });

  // Show notification with animation
  setTimeout(() => {
    notification.classList.add("show");
  }, 10);

  // Auto hide after 5 seconds
  setTimeout(() => {
    if (document.body.contains(notification)) {
      notification.classList.remove("show");
      setTimeout(() => {
        if (document.body.contains(notification)) {
          notification.remove();
        }
      }, 500);
    }
  }, 5000);
}

// New function to fetch and render guest options into a select element
async function renderGuestSelection(selectElement, selectedGuestId = "") {
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

let selectedPodcastId = null; // Ensure this variable is declared globally

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
        selectedPodcastId || document.getElementById("podcast-select")?.value; // Use selectedPodcastId if available

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

// Updated showAddGuestPopup function:
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

  // When a podcast is selected, fetch episodes for that podcast using fetchEpisodesByPodcast
  podcastSelect.addEventListener("change", async () => {
    const selectedPodcast = podcastSelect.value;
    const episodeSelect = document.getElementById("episode-id");
    episodeSelect.innerHTML = "";
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
  podcastSelect.dispatchEvent(new Event("change"));
}

// Function to close the Add Guest popup
function closeAddGuestPopup() {
  const popup = document.getElementById("guest-popup");
  popup.style.display = "none";
}

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
    const guestTwitter = document.getElementById("guest-twitter").value.trim();

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
      } catch (error) {
        console.error("Error adding guest:", error);
        showNotification("Error", "Failed to add guest.", "error");
      }
    } else {
      alert("Please fill in all required fields.");
    }
  });

document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM fully loaded and parsed");

  renderPodcastList();

  // Show form for adding a podcast
  document.getElementById("add-podcast-btn").addEventListener("click", () => {
    resetForm();
    selectedPodcastId = null;
    document.getElementById("form-popup").style.display = "flex";
    document.querySelector(".form-title").textContent = "Add New Podcast";
    document.querySelector(".save-btn").textContent = "Save Podcast";
  });

  // Close the form popup
  document.getElementById("close-form-popup").addEventListener("click", () => {
    document.getElementById("form-popup").style.display = "none";
  });

  // Cancel button in form
  document.getElementById("cancel-form-btn").addEventListener("click", () => {
    document.getElementById("form-popup").style.display = "none";
  });

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
        // Populate guest select for the create episode form
        const guestSelect = document.getElementById("guest-id");
        // renderGuestSelection(guestSelect);;
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

  // Episode form submission
  document
    .getElementById("create-episode-form")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      const data = Object.fromEntries(formData.entries());

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
        } else {
          showNotification("Error", result.error, "error");
        }
      } catch (error) {
        console.error("Error creating episode:", error);
        showNotification("Error", "Failed to create episode.", "error");
      }
    });

  // Close popup button
  document.getElementById("close-popup-btn").addEventListener("click", () => {
    document.getElementById("podcasts-popup").style.display = "none";
  });

  // Delete selected podcasts
  document
    .getElementById("delete-selected-podcasts-btn")
    .addEventListener("click", async () => {
      const selectedPodcasts = document.querySelectorAll(
        "#podcasts-list input[type='checkbox']:checked"
      );
      const podcastIds = Array.from(selectedPodcasts).map(
        (checkbox) => checkbox.value
      );

      if (podcastIds.length === 0) {
        showNotification(
          "No Selection",
          "Please select at least one podcast to delete.",
          "info"
        );
        return;
      }

      try {
        for (const podcastId of podcastIds) {
          await deletePodcast(podcastId);
        }
        showNotification(
          "Success",
          "Selected podcasts deleted successfully!",
          "success"
        );
        document.getElementById("podcasts-popup").style.display = "none";
        renderPodcastList();
      } catch (error) {
        showNotification(
          "Error",
          "Failed to delete selected podcasts.",
          "error"
        );
      }
    });
});

const form = document.getElementById("register-podcast-form");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  console.log("Form submitted");

  // Retrieve regular input values
  const podName = document.getElementById("pod-name")?.value.trim() || "";
  const email = document.getElementById("email")?.value.trim() || "";
  const category = document.getElementById("category")?.value.trim() || "";

  if (!podName) {
    showNotification(
      "Missing Field",
      "Please fill in the Podcast Name field.",
      "error"
    );
    return;
  }

  // Build the data object from other form fields
  const data = {
    teamId: "",
    podName,
    ownerName: document.getElementById("pod-owner")?.value.trim() || "",
    hostName: document.getElementById("pod-host")?.value.trim() || "",
    rssFeed: document.getElementById("pod-rss")?.value.trim() || "",
    googleCal: document.getElementById("google-cal")?.value.trim() || null,
    guestUrl: document.getElementById("guest-form-url")?.value.trim() || null,
    email,
    description: document.getElementById("description")?.value.trim() || "",
    // the logoUrl field will be replaced if a logo is uploaded

    category,
    socialMedia: [
      document.getElementById("facebook")?.value.trim(),
      document.getElementById("instagram")?.value.trim(),
      document.getElementById("linkedin")?.value.trim(),
      document.getElementById("twitter")?.value.trim(),
      document.getElementById("tiktok")?.value.trim(),
      document.getElementById("pinterest")?.value.trim()
    ].filter((link) => link)
  };

  // Remove any keys with null or empty values
  Object.keys(data).forEach((key) => {
    if (
      data[key] === null ||
      (Array.isArray(data[key]) && data[key].length === 0) ||
      data[key] === ""
    ) {
      delete data[key];
    }
  });

  // Function to continue submission after processing the logo (if any)
  async function submitPodcast(updatedData) {
    try {
      let responseData;
      if (selectedPodcastId) {
        responseData = await updatePodcast(selectedPodcastId, updatedData);
        if (!responseData.error) {
          showNotification(
            "Success",
            "Podcast updated successfully!",
            "success"
          );
        }
      } else {
        responseData = await addPodcast(updatedData);
        if (!responseData.error) {
          showNotification("Success", "Podcast added successfully!", "success");
        }
      }

      if (responseData.error) {
        showNotification(
          "Error",
          responseData.details
            ? JSON.stringify(responseData.details)
            : responseData.error,
          "error"
        );
      } else {
        document.getElementById("form-popup").style.display = "none";
        document.getElementById("podcast-detail").style.display = "none";
        document.getElementById("podcast-list").style.display = "flex";
        resetForm();
        renderPodcastList();
      }
    } catch (error) {
      console.error("Error:", error);
      showNotification(
        "Error",
        selectedPodcastId
          ? "Failed to update podcast."
          : "Failed to add podcast.",
        "error"
      );
    }
  }

  // Check for a logo file and convert it to a Base64 string if one is selected
  const logoInput = document.getElementById("logo");
  if (logoInput && logoInput.files[0]) {
    const file = logoInput.files[0];
    const reader = new FileReader();
    reader.onloadend = async () => {
      data.logoUrl = reader.result; // update with new image
      await submitPodcast(data);
    };
    reader.readAsDataURL(file);
  } else {
    // If editing and no new image is selected, do not overwrite the existing logoUrl
    if (selectedPodcastId) {
      delete data.logoUrl;
    }
    await submitPodcast(data);
  }
});

function displayPodcastDetails(podcast) {
  // Set form title for editing
  document.querySelector(".form-title").textContent = "Edit Podcast";
  document.querySelector(".save-btn").textContent = "Update Podcast";

  // Fill in form fields
  const podNameEl = document.getElementById("pod-name");
  if (podNameEl) podNameEl.value = podcast.podName || "";

  const podOwnerEl = document.getElementById("pod-owner");
  if (podOwnerEl) podOwnerEl.value = podcast.ownerName || "";

  const podHostEl = document.getElementById("pod-host");
  if (podHostEl) podHostEl.value = podcast.hostName || "";

  const podRssEl = document.getElementById("pod-rss");
  if (podRssEl) podRssEl.value = podcast.rssFeed || "";

  const googleCalEl = document.getElementById("google-cal");
  if (googleCalEl) googleCalEl.value = podcast.googleCal || "";

  const guestFormUrlEl = document.getElementById("guest-form-url");
  if (guestFormUrlEl) guestFormUrlEl.value = podcast.guestUrl || "";

  const emailEl = document.getElementById("email");
  if (emailEl) emailEl.value = podcast.email || "";

  const descriptionEl = document.getElementById("description");
  if (descriptionEl) descriptionEl.value = podcast.description || "";

  const categoryEl = document.getElementById("category");
  if (categoryEl) categoryEl.value = podcast.category || "";

  // Social media links
  const facebookEl = document.getElementById("facebook");
  if (facebookEl) facebookEl.value = podcast.socialMedia?.[0] || "";

  const instagramEl = document.getElementById("instagram");
  if (instagramEl) instagramEl.value = podcast.socialMedia?.[1] || "";

  const linkedinEl = document.getElementById("linkedin");
  if (linkedinEl) linkedinEl.value = podcast.socialMedia?.[2] || "";

  const twitterEl = document.getElementById("twitter");
  if (twitterEl) twitterEl.value = podcast.socialMedia?.[3] || "";

  const tiktokEl = document.getElementById("tiktok");
  if (tiktokEl) tiktokEl.value = podcast.socialMedia?.[4] || "";

  const pinterestEl = document.getElementById("pinterest");
  if (pinterestEl) pinterestEl.value = podcast.socialMedia?.[5] || "";
}

function resetForm() {
  form.reset();
  selectedPodcastId = null;
}

async function renderPodcastList() {
  try {
    // Fetch podcasts from your backend
    const response = await fetchPodcasts();
    const podcasts = response.podcast; // adjust if needed

    const podcastListElement = document.getElementById("podcast-list");
    podcastListElement.innerHTML = "";

    if (podcasts.length === 0) {
      podcastListElement.innerHTML = `
        <div class="empty-state">
          <p>No podcasts found. Click "Add Podcast" to create your first podcast.</p>
        </div>
      `;
      return;
    }

    podcasts.forEach((podcast) => {
      const podcastCard = document.createElement("div");
      podcastCard.className = "podcast-card";
      podcastCard.innerHTML = `
        <div class="podcast-content">
          <div class="podcast-image" style="background-image: url('${
            podcast.logoUrl
          }')"></div>
          <div class="podcast-info">
            <div class="podcast-header">
              <div>
                <h2 class="podcast-title">${podcast.podName}</h2>
                <p class="podcast-meta"><span>Category:</span> ${
                  podcast.category || "Uncategorized"
                }</p>
                <p class="podcast-meta"><span>Host:</span> ${
                  podcast.hostName || "Not specified"
                }</p>
                <p class="podcast-meta"><span>Owner:</span> ${
                  podcast.ownerName || "Not specified"
                }</p>
              </div>
              <div class="podcast-actions">
                <button class="action-btn view-btn" title="View podcast details" data-id="${
                  podcast._id
                }">
                  ${svgpodcastmanagement.view}
                </button>
                <button class="action-btn edit-btn" title="Edit podcast" data-id="${
                  podcast._id
                }">
                  ${svgpodcastmanagement.edit}
                </button>
                <button class="action-btn delete-btn-home" title="Delete podcast" data-id="${
                  podcast._id
                }">
                  <span class="icon">${svgpodcastmanagement.delete}</span>
                </button>
              </div>
            </div>
            <p class="podcast-description"><strong>Description: </strong>${
              podcast.description || "No description available."
            }</p>
            <!-- Container for episodes -->
            <div class="podcast-episodes"></div>
          </div>
        </div>
        <div class="podcast-footer">
          <button class="view-details-btn" data-id="${
            podcast._id
          }">View Details</button>
        </div>`;
      podcastListElement.appendChild(podcastCard);

      // Fetch and display episodes for this podcast with heading "Episodes:"
      fetchEpisodesByPodcast(podcast._id).then((episodes) => {
        if (episodes && episodes.length) {
          const epContainer = podcastCard.querySelector(".podcast-episodes");
          const epHeading = document.createElement("h4");
          epHeading.textContent = "Episodes:";
          epContainer.appendChild(epHeading);

          // Always create a flex container for episode labels (dropdown removed)
          const epList = document.createElement("div");
          epList.style.display = "flex";
          epList.style.flexDirection = "row";
          epList.style.gap = "1rem";
          episodes.forEach((ep) => {
            const epItem = document.createElement("div");
            epItem.textContent = ep.title;
            epItem.classList.add("episode-label"); // added label class
            // Attach click event to open the popup for editing
            epItem.addEventListener("click", () => {
              showEpisodePopup(ep);
            });
            epList.appendChild(epItem);
          });
          epContainer.appendChild(epList);
        }
      });
    });

    // Add event listeners for action buttons
    document
      .querySelectorAll(".view-btn, .view-details-btn")
      .forEach((button) => {
        button.addEventListener("click", (e) => {
          const btn = e.target.closest("button");
          const podcastId = btn ? btn.getAttribute("data-id") : null;
          if (podcastId) {
            viewPodcast(podcastId);
          }
        });
      });

    document.querySelectorAll(".edit-btn").forEach((button) => {
      button.addEventListener("click", async (e) => {
        const podcastId = e.target.closest("button").getAttribute("data-id");
        try {
          const podcast = await fetchPodcast(podcastId);
          displayPodcastDetails(podcast.podcast);
          selectedPodcastId = podcastId; // Set the selected podcast ID

          // Fetch podcasts to ensure the podcast ID is available
          const response = await fetchPodcasts();
          const podcasts = response.podcast;
          renderPodcastSelection(podcasts);

          document.getElementById("form-popup").style.display = "flex";
        } catch (error) {
          showNotification("Error", "Failed to fetch podcast details", "error");
        }
      });
    });

    document.querySelectorAll(".delete-btn").forEach((button) => {
      button.addEventListener("click", async (e) => {
        const podcastId = e.target.closest("button").getAttribute("data-id");
        if (confirm("Are you sure you want to delete this podcast?")) {
          try {
            await deletePodcast(podcastId);
            showNotification(
              "Success",
              "Podcast deleted successfully!",
              "success"
            );
            e.target.closest(".podcast-card")?.remove();

            // Check if there are no more podcasts
            if (document.querySelectorAll(".podcast-card").length === 0) {
              renderPodcastList(); // This will show the empty state
            }
          } catch (error) {
            showNotification("Error", "Failed to delete podcast.", "error");
          }
        }
      });
    });

    // Added event listener for elements with class "delete-btn-home"
    document.querySelectorAll(".delete-btn-home").forEach((button) => {
      button.addEventListener("click", async (e) => {
        const podcastId = e.target.closest("button").getAttribute("data-id");
        if (confirm("Are you sure you want to delete this podcast?")) {
          try {
            await deletePodcast(podcastId);
            showNotification(
              "Success",
              "Podcast deleted successfully!",
              "success"
            );
            e.target.closest(".podcast-card")?.remove();
            if (document.querySelectorAll(".podcast-card").length === 0) {
              renderPodcastList();
            }
          } catch (error) {
            showNotification("Error", "Failed to delete podcast.", "error");
          }
        }
      });
    });
  } catch (error) {
    console.error("Error rendering podcast list:", error);
    showNotification("Error", "Failed to load podcasts.", "error");
  }
}

// Render podcast selection for creating a new episode
function renderPodcastSelection(podcasts) {
  const podcastSelectElement = document.getElementById("podcast-select");
  podcastSelectElement.innerHTML = "";

  if (podcasts.length === 0) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "No podcasts available";
    podcastSelectElement.appendChild(option);
    return;
  }

  podcasts.forEach((podcast) => {
    const option = document.createElement("option");
    option.value = podcast._id;
    option.textContent = podcast.podName;
    podcastSelectElement.appendChild(option);
  });
}

// View podcast details
async function viewPodcast(podcastId) {
  try {
    const response = await fetchPodcast(podcastId);
    const podcast = response.podcast;
    renderPodcastDetail(podcast);
    document.getElementById("podcast-list").style.display = "none";
    document.getElementById("podcast-detail").style.display = "block";
  } catch (error) {
    showNotification("Error", "Failed to load podcast details", "error");
  }
}

// Render the podcast detail view
function renderPodcastDetail(podcast) {
  const podcastDetailElement = document.getElementById("podcast-detail");
  podcastDetailElement.innerHTML = `
    <div class="detail-header">
      <button class="back-btn" id="back-to-list">
        ${svgpodcastmanagement.back}
        Back to podcasts
      </button>
    </div>
    <div class="detail-content">
      <div class="detail-image" style="background-image: url('${
        podcast.logoUrl
      }')"></div>
      <!-- New Episodes container moved under the image -->
      <div id="episodes-list" class="episodes-list"></div>
      <div class="detail-info">
        <h1 class="detail-title">${podcast.podName}</h1>
        <p class="detail-category">${podcast.category || "Uncategorized"}</p>
        <div class="detail-section">
          <h2>About</h2>
          <p>${podcast.description || "No description available."}</p>
        </div>
        <div class="separator"></div>
        <div class="detail-grid">
          <div class="detail-item">
            <h3>Podcast Owner</h3>
            <p>${podcast.ownerName || "Not specified"}</p>
          </div>
          <div class="detail-item">
            <h3>Host(s)</h3>
            <p>${podcast.hostName || "Not specified"}</p>
          </div>
          <div class="detail-item">
            <h3>Email Address</h3>
            <p>${podcast.email || "Not specified"}</p>
          </div>
          <div class="detail-item">
            <h3>RSS Feed</h3>
            ${
              podcast.rssFeed
                ? `<a href="${podcast.rssFeed}" target="_blank">${podcast.rssFeed}</a>`
                : "<p>Not specified</p>"
            }
          </div>
        </div>
        <div class="separator"></div>
        <div class="detail-section">
          <h2>Scheduling</h2>
          <div class="detail-grid">
            <div class="detail-item">
              <h3>Google Calendar</h3>
              ${
                podcast.googleCal
                  ? `<a href="${podcast.googleCal}" target="_blank" style="display: flex; align-items: center; gap: 0.5rem;">
                    ${svgpodcastmanagement.calendar}
                    Calendar Link
                  </a>`
                  : `<p style="display: flex; align-items: center; gap: 0.5rem;">
                    ${svgpodcastmanagement.calendar}
                    Not connected
                  </p>`
              }
            </div>
            <div class="detail-item">
              <h3>Guest Form URL</h3>
              ${
                podcast.guestUrl
                  ? `<a href="${podcast.guestUrl}" target="_blank">${podcast.guestUrl}</a>`
                  : "<p>Not specified</p>"
              }
            </div>
          </div>
        </div>
        <div class="separator"></div>
        <div class="detail-section">
          <h2>Social Media</h2>
          <div class="social-links">
            ${
              podcast.socialMedia && podcast.socialMedia[0]
                ? `<a href="${podcast.socialMedia[0]}" target="_blank" class="social-link">
                  ${svgpodcastmanagement.facebook}
                  Facebook
                </a>`
                : ""
            }
            ${
              podcast.socialMedia && podcast.socialMedia[1]
                ? `<a href="${podcast.socialMedia[1]}" target="_blank" class="social-link">
                  ${svgpodcastmanagement.instagram}
                  Instagram
                </a>`
                : ""
            }
            ${
              podcast.socialMedia && podcast.socialMedia[2]
                ? `<a href="${podcast.socialMedia[2]}" target="_blank" class="social-link">
                  ${svgpodcastmanagement.linkedin}
                  LinkedIn
                </a>`
                : ""
            }
            ${
              podcast.socialMedia && podcast.socialMedia[3]
                ? `<a href="${podcast.socialMedia[3]}" target="_blank" class="social-link">
                  ${svgpodcastmanagement.twitter}
                  Twitter
                </a>`
                : ""
            }
            ${
              podcast.socialMedia && podcast.socialMedia[4]
                ? `<a href="${podcast.socialMedia[4]}" target="_blank" class="social-link">
                  ${svgpodcastmanagement.tiktok}
                  TikTok
                </a>`
                : ""
            }
          </div>
        </div>
        <div class="detail-actions" style="margin-top: 2rem; display: flex; gap: 1rem;">
          <button class="back-btn" id="edit-podcast-btn" data-id="${
            podcast._id
          }">
            ${svgpodcastmanagement.edit}
            Edit Podcast
          </button>
          <button class="delete-btn" id="delete-podcast-btn" data-id="${
            podcast._id
          }">
            <span class="icon">${svgpodcastmanagement.delete}</span>
            Delete Podcast
          </button>
        </div>
      </div>
    </div>
  `;

  // Back button event listener
  document.getElementById("back-to-list").addEventListener("click", () => {
    document.getElementById("podcast-detail").style.display = "none";
    document.getElementById("podcast-list").style.display = "flex";
  });

  // Edit button event listener
  document
    .getElementById("edit-podcast-btn")
    .addEventListener("click", async () => {
      try {
        const podcastId = document
          .getElementById("edit-podcast-btn")
          .getAttribute("data-id");
        const response = await fetchPodcast(podcastId);
        displayPodcastDetails(response.podcast);
        selectedPodcastId = podcastId;
        document.getElementById("form-popup").style.display = "flex";
        document.getElementById("podcast-detail").style.display = "none";
      } catch (error) {
        showNotification("Error", "Failed to fetch podcast details", "error");
      }
    });

  // Delete button event listener
  document
    .getElementById("delete-podcast-btn")
    .addEventListener("click", async () => {
      if (confirm("Are you sure you want to delete this podcast?")) {
        try {
          const podcastId = document
            .getElementById("delete-podcast-btn")
            .getAttribute("data-id");
          await deletePodcast(podcastId);
          showNotification(
            "Success",
            "Podcast deleted successfully!",
            "success"
          );
          document.getElementById("podcast-detail").style.display = "none";
          renderPodcastList();
          document.getElementById("podcast-list").style.display = "flex";
        } catch (error) {
          showNotification("Error", "Failed to delete podcast.", "error");
        }
      }
    });

  // Render episodes vertically under the image container
  fetchEpisodesByPodcast(podcast._id)
    .then((episodes) => {
      const episodesListEl = document.getElementById("episodes-list");
      episodesListEl.innerHTML = `<h3 class="detail-section-title">Episodes</h3>`;

      if (episodes && episodes.length) {
        const episodesContainer = document.createElement("div");
        episodesContainer.className = "episodes-container";
        episodesContainer.style.display = "flex";
        episodesContainer.style.flexDirection = "column";
        episodesContainer.style.gap = "10px";
        episodesContainer.style.marginTop = "10px";

        episodes.forEach((ep) => {
          const episodeCard = document.createElement("div");
          episodeCard.className = "episode-card";
          episodeCard.style.padding = "12px";
          episodeCard.style.borderRadius = "var(--radius-medium)";
          episodeCard.style.backgroundColor = "var(--background-light)";
          episodeCard.style.boxShadow =
            "-3px -3px 6px var(--light-shadow-light), 3px 3px 6px var(--dark-shadow-light)";
          episodeCard.style.transition = "all 0.3s ease";
          episodeCard.style.cursor = "pointer";
          episodeCard.style.borderLeft = "3px solid var(--highlight-color)";
          episodeCard.style.display = "flex";
          episodeCard.style.justifyContent = "space-between";

          const publishDate = ep.publishDate
            ? new Date(ep.publishDate).toLocaleDateString()
            : "No date";
          const description = ep.description
            ? ep.description
            : "No description available.";

          // Create content container for title, date, and description
          const contentDiv = document.createElement("div");
          contentDiv.style.flex = "1";
          contentDiv.style.marginRight = "10px";

          contentDiv.innerHTML = `
          <div class="episode-title" style="font-weight: 600; color: rgba(0, 0, 0, 0.7); margin-bottom: 5px;">${
            ep.title
          }</div>
          <div class="episode-meta" style="font-size: 0.8rem; color: var(--text-color-light); margin-bottom: 5px;">
            <span>Published: ${publishDate}</span>
            ${ep.duration ? `<span> • ${ep.duration} min</span>` : ""}
          </div>
          <div class="episode-description" style="font-size: 0.85rem; color: var(--text-color-light); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${description}</div>
        `;

          // Create view button
          const viewButton = document.createElement("button");
          viewButton.className = "view-episode-btn";
          viewButton.textContent = "View";
          viewButton.style.alignSelf = "center";
          viewButton.style.backgroundColor = "var(--highlight-color)";
          viewButton.style.color = "white";
          viewButton.style.border = "none";
          viewButton.style.borderRadius = "var(--radius-small)";
          viewButton.style.padding = "5px 12px";
          viewButton.style.cursor = "pointer";
          viewButton.style.fontWeight = "600";
          viewButton.style.fontSize = "0.85rem";
          viewButton.style.transition = "all 0.3s ease";

          // Add hover effect to button
          viewButton.addEventListener("mouseenter", () => {
            viewButton.style.backgroundColor = "#e0662c";
            viewButton.style.transform = "translateY(-2px)";
          });

          viewButton.addEventListener("mouseleave", () => {
            viewButton.style.backgroundColor = "var(--highlight-color)";
            viewButton.style.transform = "translateY(0)";
          });

          // Add click event to view button
          viewButton.addEventListener("click", (e) => {
            e.stopPropagation(); // Prevent triggering the card click
            renderEpisodeDetail(ep);
          });

          // Add elements to card
          episodeCard.appendChild(contentDiv);
          episodeCard.appendChild(viewButton);

          // Add hover effect to card
          episodeCard.addEventListener("mouseenter", () => {
            episodeCard.style.transform = "translateY(-2px)";
            episodeCard.style.boxShadow =
              "-5px -5px 10px var(--light-shadow-light), 5px 5px 10px var(--dark-shadow-light)";
          });

          episodeCard.addEventListener("mouseleave", () => {
            episodeCard.style.transform = "translateY(0)";
            episodeCard.style.boxShadow =
              "-3px -3px 6px var(--light-shadow-light), 3px 3px 6px var(--dark-shadow-light)";
          });

          // Add click event to card (excluding the button)
          episodeCard.addEventListener("click", () => {
            renderEpisodeDetail(ep);
          });

          episodesContainer.appendChild(episodeCard);
        });

        episodesListEl.appendChild(episodesContainer);
      } else {
        const noEpisodes = document.createElement("p");
        noEpisodes.textContent = "No episodes available.";
        noEpisodes.style.marginTop = "10px";
        episodesListEl.appendChild(noEpisodes);
      }
    })
    .catch((error) => {
      console.error("Error fetching episodes:", error);
    });
}

// New function to render episode details and fetch guests
function renderEpisodeDetail(episode) {
  const episodeDetailElement = document.getElementById("podcast-detail");
  episodeDetailElement.innerHTML = `
    <div class="detail-header">
      <button class="back-btn" id="back-to-podcast">
        ${svgpodcastmanagement.back}
        Back to podcast
      </button>
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
        </div>
        <div class="separator"></div>
        <div class="detail-grid">
          <div class="detail-item">
            <h3>Publish Date</h3>
            <p>${
              new Date(episode.publishDate).toLocaleString() || "Not specified"
            }</p>
          </div>
          <div class="detail-item">
            <h3>Duration</h3>
            <p>${episode.duration || "Not specified"} minutes</p>
          </div>
        </div>
        <div class="separator"></div>
        <div class="detail-section">
          <h2>Guests</h2>
          <div id="guests-list"></div>
        </div>
        <div class="separator"></div>
        <div class="detail-actions" style="margin-top: 2rem; display: flex; gap: 1rem;">
          <button class="back-btn" id="edit-episode-btn" data-id="${
            episode._id
          }">
            ${svgpodcastmanagement.edit}
            Edit Episode
          </button>
          <button class="delete-btn" id="delete-episode-btn" data-id="${
            episode._id
          }">
            <span class="icon">${svgpodcastmanagement.delete}</span>
            Delete Episode
          </button>
        </div>
      </div>
    </div>
  `;

  // Back button event listener
  document.getElementById("back-to-podcast").addEventListener("click", () => {
    viewPodcast(episode.podcast_id);
  });

  // Edit button event listener
  document
    .getElementById("edit-episode-btn")
    .addEventListener("click", async () => {
      try {
        const response = await fetch(`/get_episodes/${episode._id}`);
        const episodeData = await response.json();
        showEpisodePopup(episodeData);
      } catch (error) {
        showNotification("Error", "Failed to fetch episode details", "error");
      }
    });

  // Delete button event listener
  document
    .getElementById("delete-episode-btn")
    .addEventListener("click", async () => {
      if (confirm("Are you sure you want to delete this episode?")) {
        try {
          await fetch(`/delete_episods/${episode._id}`, { method: "DELETE" });
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

  // Fetch and display guests for the episode
  fetchGuestsByEpisode(episode._id)
    .then((guests) => {
      const guestsListEl = document.getElementById("guests-list");
      guestsListEl.innerHTML = "";

      if (guests && guests.length) {
        const guestsContainer = document.createElement("div");
        guestsContainer.className = "guests-container";
        guestsContainer.style.display = "flex";
        guestsContainer.style.flexDirection = "column";
        guestsContainer.style.gap = "12px";
        guestsContainer.style.marginTop = "10px";

        guests.forEach((guest) => {
          const guestCard = document.createElement("div");
          guestCard.className = "guest-card";
          guestCard.style.padding = "15px";
          guestCard.style.borderRadius = "var(--radius-medium)";
          guestCard.style.backgroundColor = "var(--background-light)";
          guestCard.style.boxShadow =
            "-3px -3px 6px var(--light-shadow-light), 3px 3px 6px var(--dark-shadow-light)";
          guestCard.style.transition = "all 0.3s ease";
          guestCard.style.cursor = "pointer";
          guestCard.style.display = "flex";
          guestCard.style.justifyContent = "space-between";
          guestCard.style.alignItems = "center";
          guestCard.style.borderLeft = "3px solid #3b82f6"; // Different color from episodes

          // Create content container for guest info
          const contentDiv = document.createElement("div");
          contentDiv.style.flex = "1";

          // Add guest avatar placeholder (circle with initials)
          const avatarDiv = document.createElement("div");
          avatarDiv.style.width = "40px";
          avatarDiv.style.height = "40px";
          avatarDiv.style.borderRadius = "50%";
          avatarDiv.style.backgroundColor = "#3b82f6";
          avatarDiv.style.color = "white";
          avatarDiv.style.display = "flex";
          avatarDiv.style.alignItems = "center";
          avatarDiv.style.justifyContent = "center";
          avatarDiv.style.fontWeight = "bold";
          avatarDiv.style.marginRight = "15px";
          avatarDiv.style.flexShrink = "0";

          // Get initials from guest name
          const initials = guest.name
            .split(" ")
            .map((word) => word[0])
            .join("")
            .substring(0, 2)
            .toUpperCase();

          avatarDiv.textContent = initials;

          // Create guest info with name and email
          const infoDiv = document.createElement("div");
          infoDiv.style.display = "flex";
          infoDiv.style.alignItems = "center";

          infoDiv.innerHTML = `
          <div style="display: flex; flex-direction: column;">
            <div class="guest-name" style="font-weight: 600; color: rgba(0, 0, 0, 0.7); font-size: 1rem;">${guest.name}</div>
            <div class="guest-email" style="font-size: 0.85rem; color: var(--text-color-light);">${guest.email}</div>
          </div>
        `;

          // Create view profile button
          const viewProfileBtn = document.createElement("button");
          viewProfileBtn.className = "view-profile-btn";
          viewProfileBtn.textContent = "View Profile";
          viewProfileBtn.style.backgroundColor = "#3b82f6";
          viewProfileBtn.style.color = "white";
          viewProfileBtn.style.border = "none";
          viewProfileBtn.style.borderRadius = "var(--radius-small)";
          viewProfileBtn.style.padding = "6px 12px";
          viewProfileBtn.style.cursor = "pointer";
          viewProfileBtn.style.fontWeight = "600";
          viewProfileBtn.style.fontSize = "0.85rem";
          viewProfileBtn.style.transition = "all 0.3s ease";

          // Add hover effect to button
          viewProfileBtn.addEventListener("mouseenter", () => {
            viewProfileBtn.style.backgroundColor = "#2563eb";
            viewProfileBtn.style.transform = "translateY(-2px)";
          });

          viewProfileBtn.addEventListener("mouseleave", () => {
            viewProfileBtn.style.backgroundColor = "#3b82f6";
            viewProfileBtn.style.transform = "translateY(0)";
          });

          // Add click event to view button
          viewProfileBtn.addEventListener("click", (e) => {
            e.stopPropagation(); // Prevent triggering the card click
            renderGuestDetail(guest);
          });

          // Add hover effect to card
          guestCard.addEventListener("mouseenter", () => {
            guestCard.style.transform = "translateY(-2px)";
            guestCard.style.boxShadow =
              "-5px -5px 10px var(--light-shadow-light), 5px 5px 10px var(--dark-shadow-light)";
          });

          guestCard.addEventListener("mouseleave", () => {
            guestCard.style.transform = "translateY(0)";
            guestCard.style.boxShadow =
              "-3px -3px 6px var(--light-shadow-light), 3px 3px 6px var(--dark-shadow-light)";
          });

          // Add click event to card
          guestCard.addEventListener("click", () => {
            renderGuestDetail(guest);
          });

          // Assemble the card
          infoDiv.prepend(avatarDiv);
          contentDiv.appendChild(infoDiv);
          guestCard.appendChild(contentDiv);
          guestCard.appendChild(viewProfileBtn);
          guestsContainer.appendChild(guestCard);
        });

        guestsListEl.appendChild(guestsContainer);
      } else {
        const noGuests = document.createElement("p");
        noGuests.textContent = "No guests available for this episode.";
        noGuests.style.marginTop = "10px";
        noGuests.style.fontStyle = "italic";
        noGuests.style.color = "var(--text-color-light)";
        guestsListEl.appendChild(noGuests);
      }
    })
    .catch((error) => {
      console.error("Error fetching guests:", error);
      const errorMsg = document.createElement("p");
      errorMsg.textContent = "Error loading guests. Please try again later.";
      errorMsg.style.color = "var(--danger-color)";
      document.getElementById("guests-list").appendChild(errorMsg);
    });
}

// Replace the renderGuestDetail function with this enhanced version:

// New function to render guest details
function renderGuestDetail(guest) {
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
        ${svgpodcastmanagement.back}
        Back to episode
      </button>
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
              <p><a href="mailto:${
                guest.email
              }" style="color: var(--highlight-color);">${guest.email}</a></p>
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
          <div>
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
          <div>
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
        <label for="upd-guest-id">Guest</label>
        <!-- Change guest field to a select -->
        <select id="upd-guest-id" name="guestId"></select>
        <!-- Add field for manual guest entry -->
        <div class="manual-guest-field">
          <label for="manual-guest">Add Guest Manually</label>
          <input type="text" id="manual-guest" placeholder="Click to add guest manually" readonly />
        </div>
      </div>
      <div class="field-group">
        <label for="upd-status">Status</label>
        <input type="text" id="upd-status" name="status" value="${
          episode.status || ""
        }" />
      </div>
      <div class="form-actions">
        <button type="button" id="cancel-episode-update" class="cancel-btn">Cancel</button></div>
        <button type="submit" class="save-btn">Update Episode</button>
      </div>
    </form>
  `;
  popup.appendChild(popupContent);
  document.body.appendChild(popup);

  // Populate guest dropdown in update popup with the current guest selected.
  const updGuestSelect = document.getElementById("upd-guest-id");
  renderGuestSelection(updGuestSelect, episode.guestId || "");

  // Fetch podcasts to ensure the podcast ID is available
  const response = await fetchPodcasts();
  const podcasts = response.podcast;
  renderPodcastSelection(podcasts);

  // Close popup events
  popup.querySelector("#close-episode-popup").addEventListener("click", () => {
    document.body.removeChild(popup);
  });
  popup
    .querySelector("#cancel-episode-update")
    .addEventListener("click", () => {
      document.body.removeChild(popup);
    });

  // Manual guest entry
  const manualGuestField = document.querySelector(".manual-guest-field");
  manualGuestField.addEventListener("click", () => {
    showManualGuestPopup(updGuestSelect);
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
        guestId: document.getElementById("upd-guest-id").value, // value from select
        status: document.getElementById("upd-status").value.trim()
      };
      Object.keys(updatedData).forEach((key) => {
        if (!updatedData[key]) delete updatedData[key];
      });
      try {
        const response = await fetch(`/update_episodes/${episode._id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(updatedData)
        });
        const result = await response.json();
        if (response.ok) {
          showNotification(
            "Success",
            "Episode updated successfully!",
            "success"
          );
          document.body.removeChild(popup);
          renderPodcastList();
        } else {
          showNotification("Error", result.error || "Update failed", "error");
        }
      } catch (error) {
        showNotification("Error", "Failed to update episode.", "error");
      }
    });
}
