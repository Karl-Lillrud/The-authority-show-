import { fetchRSSData } from "../requests/podcastRequests.js";
import { sendInvitationEmail } from "../requests/invitationRequests.js";
import { registerEpisode } from "../requests/episodeRequest.js";

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const darkModeToggle = document.getElementById("dark-mode-toggle");
  const goToEmailSection = document.getElementById("goToEmailSection");
  const podNameSection = document.getElementById("pod-name-section");
  const podNameForm = document.getElementById("podNameForm");
  const podRssInput = document.getElementById("podRss");
  const podNameInput = document.getElementById("podName");
  const creditsContainer = document.getElementById("creditsContainer");
  const podcastPreviewContainer = document.getElementById("podcast-preview");
  const episodesCarouselContainer =
    document.getElementById("episodes-carousel");
  const episodesSlider = document.getElementById("episodes-slider");
  const prevEpisodesBtn = document.getElementById("prev-episodes");
  const nextEpisodesBtn = document.getElementById("next-episodes");

  let currentRssData = null;
  let currentlyPlayingAudio = null;
  let currentlyPlayingId = null;

  // Dark Mode Toggle
  if (darkModeToggle) {
    darkModeToggle.addEventListener("click", () => {
      document.body.classList.toggle("dark-mode");

      // Update moon/sun emoji based on dark mode state
      if (document.body.classList.contains("dark-mode")) {
        darkModeToggle.textContent = "☀️"; // Sun for dark mode
      } else {
        darkModeToggle.textContent = "🌙"; // Moon for light mode
      }
    });
  }

  // RSS Feed Input Handler
  if (podRssInput) {
    podRssInput.addEventListener(
      "input",
      debounce(async function () {
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
            if (podNameInput) {
              podNameInput.value = rssData.title;
            }

            // Display podcast preview if container exists
            if (podcastPreviewContainer) {
              displayPodcastPreview(rssData);
            }

            // Display episodes carousel
            if (episodesCarouselContainer && episodesSlider) {
              displayEpisodesCarousel(rssData.episodes || []);
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
      }, 500)
    );
  }

  // Go to Email Section Button
  if (goToEmailSection) {
    goToEmailSection.addEventListener("click", async () => {
      const podName = podNameInput ? podNameInput.value.trim() : "";
      const podRss = podRssInput ? podRssInput.value.trim() : "";

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

    // Find Spotify and Apple Podcast links
    const spotifyLink = rssData.socialMedia?.find(
      (social) =>
        social.url.includes("spotify.com") || social.platform === "spotify"
    );

    const appleLink = rssData.socialMedia?.find(
      (social) =>
        social.url.includes("apple.com/podcast") || social.platform === "apple"
    );

    // Format social media links
    const socialMediaLinks =
      rssData.socialMedia && rssData.socialMedia.length > 0
        ? rssData.socialMedia
            .filter(
              (social) =>
                !social.url.includes("spotify.com") &&
                !social.url.includes("apple.com/podcast")
            )
            .map((social) => {
              const platform = social.platform || "website";
              const icon = getPlatformIcon(platform);
              return `
            <a href="${
              social.url
            }" target="_blank" class="social-link ${platform}">
              <i class="${icon}"></i>
              ${capitalizeFirstLetter(platform)}
            </a>
          `;
            })
            .join("")
        : "";

    // Build the complete podcast preview HTML
    podcastPreviewContainer.innerHTML = `
      <div class="podcast-header">
        <img src="${
          rssData.imageUrl || "/placeholder.svg?height=300&width=300"
        }" alt="${rssData.title}" class="podcast-cover">
        <div class="podcast-info">
          <h2 class="podcast-title">${rssData.title}</h2>
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
              (rssData.episodes || []).length
            } Episodes</span>
          </div>
          <div class="podcast-actions">
            ${
              spotifyLink
                ? `<a href="${spotifyLink.url}" target="_blank" class="podcast-action-btn spotify"><i class="fab fa-spotify"></i> Spotify</a>`
                : ""
            }
            ${
              appleLink
                ? `<a href="${appleLink.url}" target="_blank" class="podcast-action-btn apple"><i class="fab fa-apple"></i> Apple Podcasts</a>`
                : ""
            }
            ${
              rssData.link
                ? `<a href="${rssData.link}" target="_blank" class="podcast-action-btn"><i class="fas fa-globe"></i> Website</a>`
                : ""
            }
          </div>
        </div>
      </div>
      <div class="podcast-body">
        ${
          rssData.description
            ? `
          <div class="podcast-description">${rssData.description}</div>
        `
            : ""
        }
        
        ${
          socialMediaLinks
            ? `
          <h3 class="podcast-section-title">Connect</h3>
          <div class="social-links">
            ${socialMediaLinks}
          </div>
        `
            : ""
        }
      </div>
    `;
  }

  // Function to display episodes in a horizontal carousel
  function displayEpisodesCarousel(episodes) {
    if (!episodesCarouselContainer || !episodesSlider || episodes.length === 0)
      return;

    episodesCarouselContainer.classList.remove("hidden");
    episodesSlider.innerHTML = "";

    // Create episode cards
    episodes.forEach((episode, index) => {
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
      const episodeId = `episode-${index}-${Date.now()}`;

      // Create episode card
      const episodeCard = document.createElement("div");
      episodeCard.className = "episode-card";
      episodeCard.dataset.episodeId = episodeId;

      episodeCard.innerHTML = `
        <div class="episode-image-container">
          <img src="${
            episode.image ||
            currentRssData.imageUrl ||
            "/placeholder.svg?height=300&width=300"
          }" alt="${episode.title}" class="episode-image">
          <div class="episode-play-overlay">
            <button class="episode-play-btn" data-audio-url="${
              episode.audio?.url
            }" data-episode-id="${episodeId}">
              <i class="fas fa-play"></i>
            </button>
          </div>
          <div class="now-playing" id="now-playing-${episodeId}">
            <span class="pulse"></span>Now Playing
          </div>
        </div>
        <div class="episode-content">
          <h3 class="episode-title">${episode.title}</h3>
          <div class="episode-meta">
            <span>${formattedDate}</span>
            ${formattedDuration ? `<span>${formattedDuration}</span>` : ""}
          </div>
          <div class="episode-description" id="desc-${episodeId}">${
        episode.description || "No description available."
      }</div>
          <div class="episode-actions">
            <button class="episode-btn primary" data-audio-url="${
              episode.audio?.url
            }" data-episode-id="${episodeId}">
              <i class="fas fa-play"></i> Play
            </button>
            <button class="episode-btn secondary toggle-description" data-desc-id="desc-${episodeId}">
              <i class="fas fa-ellipsis-h"></i> More
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

      episodesSlider.appendChild(episodeCard);
    });

    // Setup episode interactions
    setupEpisodeInteractions();

    // Setup carousel navigation
    setupCarouselNavigation();
  }

  // Function to setup episode interactions
  function setupEpisodeInteractions() {
    // Play buttons
    const playButtons = document.querySelectorAll(
      ".episode-play-btn, .episode-btn.primary"
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
            ? '<i class="fas fa-chevron-up"></i> Less'
            : '<i class="fas fa-ellipsis-h"></i> More';
        }
      });
    });
  }

  // Function to setup carousel navigation
  function setupCarouselNavigation() {
    if (!prevEpisodesBtn || !nextEpisodesBtn || !episodesSlider) return;

    // Scroll amount (width of one episode card + gap)
    const scrollAmount = 320; // 300px card width + 20px gap

    prevEpisodesBtn.addEventListener("click", () => {
      episodesSlider.scrollBy({
        left: -scrollAmount,
        behavior: "smooth"
      });
    });

    nextEpisodesBtn.addEventListener("click", () => {
      episodesSlider.scrollBy({
        left: scrollAmount,
        behavior: "smooth"
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
            button.innerHTML = '<i class="fas fa-play"></i> Play';
          } else if (button.classList.contains("episode-play-btn")) {
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
            button.innerHTML = '<i class="fas fa-pause"></i> Pause';
          } else if (button.classList.contains("episode-play-btn")) {
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
              button.innerHTML = '<i class="fas fa-play"></i> Play';
            } else if (button.classList.contains("episode-play-btn")) {
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

  // Helper function to get platform icon
  function getPlatformIcon(platform) {
    const icons = {
      twitter: "fab fa-twitter",
      facebook: "fab fa-facebook-f",
      instagram: "fab fa-instagram",
      youtube: "fab fa-youtube",
      linkedin: "fab fa-linkedin-in",
      website: "fas fa-globe",
      spotify: "fab fa-spotify",
      apple: "fab fa-apple"
    };
    return icons[platform.toLowerCase()] || "fas fa-link";
  }

  // Helper function to capitalize first letter
  function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  }

  // Debounce function to prevent too many API calls
  function debounce(func, wait) {
    let timeout;
    return function (...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), wait);
    };
  }
});
