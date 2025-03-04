import {
  addPodcast,
  fetchPodcasts,
  fetchPodcast,
  updatePodcast,
  deletePodcast
} from "../requests/podcastRequest.js";

console.log("podcastmanagement.js loaded");

document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM fully loaded and parsed");

  renderPodcastList();
});

const formContainer = document.querySelector(".form-box");
const podcastsContainer = document.querySelector(".podcasts-container");
const form = document.getElementById("register-podcast-form");
let selectedPodcastId = null;

// New event: show form for adding a podcast
document.getElementById("add-podcast-btn").addEventListener("click", () => {
  resetForm();
  selectedPodcastId = null;
  formContainer.style.display = "block";
});

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
    logoUrl:
      "https://podmanagerstorage.blob.core.windows.net/blob-container/pod1.jpg",
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

function showAlert(message, color) {
  const alertBox = document.getElementById("custom-alert");
  const alertMessage = document.getElementById("alert-message");

  alertMessage.innerHTML = message;
  alertBox.style.background = color;
  alertBox.style.display = "block";

  setTimeout(() => {
    alertBox.style.display = "none";
  }, 2500);
}

// CRUD operation buttons
document
  .getElementById("fetch-podcasts-btn")
  .addEventListener("click", async () => {
    console.log("Fetch All Podcasts button clicked");
    try {
      const response = await fetchPodcasts();
      const podcasts = response.podcast;
      console.log("Fetched Podcasts:", podcasts);

      // Populate podcasts container
      const podcastsList = document.getElementById("podcasts-list");
      podcastsList.innerHTML = "";
      podcasts.forEach((podcast) => {
        const podcastItem = document.createElement("div");
        podcastItem.className = "podcast-item";
        podcastItem.innerHTML = `
            <span>${podcast.podName}</span>
            <div class="action-buttons">
              <button class="select-btn" data-id="${podcast._id}">Select</button>
              <button class="delete-btn" data-id="${podcast._id}">Delete</button>
            </div>
          `;
        podcastsList.appendChild(podcastItem);
      });

      // Show popup
      const popup = document.getElementById("podcasts-popup");
      popup.style.display = "flex";

      // Add event listeners for select and delete buttons
      document.querySelectorAll(".select-btn").forEach((button) => {
        button.addEventListener("click", async (e) => {
          const podcastId = e.target.getAttribute("data-id");
          try {
            const podcast = await fetchPodcast(podcastId);
            console.log("Fetched Podcast:", podcast);
            displayPodcastDetails(podcast.podcast);
            selectedPodcastId = podcastId;
            const inviteBtn = document.querySelector(".invite-btn");
            inviteBtn.textContent = "Update";
            inviteBtn.classList.add("update-btn");
            addBackButton();
          } catch (error) {
            console.error("Error fetching podcast (ignored):", error);
            // Do not show error alert for this operation.
          }
          const popup = document.getElementById("podcasts-popup");
          popup.style.display = "none";
        });
      });

      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", async (e) => {
          const podcastId = e.target.getAttribute("data-id");
          try {
            await deletePodcast(podcastId);
            // Remove the entire podcast item from the popup list
            const podcastItem = e.target.closest(".podcast-item");
            if (podcastItem) podcastItem.remove();
          } catch (error) {
            showAlert("Failed to delete podcast.", "red");
          }
        });
      });
    } catch (error) {
      showAlert("Failed to fetch podcasts.", "red");
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

document
  .getElementById("fetch-podcast-btn")
  .addEventListener("click", async () => {
    const podcastId = prompt("Enter Podcast ID:");
    if (podcastId) {
      try {
        const podcast = await fetchPodcast(podcastId);
        console.log("Fetched Podcast:", podcast);
        displayPodcastDetails(podcast.podcast);
        selectedPodcastId = podcastId;
        document.querySelector(".invite-btn").textContent = "UPDATE";
      } catch (error) {
        showAlert("Failed to fetch podcast.", "red");
      }
    }
  });

document
  .getElementById("update-podcast-btn")
  .addEventListener("click", async () => {
    const podcastId = prompt("Enter Podcast ID:");
    if (podcastId) {
      const updateData = prompt("Enter update data in JSON format:");
      if (updateData) {
        try {
          const updatedPodcast = await updatePodcast(
            podcastId,
            JSON.parse(updateData)
          );
          console.log("Updated Podcast:", updatedPodcast);
          showAlert("Updated podcast successfully!", "green");
        } catch (error) {
          showAlert("Failed to update podcast.", "red");
        }
      }
    }
  });

document
  .getElementById("delete-podcast-btn")
  .addEventListener("click", async () => {
    const podcastId = prompt("Enter Podcast ID:");
    if (podcastId) {
      try {
        const deletedPodcast = await deletePodcast(podcastId);
        console.log("Deleted Podcast:", deletedPodcast);
        showAlert("Deleted podcast successfully!", "green");
      } catch (error) {
        showAlert("Failed to delete podcast.", "red");
      }
    }
  });

// Close popup
document.getElementById("close-popup-btn").addEventListener("click", () => {
  const popup = document.getElementById("podcasts-popup");
  popup.style.display = "none";
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

// Add HTML content dynamically
const container = document.querySelector(".container");
container.insertAdjacentHTML(
  "afterbegin",
  `
    <a href="${url_for(
      "dashboard_bp.dashboard"
    )}" class="back-arrow">&#8592; Back</a>
    <div class="crud-buttons">
      <button id="fetch-podcasts-btn" class="crud-btn">Fetch All Podcasts</button>

    </div>
    <div class="form-box">
      <div class="form-fields">
        <form id="register-podcast-form">
          <!-- Pod Logo -->
          <div class="form-group">
            <label for="pod-logo">Pod Logo</label>
            <div
              style="display: flex; align-items: center; justify-content: center"
            >
              <img
                src="https://podmanagerstorage.blob.core.windows.net/blob-container/pod1.jpg"
                alt="Pod Logo"
                class="pod-logo pod-logo-inline"
              />
            </div>
          </div>

          <!-- Podcast Name -->
          <div class="field-group">
            <label for="pod-name">Podcast Name</label>
            <input type="text" id="pod-name" name="podName" autocomplete="off" />
          </div>

          <!-- RSS Feed -->
          <div class="field-group">
            <label for="pod-rss">RSS Feed</label>
            <input type="url" id="pod-rss" name="rssFeed" />
          </div>

          <!-- Podcast Owner -->
          <div class="field-group">
            <label for="pod-owner">Podcast Owner</label>
            <input type="text" id="pod-owner" name="ownerName" />
          </div>

          <!-- Host Name -->
          <div class="field-group">
            <label for="pod-host">Host(s) Name(s)</label>
            <input type="text" id="pod-host" name="hostName" />
          </div>

          <!-- Description -->
          <div class="field-group">
            <label for="description">Podcast Description</label>
            <textarea id="description" name="description"></textarea>
          </div>

          <!-- Category -->
          <div class="field-group">
            <label for="category">Category (Required)</label>
            <input type="text" id="category" name="category" required />
          </div>

          <!-- Email Address -->
          <div class="field-group">
            <label for="email">Email Address</label>
            <input type="email" id="email" name="email" />
          </div>

          <!-- Google Calendar Integration -->
          <div class="field-group">
            <label>Google Calendar Integration</label>
            <button type="button" class="connect-btn">CONNECT</button>
          </div>

          <!-- Google Calendar Link -->
          <div class="field-group">
            <label>Google Calendar Pick a Date URL</label>
            <div class="inline-field">
              <span>podmanager.com/?pod=TheAuthorityShow</span>
            </div>
          </div>

          <!-- Guest Form URL -->
          <div class="field-group">
            <label for="guest-form-url">Guest Form URL</label>
            <input type="url" id="guest-form-url" name="guestUrl" />
          </div>

          <!-- Social Media Links -->
          <div class="field-group">
            <label for="facebook">Facebook</label>
            <input type="url" id="facebook" name="socialMedia[]" />
          </div>

          <div class="field-group">
            <label for="instagram">Instagram</label>
            <input type="url" id="instagram" name="socialMedia[]" />
          </div>

          <div class="field-group">
            <label for="linkedin">LinkedIn</label>
            <input type="url" id="linkedin" name="socialMedia[]" />
          </div>

          <div class="field-group">
            <label for="twitter">Twitter</label>
            <input type="url" id="twitter" name="socialMedia[]" />
          </div>

          <div class="field-group">
            <label for="tiktok">TikTok</label>
            <input type="url" id="tiktok" name="socialMedia[]" />
          </div>

          <div class="field-group">
            <label for="pinterest">Pinterest</label>
            <input type="url" id="pinterest" name="socialMedia[]" />
          </div>

          <button type="submit" class="invite-btn">SAVE</button>
        </form>
      </div>
    </div>
    `
);

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
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                  </svg>
                </button>
                <button class="action-btn edit-btn" title="Edit podcast" data-id="${
                  podcast._id
                }">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"></path>
                  </svg>
                </button>
                <button class="action-btn delete-btn" title="Delete podcast" data-id="${
                  podcast._id
                }">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 6h18"></path>
                    <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                    <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                  </svg>
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
      button.addEventListener("click", (e) => {
        const podcastId = e.target.closest("button").dataset.id;
        updatePodcast(podcastId);
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

// Example usage: call renderPodcastList() after adding/updating or on "Fetch All Podcasts" click
document
  .getElementById("fetch-podcasts-btn")
  .addEventListener("click", renderPodcastList);

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
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m12 19-7-7 7-7"></path>
          <path d="M19 12H5"></path>
        </svg>
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
                  ? `
                <a href="${podcast.googleCal}" target="_blank" style="display: flex; align-items: center; gap: 0.5rem;">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect width="18" height="18" x="3" y="4" rx="2" ry="2"></rect>
                    <line x1="16" x2="16" y1="2" y2="6"></line>
                    <line x1="8" x2="8" y1="2" y2="6"></line>
                    <line x1="3" x2="21" y1="10" y2="10"></line>
                  </svg>
                  Calendar Link
                </a>`
                  : `
                <p style="display: flex; align-items: center; gap: 0.5rem;">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect width="18" height="18" x="3" y="4" rx="2" ry="2"></rect>
                    <line x1="16" x2="16" y1="2" y2="6"></line>
                    <line x1="8" x2="8" y1="2" y2="6"></line>
                    <line x1="3" x2="21" y1="10" y2="10"></line>
                  </svg>
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
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"></path>
              </svg>
              Facebook
            </a>`
                : ""
            }
            ${
              podcast.socialMedia && podcast.socialMedia[1]
                ? `<a href="${podcast.socialMedia[1]}" target="_blank" class="social-link">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect width="20" height="20" x="2" y="2" rx="5" ry="5"></rect>
                <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
                <line x1="17.5" x2="17.51" y1="6.5" y2="6.5"></line>
              </svg>
              Instagram
            </a>`
                : ""
            }
            ${
              podcast.socialMedia && podcast.socialMedia[2]
                ? `<a href="${podcast.socialMedia[2]}" target="_blank" class="social-link">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path>
                <rect width="4" height="12" x="2" y="9"></rect>
                <circle cx="4" cy="4" r="2"></circle>
              </svg>
              LinkedIn
            </a>`
                : ""
            }
            ${
              podcast.socialMedia && podcast.socialMedia[3]
                ? `<a href="${podcast.socialMedia[3]}" target="_blank" class="social-link">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z"></path>
              </svg>
              Twitter
            </a>`
                : ""
            }
            ${
              podcast.socialMedia && podcast.socialMedia[4]
                ? `<a href="${podcast.socialMedia[4]}" target="_blank" class="social-link">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z"></path>
              </svg>
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
