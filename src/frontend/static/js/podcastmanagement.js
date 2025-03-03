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
    const requiredFields = [
      { name: "podName", value: podName },
      { name: "email", value: email },
      { name: "category", value: category }
    ];

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
    const googleCal =
      document.getElementById("google-cal")?.value.trim() || null;
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
        setTimeout(
          () => (window.location.href = responseData.redirect_url),
          2500
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
      button.addEventListener("click", (e) => {
        const podcastId = e.target.closest("button").dataset.id;
        deletePodcast(podcastId);
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

async function viewPodcast(podcastId) {
  try {
    const response = await fetchPodcast(podcastId);
    // Assuming your API returns the podcast in response.podcast
    const podcast = response.podcast;
    // Use your pre-existing function to pre-populate the form fields
    displayPodcastDetails(podcast);
    // Show the form with details and hide the podcast list
    document.querySelector(".form-box").style.display = "block";
    document.getElementById("podcast-list").style.display = "none";
  } catch (error) {
    showAlert("Podcast not found", "red");
  }
}
