import {
  addPodcast,
  fetchPodcasts,
  fetchPodcast,
  updatePodcast,
  deletePodcast
} from "../../../static/requests/podcastRequests.js";
import {
  fetchEpisodesByPodcast,
  fetchEpisode
} from "../../../static/requests/episodeRequest.js";
import {
  showNotification,
  updateEditButtons,
  shared
} from "./podcastmanagement.js";
import { createPlayButton, playAudio } from "./episode-functions.js";
import { renderEpisodeDetail } from "./episode-functions.js";

// Function to set image source with fallback
function setImageSource(imgElement, customSrc, mockSrc) {
  imgElement.src = customSrc || mockSrc;
}

// Function to reset the podcast form
function resetForm() {
  const form = document.getElementById("register-podcast-form");
  form.reset();
  shared.selectedPodcastId = null;
}

// Function to display podcast details in the form
function displayPodcastDetails(podcast) {
  // Set form title for editing
  document.querySelector(".form-title").textContent = "Edit Podcast";
  document.querySelector(".save-btn").textContent = "Update Podcast";

  // Fill in form fields
  const podNameEl = document.getElementById("pod-name");
  if (podNameEl) podNameEl.value = podcast.podName || "";

  // Removed: ownerName and hostName
  // New fields: Author and Language
  const podAuthorEl = document.getElementById("pod-author");
  if (podAuthorEl) podAuthorEl.value = podcast.author || "";

  const podLanguageEl = document.getElementById("pod-language");
  if (podLanguageEl) podLanguageEl.value = podcast.language || "";

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

  const taglineEl = document.getElementById("tagline");
  if (taglineEl) taglineEl.value = podcast.tagline || "";

  const hostBioEl = document.getElementById("host-bio");
  if (hostBioEl) hostBioEl.value = podcast.hostBio || "";

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
  if (tiktokEl) twitterEl.value = podcast.socialMedia?.[4] || "";

  const pinterestEl = document.getElementById("pinterest");
  if (pinterestEl) pinterestEl.value = podcast.socialMedia?.[5] || "";

  const youtubeEl = document.getElementById("youtube");
  if (youtubeEl) youtubeEl.value = podcast.socialMedia?.[6] || "";
}

// Function to view podcast details
export async function viewPodcast(podcastId) {
  try {
    const response = await fetchPodcast(podcastId);
    if (response && response.podcast) {
      shared.selectedPodcastId = podcastId;
      renderPodcastDetail(response.podcast);
      document.getElementById("podcast-list").style.display = "none";
      document.getElementById("podcast-detail").style.display = "block";
    } else {
      showNotification("Error", "Failed to load podcast details.", "error");
    }
  } catch (error) {
    console.error("Error viewing podcast:", error);
    showNotification("Error", "Failed to load podcast details.", "error");
  }
}

