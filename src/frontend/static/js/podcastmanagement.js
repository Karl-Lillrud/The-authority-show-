import {
  addPodcast,
  fetchPodcasts,
  fetchPodcast,
  updatePodcast,
  deletePodcast
} from "../requests/podcastRequests.js";
import { registerEpisode } from "../requests/episodeRequest.js";
import { svgIcons } from "./svgIcons.js";

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
    iconSvg =
      '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>';
  } else if (type === "error") {
    iconSvg =
      '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>';
  } else {
    iconSvg =
      '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';
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

document.addEventListener("DOMContentLoaded", function () {
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
      if (!data.podcastId || !data.title) {
        showNotification(
          "Missing Fields",
          "Please fill in all required fields.",
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
let selectedPodcastId = null;

form.addEventListener("submit", async function (e) {
  e.preventDefault();
  console.log("Form submitted");

  // Retrieve the form elements
  const podName = document.getElementById("pod-name")?.value.trim() || "";
  const email = document.getElementById("email")?.value.trim() || "";
  const category = document.getElementById("category")?.value.trim() || "";

  // Check if required fields are empty
  if (!podName) {
    showNotification(
      "Missing Field",
      "Please fill in the Podcast Name field.",
      "error"
    );
    return;
  }

  // Collect social media values, filtering out empty ones
  const socialMedia = [
    document.getElementById("facebook")?.value.trim(),
    document.getElementById("instagram")?.value.trim(),
    document.getElementById("linkedin")?.value.trim(),
    document.getElementById("twitter")?.value.trim(),
    document.getElementById("tiktok")?.value.trim(),
    document.getElementById("pinterest")?.value.trim()
  ].filter((link) => link);

  // Build the data object
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
    logoUrl: "https://via.placeholder.com/300", // Placeholder image
    category,
    socialMedia
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

  try {
    let responseData;
    if (selectedPodcastId) {
      responseData = await updatePodcast(selectedPodcastId, data);
      if (!responseData.error) {
        showNotification("Success", "Podcast updated successfully!", "success");
      }
    } else {
      responseData = await addPodcast(data);
      if (!responseData.error) {
        showNotification("Success", "Podcast added successfully!", "success");
      }
    }

    if (responseData.error) {
      showNotification(
        "Error",
        `${
          responseData.details
            ? JSON.stringify(responseData.details)
            : responseData.error
        }`,
        "error"
      );
    } else {
      document.getElementById("form-popup").style.display = "none";
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
            podcast.logoUrl || "https://via.placeholder.com/300"
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
                  ${svgIcons.view}
                </button>
                <button class="action-btn edit-btn" title="Edit podcast" data-id="${
                  podcast._id
                }">
                  ${svgIcons.edit}
                </button>
                <button class="action-btn delete-btn" title="Delete podcast" data-id="${
                  podcast._id
                }">
                  <span class="icon">${svgIcons.delete}</span>
                </button>
              </div>
            </div>
            <p class="podcast-description">${
              podcast.description || "No description available."
            }</p>
          </div>
        </div>
        <div class="podcast-footer">
          <button class="view-details-btn" data-id="${
            podcast._id
          }">View Details</button>
        </div>
      `;
      podcastListElement.appendChild(podcastCard);
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
          selectedPodcastId = podcastId;
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
        ${svgIcons.back}
        Back to podcasts
      </button>
    </div>
    <div class="detail-content">
      <div class="detail-image" style="background-image: url('${
        podcast.logoUrl || "https://via.placeholder.com/300"
      }')"></div>
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
                    ${svgIcons.calendar}
                    Calendar Link
                  </a>`
                  : `<p style="display: flex; align-items: center; gap: 0.5rem;">
                    ${svgIcons.calendar}
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
                  ${svgIcons.facebook}
                  Facebook
                </a>`
                : ""
            }
            ${
              podcast.socialMedia && podcast.socialMedia[1]
                ? `<a href="${podcast.socialMedia[1]}" target="_blank" class="social-link">
                  ${svgIcons.instagram}
                  Instagram
                </a>`
                : ""
            }
            ${
              podcast.socialMedia && podcast.socialMedia[2]
                ? `<a href="${podcast.socialMedia[2]}" target="_blank" class="social-link">
                  ${svgIcons.linkedin}
                  LinkedIn
                </a>`
                : ""
            }
            ${
              podcast.socialMedia && podcast.socialMedia[3]
                ? `<a href="${podcast.socialMedia[3]}" target="_blank" class="social-link">
                  ${svgIcons.twitter}
                  Twitter
                </a>`
                : ""
            }
            ${
              podcast.socialMedia && podcast.socialMedia[4]
                ? `<a href="${podcast.socialMedia[4]}" target="_blank" class="social-link">
                  ${svgIcons.tiktok}
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
            ${svgIcons.edit}
            Edit Podcast
          </button>
          <button class="delete-btn" id="delete-podcast-btn" data-id="${
            podcast._id
          }">
            <span class="icon">${svgIcons.delete}</span>
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
}
