import { fetchRSSData } from "../requests/podcastRequests.js";
import { sendInvitationEmail } from "../requests/invitationRequests.js";

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const darkModeToggle = document.getElementById("dark-mode-toggle");
  const goToEmailSection = document.getElementById("goToEmailSection");
  const skipToDashboard = document.getElementById("skipToDashboard");
  const podNameSection = document.getElementById("pod-name-section");
  const emailSection = document.getElementById("email-section");
  const podNameForm = document.getElementById("podNameForm");
  const podRssInput = document.getElementById("podRss");
  const podNameInput = document.getElementById("podName");
  const creditsContainer = document.getElementById("creditsContainer");
  const welcomePopup = document.getElementById("welcome-popup");
  const closeWelcomePopup = document.getElementById("close-welcome-popup");
  const podcastPreviewContainer = document.getElementById("podcast-preview");
  const episodesContainer = document.getElementById("episodes-container");
  const loadMoreEpisodesBtn = document.getElementById("load-more-episodes");

  let currentRssData = null;
  let currentEpisodeIndex = 0;
  const episodesPerPage = 5;

  // Dark Mode Toggle
  darkModeToggle.addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");

    // Update moon/sun emoji based on dark mode state
    if (document.body.classList.contains("dark-mode")) {
      darkModeToggle.textContent = "☀️"; // Sun for dark mode
    } else {
      darkModeToggle.textContent = "🌙"; // Moon for light mode
    }
  });

  // RSS Feed Input Handler
  if (podRssInput) {
    podRssInput.addEventListener("input", async function () {
      const rssUrl = this.value.trim();
      if (rssUrl) {
        try {
          // Show loading indicator
          if (podcastPreviewContainer) {
            podcastPreviewContainer.innerHTML =
              '<div class="loading">Loading podcast data...</div>';
            podcastPreviewContainer.classList.remove("hidden");
          }

          // Fetch RSS data
          const rssData = await fetchRSSData(rssUrl);
          currentRssData = rssData;

          // Set the podcast name
          podNameInput.value = rssData.title;

          // Display podcast preview if container exists
          if (podcastPreviewContainer) {
            displayPodcastPreview(rssData);
          }

          // Display episodes if container exists
          if (episodesContainer) {
            displayEpisodes(rssData.episodes, 0, episodesPerPage);

            // Show load more button if there are more episodes
            if (
              loadMoreEpisodesBtn &&
              rssData.episodes.length > episodesPerPage
            ) {
              loadMoreEpisodesBtn.classList.remove("hidden");
            } else if (loadMoreEpisodesBtn) {
              loadMoreEpisodesBtn.classList.add("hidden");
            }
          }
        } catch (error) {
          console.error("Error processing RSS feed:", error);
          if (podcastPreviewContainer) {
            podcastPreviewContainer.innerHTML = `<div class="error">Error loading podcast: ${error.message}</div>`;
          }
        }
      }
    });
  }

  // Load more episodes button
  if (loadMoreEpisodesBtn) {
    loadMoreEpisodesBtn.addEventListener("click", () => {
      if (currentRssData && currentRssData.episodes) {
        currentEpisodeIndex += episodesPerPage;
        displayEpisodes(
          currentRssData.episodes,
          currentEpisodeIndex,
          episodesPerPage
        );

        // Hide button if no more episodes
        if (
          currentEpisodeIndex + episodesPerPage >=
          currentRssData.episodes.length
        ) {
          loadMoreEpisodesBtn.classList.add("hidden");
        }
      }
    });
  }

  // Go to Email Section Button
  if (goToEmailSection) {
    goToEmailSection.addEventListener("click", async () => {
      const podName = podNameInput ? podNameInput.value.trim() : "";
      const podRss = podRssInput ? podRssInput.value.trim() : "";

      console.log("Podcast Name:", podName);
      console.log("Podcast RSS:", podRss);

      if (!podName || !podRss) {
        alert("Please enter all required fields: Podcast Name and RSS URL.");
        return;
      }

      try {
        console.log("Fetching RSS data");
        const rssData = await fetchRSSData(podRss);
        podNameInput.value = rssData.title; // Set the title correctly
        const imageUrl = rssData.imageUrl; // Get the imageUrl from RSS

        // Prepare complete podcast data to send
        const podcastData = {
          podName: podName,
          podRss: podRss,
          imageUrl: imageUrl,
          description: rssData.description,
          socialMedia: rssData.socialMedia,
          category: rssData.category,
          author: rssData.author,
          episodes: rssData.episodes // Include episodes data
        };

        console.log("Sending invitation email with complete podcast data");
        await sendInvitationEmail(podName, podRss, imageUrl, podcastData);

        // Redirect to dashboard and set a flag to show the popup
        sessionStorage.setItem("showWelcomePopup", "true");
        window.location.href = "/dashboard"; // Redirects to the dashboard
      } catch (error) {
        console.error("Error sending invitation email:", error);
        alert("Something went wrong. Please try again.");
      }
    });
  }

  // Function to display podcast preview
  function displayPodcastPreview(rssData) {
    if (!podcastPreviewContainer) return;

    const socialMediaHtml =
      rssData.socialMedia && rssData.socialMedia.length > 0
        ? `<div class="social-media">
          <h3>Social Media</h3>
          <ul>${rssData.socialMedia
            .map(
              (social) =>
                `<li><a href="${social.url}" target="_blank">${social.platform}</a></li>`
            )
            .join("")}
          </ul>
        </div>`
        : "";

    podcastPreviewContainer.innerHTML = `
      <div class="podcast-preview-card">
        <div class="podcast-header">
          ${
            rssData.imageUrl
              ? `<img src="${rssData.imageUrl}" alt="${rssData.title}" class="podcast-image">`
              : ""
          }
          <div class="podcast-info">
            <h2>${rssData.title}</h2>
            ${
              rssData.author
                ? `<p class="podcast-author">By ${rssData.author}</p>`
                : ""
            }
            ${
              rssData.category
                ? `<p class="podcast-category">${rssData.category}</p>`
                : ""
            }
          </div>
        </div>
        ${
          rssData.description
            ? `<div class="podcast-description">${rssData.description}</div>`
            : ""
        }
        ${socialMediaHtml}
      </div>
    `;
  }

  // Function to display episodes
  function displayEpisodes(episodes, startIndex, count) {
    if (!episodesContainer) return;

    const endIndex = Math.min(startIndex + count, episodes.length);
    const episodesToShow = episodes.slice(startIndex, endIndex);

    const episodesHtml = episodesToShow
      .map((episode) => {
        // Format date
        const pubDate = new Date(episode.pubDate);
        const formattedDate = isNaN(pubDate)
          ? episode.pubDate
          : pubDate.toLocaleDateString();

        // Format duration
        let formattedDuration = episode.duration;
        if (episode.duration) {
          // Try to convert seconds to MM:SS format if it's just a number
          if (!isNaN(episode.duration) && !episode.duration.includes(":")) {
            const minutes = Math.floor(Number.parseInt(episode.duration) / 60);
            const seconds = Number.parseInt(episode.duration) % 60;
            formattedDuration = `${minutes}:${seconds
              .toString()
              .padStart(2, "0")}`;
          }
        }

        return `
        <div class="episode-card">
          <div class="episode-header">
            ${
              episode.image
                ? `<img src="${episode.image}" alt="${episode.title}" class="episode-image">`
                : ""
            }
            <div class="episode-info">
              <h3>${episode.title}</h3>
              <div class="episode-meta">
                <span class="episode-date">${formattedDate}</span>
                ${
                  formattedDuration
                    ? `<span class="episode-duration">${formattedDuration}</span>`
                    : ""
                }
              </div>
            </div>
          </div>
          <div class="episode-description">${episode.description}</div>
          ${
            episode.audio && episode.audio.url
              ? `<div class="episode-audio">
              <audio controls>
                <source src="${episode.audio.url}" type="${
                  episode.audio.type || "audio/mpeg"
                }">
                Your browser does not support the audio element.
              </audio>
            </div>`
              : ""
          }
          ${
            episode.link
              ? `<a href="${episode.link}" target="_blank" class="episode-link">View Episode</a>`
              : ""
          }
        </div>
      `;
      })
      .join("");

    // If this is the first batch, replace content, otherwise append
    if (startIndex === 0) {
      episodesContainer.innerHTML = episodesHtml;
    } else {
      episodesContainer.innerHTML += episodesHtml;
    }
  }
});
