import { fetchRSSData } from "../requests/podcastRequests.js";
import { sendInvitationEmail } from "../requests/invitationRequests.js";
import { registerEpisode } from "../requests/episodeRequest.js";

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

  let currentRssData = null;
  let currentEpisodeIndex = 0;
  const episodesPerPage = 6;
  let currentlyPlayingAudio = null;
  let currentlyPlayingId = null;

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
            podcastPreviewContainer.innerHTML = `
              <div class="loading-container">
                <div class="loading-spinner"></div>
                <div class="loading-text">Loading podcast data...</div>
              </div>
            `;
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
        } catch (error) {
          console.error("Error processing RSS feed:", error);
          if (podcastPreviewContainer) {
            podcastPreviewContainer.innerHTML = `
              <div class="error-container">
                <strong>Error loading podcast:</strong> ${error.message}
              </div>
            `;
          }
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
          author: rssData.author
        };

        console.log("Sending invitation email with complete podcast data");
        const response = await sendInvitationEmail(
          podName,
          podRss,
          imageUrl,
          podcastData
        );

        // Save episodes to the server
        const podcastId = response.podcastId;
        const episodes = rssData.episodes || [];
        for (const episode of episodes) {
          await registerEpisode({
            podcastId: podcastId,
            title: episode.title,
            description: episode.description,
            pubDate: episode.pubDate,
            duration: episode.duration,
            audioUrl: episode.audio.url,
            fileSize: episode.audio.length,
            fileType: episode.audio.type,
            guid: episode.guid,
            season: episode.seasonNumber,
            episode: episode.episodeNumber,
            episodeType: episode.episodeType,
            explicit: episode.explicit,
            imageUrl: episode.image
          });
        }

        // Redirect to dashboard and set a flag to show the popup
        sessionStorage.setItem("showWelcomePopup", "true");
        window.location.href = "/dashboard"; // Redirects to the dashboard
      } catch (error) {
        console.error("Error processing podcast data:", error);
        alert("Something went wrong. Please try again.");
      }
    });
  }

  // Function to display podcast preview with enhanced UI
  function displayPodcastPreview(rssData) {
    if (!podcastPreviewContainer) return;

    // Get social media icons based on platform
    const getSocialIcon = (platform) => {
      const icons = {
        twitter: "fa-twitter",
        facebook: "fa-facebook-f",
        instagram: "fa-instagram",
        youtube: "fa-youtube",
        linkedin: "fa-linkedin-in",
        website: "fa-globe"
      };
      return icons[platform] || "fa-link";
    };

    // Format social media links
    const socialMediaHtml =
      rssData.socialMedia && rssData.socialMedia.length > 0
        ? `<div class="social-media-links">
          ${rssData.socialMedia
            .map(
              (social) =>
                `<a href="${social.url}" target="_blank" class="social-link ${
                  social.platform
                }">
              <i class="fab ${getSocialIcon(social.platform)}"></i>
              ${
                social.platform.charAt(0).toUpperCase() +
                social.platform.slice(1)
              }
            </a>`
            )
            .join("")}
        </div>`
        : "";

    // Format episodes for gallery view
    const episodes = rssData.episodes || [];
    const displayedEpisodes = episodes.slice(0, episodesPerPage);

    const episodesHtml =
      displayedEpisodes.length > 0
        ? `<div class="episodes-gallery">
          ${displayedEpisodes
            .map((episode, index) => {
              // Format date
              const pubDate = new Date(episode.pubDate);
              const formattedDate = isNaN(pubDate)
                ? episode.pubDate
                : pubDate.toLocaleDateString();

              // Format duration
              let formattedDuration = episode.duration;
              if (episode.duration) {
                // Try to convert seconds to MM:SS format if it's just a number
                if (
                  !isNaN(episode.duration) &&
                  !episode.duration.includes(":")
                ) {
                  const minutes = Math.floor(
                    Number.parseInt(episode.duration) / 60
                  );
                  const seconds = Number.parseInt(episode.duration) % 60;
                  formattedDuration = `${minutes}:${seconds
                    .toString()
                    .padStart(2, "0")}`;
                }
              }

              // Generate unique ID for this episode
              const episodeId = `episode-${index}-${Date.now()}`;

              return `
              <div class="episode-card" data-episode-id="${episodeId}">
                <div class="episode-image-container">
                  <img src="${episode.image || rssData.imageUrl}" alt="${
                episode.title
              }" class="episode-image">
                  <div class="episode-play-button" data-audio-url="${
                    episode.audio?.url
                  }" data-episode-id="${episodeId}">
                    <i class="fas fa-play"></i>
                  </div>
                  <div class="now-playing" id="now-playing-${episodeId}">
                    <span class="pulse"></span>Now Playing
                  </div>
                </div>
                <div class="episode-content">
                  <h3 class="episode-title">${episode.title}</h3>
                  <div class="episode-meta">
                    <span class="episode-date"><i class="far fa-calendar-alt"></i> ${formattedDate}</span>
                    ${
                      formattedDuration
                        ? `<span class="episode-duration"><i class="far fa-clock"></i> ${formattedDuration}</span>`
                        : ""
                    }
                  </div>
                  <div class="episode-description" id="desc-${episodeId}">${
                episode.description
              }</div>
                  <div class="episode-actions">
                    <button class="episode-button primary" data-audio-url="${
                      episode.audio?.url
                    }" data-episode-id="${episodeId}">
                      <i class="fas fa-play"></i>Play Episode
                    </button>
                    <button class="episode-button secondary toggle-description" data-desc-id="desc-${episodeId}">
                      <i class="fas fa-ellipsis-h"></i>
                    </button>
                  </div>
                  <div class="audio-player" id="player-${episodeId}">
                    <audio controls>
                      <source src="${episode.audio?.url}" type="${
                episode.audio?.type || "audio/mpeg"
              }">
                      Your browser does not support the audio element.
                    </audio>
                  </div>
                </div>
              </div>
            `;
            })
            .join("")}
        </div>`
        : '<div class="no-episodes">No episodes found for this podcast.</div>';

    // Load more button if there are more episodes
    const loadMoreButton =
      episodes.length > episodesPerPage
        ? `<div class="load-more-container">
          <button id="load-more-episodes" class="load-more-btn">
            Load More Episodes <i class="fas fa-chevron-down"></i>
          </button>
        </div>`
        : "";

    // Build the complete podcast preview HTML
    podcastPreviewContainer.innerHTML = `
      <div class="podcast-container">
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
            <div class="podcast-meta">
              ${
                rssData.category
                  ? `<span class="podcast-meta-item"><i class="fas fa-tag"></i> ${rssData.category}</span>`
                  : ""
              }
              ${
                rssData.language
                  ? `<span class="podcast-meta-item"><i class="fas fa-globe"></i> ${rssData.language}</span>`
                  : ""
              }
              <span class="podcast-meta-item"><i class="fas fa-microphone"></i> ${
                episodes.length
              } Episodes</span>
            </div>
          </div>
        </div>
        <div class="podcast-body">
          ${
            rssData.description
              ? `<div class="podcast-description">${rssData.description}</div>`
              : ""
          }
          
          ${
            socialMediaHtml
              ? `
            <h3 class="podcast-section-title">Connect</h3>
            ${socialMediaHtml}
          `
              : ""
          }
          
          <h3 class="podcast-section-title">Episodes</h3>
          ${episodesHtml}
          ${loadMoreButton}
        </div>
      </div>
    `;

    // Add event listeners for episode interactions
    setupEpisodeInteractions();

    // Add event listener for load more button
    const loadMoreBtn = document.getElementById("load-more-episodes");
    if (loadMoreBtn) {
      loadMoreBtn.addEventListener("click", loadMoreEpisodes);
    }
  }

  // Function to load more episodes
  function loadMoreEpisodes() {
    if (!currentRssData || !currentRssData.episodes) return;

    currentEpisodeIndex += episodesPerPage;
    const episodes = currentRssData.episodes;

    // If no more episodes to load, hide the button
    if (currentEpisodeIndex >= episodes.length) {
      const loadMoreBtn = document.getElementById("load-more-episodes");
      if (loadMoreBtn) {
        loadMoreBtn.parentElement.remove();
      }
      return;
    }

    // Get the next batch of episodes
    const nextEpisodes = episodes.slice(
      currentEpisodeIndex,
      currentEpisodeIndex + episodesPerPage
    );
    const episodesGallery = document.querySelector(".episodes-gallery");

    if (episodesGallery && nextEpisodes.length > 0) {
      // Format and append new episodes
      nextEpisodes.forEach((episode, index) => {
        // Format date
        const pubDate = new Date(episode.pubDate);
        const formattedDate = isNaN(pubDate)
          ? episode.pubDate
          : pubDate.toLocaleDateString();

        // Format duration
        let formattedDuration = episode.duration;
        if (episode.duration) {
          if (!isNaN(episode.duration) && !episode.duration.includes(":")) {
            const minutes = Math.floor(Number.parseInt(episode.duration) / 60);
            const seconds = Number.parseInt(episode.duration) % 60;
            formattedDuration = `${minutes}:${seconds
              .toString()
              .padStart(2, "0")}`;
          }
        }

        // Generate unique ID for this episode
        const episodeId = `episode-${
          currentEpisodeIndex + index
        }-${Date.now()}`;

        // Create episode card element
        const episodeCard = document.createElement("div");
        episodeCard.className = "episode-card";
        episodeCard.dataset.episodeId = episodeId;

        episodeCard.innerHTML = `
          <div class="episode-image-container">
            <img src="${episode.image || currentRssData.imageUrl}" alt="${
          episode.title
        }" class="episode-image">
            <div class="episode-play-button" data-audio-url="${
              episode.audio?.url
            }" data-episode-id="${episodeId}">
              <i class="fas fa-play"></i>
            </div>
            <div class="now-playing" id="now-playing-${episodeId}">
              <span class="pulse"></span>Now Playing
            </div>
          </div>
          <div class="episode-content">
            <h3 class="episode-title">${episode.title}</h3>
            <div class="episode-meta">
              <span class="episode-date"><i class="far fa-calendar-alt"></i> ${formattedDate}</span>
              ${
                formattedDuration
                  ? `<span class="episode-duration"><i class="far fa-clock"></i> ${formattedDuration}</span>`
                  : ""
              }
            </div>
            <div class="episode-description" id="desc-${episodeId}">${
          episode.description
        }</div>
            <div class="episode-actions">
              <button class="episode-button primary" data-audio-url="${
                episode.audio?.url
              }" data-episode-id="${episodeId}">
                <i class="fas fa-play"></i>Play Episode
              </button>
              <button class="episode-button secondary toggle-description" data-desc-id="desc-${episodeId}">
                <i class="fas fa-ellipsis-h"></i>
              </button>
            </div>
            <div class="audio-player" id="player-${episodeId}">
              <audio controls>
                <source src="${episode.audio?.url}" type="${
          episode.audio?.type || "audio/mpeg"
        }">
                Your browser does not support the audio element.
              </audio>
            </div>
          </div>
        `;

        episodesGallery.appendChild(episodeCard);
      });

      // Setup interactions for newly added episodes
      setupEpisodeInteractions();

      // Hide load more button if no more episodes
      if (currentEpisodeIndex + episodesPerPage >= episodes.length) {
        const loadMoreBtn = document.getElementById("load-more-episodes");
        if (loadMoreBtn) {
          loadMoreBtn.parentElement.remove();
        }
      }
    }
  }

  // Function to setup episode interactions
  function setupEpisodeInteractions() {
    // Play buttons
    const playButtons = document.querySelectorAll(
      ".episode-play-button, .episode-button.primary"
    );
    playButtons.forEach((button) => {
      button.addEventListener("click", function () {
        const audioUrl = this.dataset.audioUrl;
        const episodeId = this.dataset.episodeId;

        if (audioUrl && episodeId) {
          playEpisode(episodeId, audioUrl);
        }
      });
    });

    // Toggle description buttons
    const toggleButtons = document.querySelectorAll(".toggle-description");
    toggleButtons.forEach((button) => {
      button.addEventListener("click", function () {
        const descId = this.dataset.descId;
        const descElement = document.getElementById(descId);

        if (descElement) {
          descElement.classList.toggle("expanded");
          this.innerHTML = descElement.classList.contains("expanded")
            ? '<i class="fas fa-chevron-up"></i>'
            : '<i class="fas fa-ellipsis-h"></i>';
        }
      });
    });
  }

  // Function to play episode audio
  function playEpisode(episodeId, audioUrl) {
    // Stop currently playing audio if any
    if (currentlyPlayingAudio) {
      currentlyPlayingAudio.pause();

      // Reset previous now playing indicator
      if (currentlyPlayingId) {
        const prevIndicator = document.getElementById(
          `now-playing-${currentlyPlayingId}`
        );
        if (prevIndicator) {
          prevIndicator.classList.remove("active");
        }

        // Reset play button icon
        const prevPlayButtons = document.querySelectorAll(
          `[data-episode-id="${currentlyPlayingId}"]`
        );
        prevPlayButtons.forEach((button) => {
          if (button.classList.contains("primary")) {
            button.innerHTML = '<i class="fas fa-play"></i>Play Episode';
          } else {
            button.innerHTML = '<i class="fas fa-play"></i>';
          }
        });

        // Hide audio player
        const prevPlayer = document.getElementById(
          `player-${currentlyPlayingId}`
        );
        if (prevPlayer) {
          prevPlayer.classList.remove("active");
        }
      }
    }

    // If clicking the same episode that's already playing, just stop it
    if (episodeId === currentlyPlayingId) {
      currentlyPlayingAudio = null;
      currentlyPlayingId = null;
      return;
    }

    // Show audio player for this episode
    const audioPlayer = document.getElementById(`player-${episodeId}`);
    if (audioPlayer) {
      audioPlayer.classList.add("active");
      const audio = audioPlayer.querySelector("audio");

      if (audio) {
        audio.play();
        currentlyPlayingAudio = audio;
        currentlyPlayingId = episodeId;

        // Update play button icons
        const playButtons = document.querySelectorAll(
          `[data-episode-id="${episodeId}"]`
        );
        playButtons.forEach((button) => {
          if (button.classList.contains("primary")) {
            button.innerHTML = '<i class="fas fa-pause"></i>Pause Episode';
          } else {
            button.innerHTML = '<i class="fas fa-pause"></i>';
          }
        });

        // Show now playing indicator
        const nowPlaying = document.getElementById(`now-playing-${episodeId}`);
        if (nowPlaying) {
          nowPlaying.classList.add("active");
        }

        // Handle audio ending
        audio.onended = () => {
          // Reset play button icons
          playButtons.forEach((button) => {
            if (button.classList.contains("primary")) {
              button.innerHTML = '<i class="fas fa-play"></i>Play Episode';
            } else {
              button.innerHTML = '<i class="fas fa-play"></i>';
            }
          });

          // Hide now playing indicator
          if (nowPlaying) {
            nowPlaying.classList.remove("active");
          }

          currentlyPlayingAudio = null;
          currentlyPlayingId = null;
        };
      }
    }
  }
});