// Function to render podcast list
export async function renderPodcastList() {
  try {
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

    podcasts.forEach(async (podcast) => {
      const podcastCard = document.createElement("div");
      podcastCard.className = "podcast-card";

      // Use imageUrl if available, otherwise allow user to upload an image
      const imageUrl =
        podcast.logoUrl || podcast.imageUrl || "default-image.png";

      // Create the basic podcast card structure
      podcastCard.innerHTML = `
      <div class="podcast-content">
        <div class="podcast-image" style="background-image: url('${imageUrl}')" data-id="${
        podcast._id
      }"></div>
        <div class="podcast-info">
          <div class="podcast-header">
            <div>
              <h2 class="podcast-title">${podcast.podName}</h2>
              <p class="podcast-meta"><span>Category:</span> ${
                podcast.category || "Uncategorized"
              }</p>
              <p class="podcast-meta"><span>Author:</span> ${
                podcast.author || "Not specified"
              }</p>
              <p class="podcast-meta"><span>Language:</span> ${
                podcast.language || "Not specified"
              }</p>
            </div>
            <div class="podcast-actions">
              <button class="action-btn view-btn" title="View podcast details" data-id="${
                podcast._id
              }">
                ${shared.svgpodcastmanagement.view}
              </button>
              <button class="action-btn delete-btn-home" title="Delete podcast" data-id="${
                podcast._id
              }">
                <span class="icon">${shared.svgpodcastmanagement.delete}</span>
              </button>
            </div>
          </div>
          <p class="podcast-description"><strong>Description: </strong>${
            podcast.description || "No description available."
          }</p>
          
          <!-- Add episodes preview section -->
          <div class="podcast-episodes-preview" id="episodes-preview-${
            podcast._id
          }">
            <h4 class="episodes-preview-title">Episodes</h4>
            <div class="episodes-loading">Loading episodes...</div>
          </div>
        </div>
      </div>
      <div class="podcast-footer">
        <button class="landing-page-btn" data-id="${
          podcast._id
        }">Landing Page</button>
        <button class="view-details-btn" data-id="${
          podcast._id
        }">View Details</button>
      </div>`;

      podcastListElement.appendChild(podcastCard);

      // Redirect to the landing page with the specific podcastId
      const landingPageBtn = podcastCard.querySelector(".landing-page-btn");
      landingPageBtn.addEventListener("click", (e) => {
        const podcastId = e.target.dataset.id; // Get podcast ID
        window.location.href = `/landingpage/${podcastId}`;
      });

      // Fetch episodes for this podcast and add them to the preview
      try {
        const episodes = await fetchEpisodesByPodcast(podcast._id);
        const episodesPreviewEl = document.getElementById(
          `episodes-preview-${podcast._id}`
        );

        if (episodesPreviewEl) {
          if (episodes && episodes.length > 0) {
            const episodesContainer = document.createElement("div");
            episodesContainer.className = "episodes-container";

            // Show up to 3 episodes in the preview
            const previewEpisodes = episodes.slice(0, 3);

            previewEpisodes.forEach((episode) => {
              const episodeItem = document.createElement("div");
              episodeItem.className = "podcast-episode-item";
              episodeItem.setAttribute("data-episode-id", episode._id);

              // Ensure publishDate is formatted correctly
              const publishDate = episode.publishDate
                ? new Date(episode.publishDate).toLocaleDateString()
                : "No date";

              // Create episode content div
              const episodeContent = document.createElement("div");
              episodeContent.className = "podcast-episode-content";
              episodeContent.innerHTML = `
              <div class="podcast-episode-title">${episode.title}</div>
              <div class="podcast-episode-description">${
                episode.description || "No description available."
              }</div>
            `;

              // Create episode actions div with play button and date
              const episodeActions = document.createElement("div");
              episodeActions.className = "podcast-episode-actions";

              // Create play button if audio URL exists
              if (episode.audioUrl) {
                const playButton = createPlayButton("small");
                playButton.addEventListener("click", (e) => {
                  e.stopPropagation();
                  playAudio(episode.audioUrl, episode.title);
                });
                episodeActions.appendChild(playButton);
              }

              // Add date
              const dateDiv = document.createElement("div");
              dateDiv.className = "podcast-episode-date";
              dateDiv.textContent = publishDate;
              episodeActions.appendChild(dateDiv);

              // Assemble the episode item
              episodeItem.appendChild(episodeContent);
              episodeItem.appendChild(episodeActions);

              // Make episode item navigate to episode details
              episodeItem.addEventListener("click", async (e) => {
                if (!e.target.closest(".podcast-episode-play")) {
                  try {
                    const episodeId = episode._id; // Get the episode ID
                    const response = await fetchEpisode(episodeId); // Fetch full episode details
                    if (response) {
                      renderEpisodeDetail({
                        ...response,
                        podcast_id: podcast._id // Pass podcast ID
                      });
                      document.getElementById("podcast-list").style.display =
                        "none";
                      document.getElementById("podcast-detail").style.display =
                        "block";
                    } else {
                      showNotification(
                        "Error",
                        "Failed to load episode details.",
                        "error"
                      );
                    }
                  } catch (error) {
                    console.error("Error fetching episode details:", error);
                    showNotification(
                      "Error",
                      "Failed to load episode details.",
                      "error"
                    );
                  }
                }
              });

              episodesContainer.appendChild(episodeItem);
            });

            // Replace loading message with episodes
            episodesPreviewEl.querySelector(".episodes-loading").remove();
            episodesPreviewEl.appendChild(episodesContainer);

            // Add "View all" link if there are more than 3 episodes
            if (episodes.length > 3) {
              const viewAllLink = document.createElement("div");
              viewAllLink.className = "view-all-link";
              viewAllLink.textContent = `View all ${episodes.length} episodes`;

              viewAllLink.addEventListener("click", (e) => {
                e.stopPropagation();
                viewPodcast(podcast._id);
              });

              episodesPreviewEl.appendChild(viewAllLink);
            }
          } else {
            episodesPreviewEl.innerHTML =
              '<p class="no-episodes-message">No episodes available</p>';
          }
        }
      } catch (error) {
        console.error("Error fetching episodes for podcast preview:", error);
        const episodesPreviewEl = document.getElementById(
          `episodes-preview-${podcast._id}`
        );
        if (episodesPreviewEl) {
          episodesPreviewEl.innerHTML =
            '<p class="episodes-error-message">Failed to load episodes</p>';
        }
      }

      // Add event listener to the image to view details
      podcastCard
        .querySelector(".podcast-image")
        .addEventListener("click", (e) => {
          const podcastId = e.target.getAttribute("data-id");
          if (podcastId) {
            viewPodcast(podcastId);
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
      button.addEventListener("click", (e) => {
        const podcastId = e.target.closest("button").getAttribute("data-id");
        if (podcastId) {
          viewPodcast(podcastId);
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

// Function to render podcast detail
export function renderPodcastDetail(podcast) {
  const podcastDetailElement = document.getElementById("podcast-detail");
  const imageUrl = podcast.logoUrl || podcast.imageUrl || "default-image.png";

  podcastDetailElement.innerHTML = `
  <div class="detail-header">
    <button class="back-btn" id="back-to-list">
      ${shared.svgpodcastmanagement.back}
      Back to podcasts
    </button>
    
    <!-- Add top-right action buttons -->
    <div class="top-right-actions">
      <button class="action-btn edit-btn" id="edit-podcast-btn" data-id="${
        podcast._id
      }">
        ${shared.svgpodcastmanagement.edit}
      </button>
    </div>
  </div>
  <div class="detail-content">
    <div class="detail-image" style="background-image: url('${imageUrl}')"></div>
    <!-- Episodes container with title outside scroll area -->
    <div id="episodes-list" class="episodes-list">
      <h3 class="detail-section-title">Episodes</h3>
      <div id="episodes-container" class="episodes-scroll-container"></div>
    </div>
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
          <h3>Author</h3>
          <p>${podcast.author || "Not specified"}</p>
        </div>
        <div class="detail-item">
          <h3>Language</h3>
          <p>${podcast.language || "Not specified"}</p>
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
                ? `<a href="${podcast.googleCal}" target="_blank" class="calendar-link">
                  ${shared.svgpodcastmanagement.calendar}
                  Calendar Link
                </a>`
                : `<p class="calendar-link">
                  ${shared.svgpodcastmanagement.calendar}
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
                ${shared.svgpodcastmanagement.facebook}
                Facebook
              </a>`
              : ""
          }
          ${
            podcast.socialMedia && podcast.socialMedia[1]
              ? `<a href="${podcast.socialMedia[1]}" target="_blank" class="social-link">
                ${shared.svgpodcastmanagement.instagram}
                Instagram
              </a>`
              : ""
          }
          ${
            podcast.socialMedia && podcast.socialMedia[2]
              ? `<a href="${podcast.socialMedia[2]}" target="_blank" class="social-link">
                ${shared.svgpodcastmanagement.linkedin}
                LinkedIn
              </a>`
              : ""
          }
          ${
            podcast.socialMedia && podcast.socialMedia[3]
              ? `<a href="${podcast.socialMedia[3]}" target="_blank" class="social-link">
                ${shared.svgpodcastmanagement.twitter}
                Twitter
              </a>`
              : ""
          }
          ${
            podcast.socialMedia && podcast.socialMedia[4]
              ? `<a href="${podcast.socialMedia[4]}" target="_blank" class="social-link">
                ${shared.svgpodcastmanagement.tiktok}
                TikTok
              </a>`
              : ""
          }
        </div>
      </div>
      <div class="detail-actions">
        <button class="delete-btn" id="delete-podcast-btn" data-id="${
          podcast._id
        }">
          <span class="icon">${shared.svgpodcastmanagement.delete}</span>
          Delete Podcast
        </button>
      </div>
    </div>
  </div>
  `;

  // Back button event listener
  document.getElementById("back-to-list").addEventListener("click", () => {
    // Hide podcast details view
    document.getElementById("podcast-detail").style.display = "none";
    // Re-render the podcast list to include the new episode
    renderPodcastList();
    // Show podcast list view
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
        shared.selectedPodcastId = podcastId;
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
      const episodesContainer = document.getElementById("episodes-container");
      episodesContainer.innerHTML = "";

      if (episodes && episodes.length) {
        const episodesListDiv = document.createElement("div");
        episodesListDiv.className = "episodes-container";

        episodes.forEach((ep) => {
          const episodeCard = document.createElement("div");
          episodeCard.className = "episode-card";
          episodeCard.setAttribute("data-episode-id", ep._id);

          const publishDate = ep.publishDate
            ? new Date(ep.publishDate).toLocaleDateString()
            : "No date";

          // Convert duration from seconds to minutes and seconds
          const durationMinutes = Math.floor(ep.duration / 60);
          const durationSeconds = ep.duration % 60;
          const formattedDuration = `${durationMinutes}m ${durationSeconds}s`;

          const description = ep.description
            ? ep.description
            : "No description available.";

          // Create content container for title, date, and description
          const contentDiv = document.createElement("div");
          contentDiv.className = "episode-content";

          contentDiv.innerHTML = `
          <div class="episode-title">${ep.title}</div>
          <div class="episode-meta">
            <span>Published: ${publishDate}</span>
            <span> • ${formattedDuration}</span>
          </div>
          <div class="episode-description">${description}</div>
        `;

          // Create actions container
          const actionsDiv = document.createElement("div");
          actionsDiv.className = "episode-actions";

          // Add play button if audio URL exists
          if (ep.audioUrl) {
            const playButton = createPlayButton();
            playButton.addEventListener("click", (e) => {
              e.stopPropagation();
              playAudio(ep.audioUrl, ep.title);
            });
            actionsDiv.appendChild(playButton);
          }

          // Create view button
          const viewButton = document.createElement("button");
          viewButton.className = "view-episode-btn";
          viewButton.textContent = "View";

          // Add click event to view button
          viewButton.addEventListener("click", (e) => {
            e.stopPropagation(); // Prevent triggering the card click
            renderEpisodeDetail(ep);
          });

          actionsDiv.appendChild(viewButton);

          // Add elements to card
          episodeCard.appendChild(contentDiv);
          episodeCard.appendChild(actionsDiv);

          // Add click event to card (excluding the button)
          episodeCard.addEventListener("click", (e) => {
            if (
              !e.target.closest(".episode-play-btn") &&
              !e.target.closest(".view-episode-btn")
            ) {
              renderEpisodeDetail(ep);
            }
          });

          episodesListDiv.appendChild(episodeCard);
        });

        episodesContainer.appendChild(episodesListDiv);
      } else {
        const noEpisodes = document.createElement("p");
        noEpisodes.className = "no-episodes-message";
        noEpisodes.textContent = "No episodes available.";
        episodesContainer.appendChild(noEpisodes);
      }
    })
    .catch((error) => {
      console.error("Error fetching episodes:", error);
    });

  // Update edit buttons after rendering
  updateEditButtons();
}

// Function to handle podcast form submission
function handlePodcastFormSubmission() {
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
      author: document.getElementById("pod-author")?.value.trim() || "",
      language: document.getElementById("pod-language")?.value.trim() || "",
      rssFeed: document.getElementById("pod-rss")?.value.trim() || "",
      googleCal: document.getElementById("google-cal")?.value.trim() || null,
      guestUrl: document.getElementById("guest-form-url")?.value.trim() || null,
      email,
      description: document.getElementById("description")?.value.trim() || "",
      bannerUrl: document.getElementById("banner")?.value.trim() || "",
      tagline: document.getElementById("tagline")?.value.trim() || "",
      hostBio: document.getElementById("host-bio")?.value.trim() || "",
      hostImage: document.getElementById("host-image")?.value.trim() || "",
      // the logoUrl field will be replaced if a logo is uploaded

      category,
      socialMedia: [
        document.getElementById("facebook")?.value.trim() || " ",
        document.getElementById("instagram")?.value.trim() || " ",
        document.getElementById("linkedin")?.value.trim() || " ",
        document.getElementById("twitter")?.value.trim() || " ",
        document.getElementById("tiktok")?.value.trim() || " ",
        document.getElementById("pinterest")?.value.trim() || " ",
        document.getElementById("youtube")?.value.trim() || " "
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
        if (shared.selectedPodcastId) {
          responseData = await updatePodcast(
            shared.selectedPodcastId,
            updatedData
          );
          if (!responseData.error) {
            showNotification(
              "Success",
              "Podcast updated successfully!",
              "success"
            );
            // Update the podcast details in the DOM
            renderPodcastDetail({
              ...updatedData,
              _id: shared.selectedPodcastId
            });
            document.getElementById("form-popup").style.display = "none";
            document.getElementById("podcast-detail").style.display = "block";
          }
        } else {
          responseData = await addPodcast(updatedData);
          if (!responseData.error) {
            showNotification(
              "Success",
              "Podcast added successfully!",
              "success"
            );
            document.getElementById("form-popup").style.display = "none";
            document.getElementById("podcast-list").style.display = "flex";
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
          resetForm();
          renderPodcastList();
        }
      } catch (error) {
        console.error("Error:", error);
        showNotification(
          "Error",
          shared.selectedPodcastId
            ? "Failed to update podcast."
            : "Failed to add podcast.",
          "error"
        );
      }
    }

    // Check for a logo, banner and host image file and convert it to a Base64 string if one is selected
    const logoInput = document.getElementById("logo");
    const bannerInput = document.getElementById("banner");
    const hostImageInput = document.getElementById("host-image");

    async function handleFileInput(inputElement, dataProperty) {
      return new Promise((resolve) => {
        if (inputElement && inputElement.files[0]) {
          const file = inputElement.files[0];
          const reader = new FileReader();
          reader.onloadend = () => {
            data[dataProperty] = reader.result; // update with new image
            resolve(true);
          };
          reader.readAsDataURL(file);
        } else {
          // If editing and no new image is selected, do not overwrite the existing property
          if (shared.selectedPodcastId) {
            delete data[dataProperty];
          }
          resolve(false);
        }
      });
    }

    async function processInputs() {
      const logoPromise = handleFileInput(logoInput, "logoUrl");
      const bannerPromise = handleFileInput(bannerInput, "bannerUrl");
      const hostImagePromise = handleFileInput(hostImageInput, "hostImage");

      // Wait for all file inputs to be processed
      const [logoChanged, bannerChanged, hostImageChanged] = await Promise.all([
        logoPromise,
        bannerPromise,
        hostImagePromise
      ]);

      // Submit podcast data
      await submitPodcast(data);
    }

    // Start processing the inputs
    processInputs();
  });
}

// Function to render podcast options in a select element
export function renderPodcastSelection(podcasts) {
  const podcastSelect = document.getElementById("podcast-select");
  podcastSelect.innerHTML = ""; // Clear existing options

  // Add a default "Select Podcast" option
  const defaultOption = document.createElement("option");
  defaultOption.value = "";
  defaultOption.textContent = "Select Podcast";
  podcastSelect.appendChild(defaultOption);

  podcasts.forEach((podcast) => {
    const option = document.createElement("option");
    option.value = podcast._id;
    option.textContent = podcast.podName;
    podcastSelect.appendChild(option);
  });
}

// Initialize podcast functions
export function initPodcastFunctions() {
  renderPodcastList();

  // Show form for adding a podcast
  document.getElementById("add-podcast-btn").addEventListener("click", () => {
    resetForm();
    shared.selectedPodcastId = null;
    document.getElementById("form-popup").style.display = "flex";
    document.querySelector(".form-title").textContent = "Add New Podcast";
    document.querySelector(".save-btn").textContent = "Save Podcast";
  });

  // Close the form popup
  document.getElementById("close-form-popup").addEventListener("click", () => {
    document.getElementById("form-popup").style.display = "none";
    document.getElementById("podcast-detail").style.display = "block";
  });

  // Cancel button in form
  document.getElementById("cancel-form-btn").addEventListener("click", () => {
    document.getElementById("form-popup").style.display = "none";
    document.getElementById("podcast-detail").style.display = "none"; // Hide podcast detail
    document.getElementById("podcast-list").style.display = "flex"; // Show podcast list
  });

  // Setup podcast form submission
  handlePodcastFormSubmission();
}
