import {
  addPodcast,
  fetchPodcasts,
  fetchPodcast,
  updatePodcast,
  deletePodcast
} from "../requests/podcastRequests.js";
import { registerEpisode } from "../requests/episodeRequest.js"; // Import the new function
import { svgIcons } from "./svgIcons.js"; // import SVG icons

console.log("podcastmanagement.js loaded");

document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM fully loaded and parsed");

  renderPodcastList();

  // New event: show form for adding a podcast
  document.getElementById("add-podcast-btn").addEventListener("click", () => {
    resetForm();
    selectedPodcastId = null;
    // Show the form popup instead of an inline form
    document.getElementById("form-popup").style.display = "flex";
  });
  // Add event listener to close the form popup
  document.getElementById("close-form-popup").addEventListener("click", () => {
    document.getElementById("form-popup").style.display = "none";
  });

  // New event: show form for creating a new episode
  document
    .getElementById("create-episode-btn")
    .addEventListener("click", async () => {
      const podcasts = await fetchPodcasts();
      renderPodcastSelection(podcasts.podcast); // Adjusted to match the existing API response
      document.getElementById("episode-form-popup").style.display = "flex";
    });
  // Add event listener to close the episode form popup
  document
    .getElementById("close-episode-form-popup")
    .addEventListener("click", () => {
      document.getElementById("episode-form-popup").style.display = "none";
    });

  // Add event listener for episode form submission
  document
    .getElementById("create-episode-form")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      const data = Object.fromEntries(formData.entries());

      // Check for missing required fields
      if (!data.podcastId || !data.title) {
        showAlert("Please fill in all required fields.", "red");
        return;
      }

      // Logga vald podcast för debug
      console.log("Skickar episoddata med podcastId:", data.podcastId);

      try {
        const result = await registerEpisode(data); // Use the new function
        console.log("Result from registerEpisode:", result); // Added log
        if (result.message) {
          showAlert("Episode created successfully!", "green");
          document.getElementById("episode-form-popup").style.display = "none";
        } else {
          showAlert(`Error: ${result.error}`, "red");
        }
      } catch (error) {
        console.error("Error creating episode:", error);
        showAlert("Failed to create episode.", "red");
      }
    });
});

const formContainer = document.querySelector(".form-box");
const podcastsContainer = document.querySelector(".podcasts-container");
const form = document.getElementById("register-podcast-form");
let selectedPodcastId = null;

form.addEventListener("submit", async function (e) {
  e.preventDefault();
  console.log("Form submitted");

  // Retrieve the form elements
  const podName = document.getElementById("pod-name")?.value.trim() || "";
  const email = document.getElementById("email")?.value.trim() || "";
  const category = document.getElementById("category")?.value.trim() || "";

  // Initialize error message
  let errorMessage = "";

  // Check if required fields are empty
  const requiredFields = [{ name: "podName", value: podName }];

  requiredFields.forEach((field) => {
    if (!field.value) {
      errorMessage += `Please fill in the ${field.name}.<br>`;
    }
  });

  // If there is any missing required field, show an alert
  if (errorMessage) {
    showAlert(errorMessage, "red");
    return;
  }

  // Collect social media values, ensuring empty strings are included but only if they are not empty
  const socialMedia = [
    document.getElementById("facebook")?.value.trim(),
    document.getElementById("instagram")?.value.trim(),
    document.getElementById("linkedin")?.value.trim(),
    document.getElementById("twitter")?.value.trim(),
    document.getElementById("tiktok")?.value.trim(),
    document.getElementById("pinterest")?.value.trim()
  ].filter((link) => link); // Remove empty strings

  // Collect URLs for optional fields, remove if empty
  const googleCal = document.getElementById("google-cal")?.value.trim() || null;
  const guestUrl =
    document.getElementById("guest-form-url")?.value.trim() || null;

  // Build the data object
  const data = {
    teamId: "",
    podName,
    ownerName: document.getElementById("pod-owner")?.value.trim() || "",
    hostName: document.getElementById("pod-host")?.value.trim() || "",
    rssFeed: document.getElementById("pod-rss")?.value.trim() || "",
    googleCal: googleCal,
    guestUrl: guestUrl,
    email,
    description: document.getElementById("description")?.value.trim() || "",
    logoUrl: document.getElementById("description")?.value.trim(),
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
    } else {
      responseData = await addPodcast(data);
    }

    if (responseData.error) {
      showAlert(
        `Error: ${
          responseData.details
            ? JSON.stringify(responseData.details)
            : responseData.error
        }`,
        "red"
      );
    } else {
      showAlert(
        selectedPodcastId
          ? "Podcast updated successfully!"
          : "Podcast added successfully!",
        "green"
      );
    }
  } catch (error) {
    console.error("Error:", error);
    showAlert(
      selectedPodcastId
        ? "There was an error with the update process."
        : "There was an error with the registration process.",
      "red"
    );
  }
});

function displayPodcastDetails(podcast) {
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

  formContainer.style.display = "block";
  document.getElementById("podcasts-popup").style.display = "none";
}

function addBackButton() {
  const inviteBtn = document.querySelector(".invite-btn");
  if (!document.getElementById("back-btn")) {
    const backBtn = document.createElement("button");
    backBtn.id = "back-btn";
    backBtn.className = "crud-btn";
    backBtn.textContent = "Back";
    backBtn.style.marginRight = "10px";
    backBtn.style.width = inviteBtn.offsetWidth + "px"; // Match the width of the invite button
    inviteBtn.parentNode.insertBefore(backBtn, inviteBtn);

    backBtn.addEventListener("click", () => {
      resetForm();
      backBtn.remove();
      inviteBtn.textContent = "SAVE";
      inviteBtn.classList.remove("update-btn");
      selectedPodcastId = null;
    });
  }
}

function resetForm() {
  form.reset();
}

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

    try {
      for (const podcastId of podcastIds) {
        await deletePodcast(podcastId);
      }
      showAlert("Selected podcasts deleted successfully!", "green");
      document.getElementById("podcasts-popup").style.display = "none";
    } catch (error) {
      showAlert("Failed to delete selected podcasts.", "red");
    }
  });

async function renderPodcastList() {
  try {
    // Fetch podcasts from your backend
    const response = await fetchPodcasts();
    const podcasts = response.podcast; // adjust if needed

    const podcastListElement = document.getElementById("podcast-list");
    podcastListElement.innerHTML = "";

    if (podcasts.length === 0) {
      podcastListElement.innerHTML = `
        <div style="text-align: center; padding: 3rem; background-color: white; border-radius: 8px;">
          <p style="color: #666;">No podcasts found</p>
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
                  podcast.category
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
                  ${svgIcons.delete}
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
          const inviteBtn = document.querySelector(".invite-btn");
          inviteBtn.textContent = "Update";
          inviteBtn.classList.add("update-btn");
          // Optionally, hide list view if needed:
          document.getElementById("podcast-list").style.display = "none";
        } catch (error) {
          showAlert("Failed to fetch podcast details", "red");
        }
      });
    });
    document.querySelectorAll(".delete-btn").forEach((button) => {
      button.addEventListener("click", async (e) => {
        const podcastId = e.target.closest("button").getAttribute("data-id");
        try {
          await deletePodcast(podcastId);
          // Remove the podcast card from the UI
          e.target.closest(".podcast-card")?.remove();
          showAlert("Podcast deleted successfully!", "green");
        } catch (error) {
          showAlert("Failed to delete podcast.", "red");
        }
      });
    });
  } catch (error) {
    console.error("Error rendering podcast list:", error);
  }
}

// New function: render podcast selection for creating a new episode
function renderPodcastSelection(podcasts) {
  const podcastSelectElement = document.getElementById("podcast-select");
  podcastSelectElement.innerHTML = "";

  podcasts.forEach((podcast) => {
    const option = document.createElement("option");
    option.value = podcast._id;
    option.textContent = podcast.podName;
    podcastSelectElement.appendChild(option);
  });
}

// Update viewPodcast to use the new detail layout
async function viewPodcast(podcastId) {
  try {
    const response = await fetchPodcast(podcastId);
    const podcast = response.podcast; // assuming API returns it here
    renderPodcastDetail(podcast);
    document.getElementById("podcast-list").style.display = "none";
    document.getElementById("podcast-detail").style.display = "block";
  } catch (error) {
    showAlert("Podcast not found", "red");
  }
}

// New function: renders the podcast detail view using your design
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
        podcast.logoUrl
      }')"></div>
      <div class="detail-info">
        <h1 class="detail-title">${podcast.podName}</h1>
        <p class="detail-category">${podcast.category}</p>
        <div class="detail-section"></div>
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
              <h3>Calendar URL</h3>
              <p>podmanager.com/?pod=${podcast.podName.replace(/\s+/g, "")}</p>
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
      </div>
    </div>
  `;

  document.getElementById("back-to-list").addEventListener("click", () => {
    document.getElementById("podcast-detail").style.display = "none";
    document.getElementById("podcast-list").style.display = "flex";
  });
}
