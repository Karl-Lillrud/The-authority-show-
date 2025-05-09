import { fetchRSSData, addPodcast } from "../../requests/podcastRequests.js";
import { sendInvitationEmail } from "../../requests/invitationRequests.js";
import { registerEpisode } from "../../requests/episodeRequest.js";
import { createLoadingBar } from "../../js/components/loading-bar.js";
import { fetchAccount, updateAccount } from "/static/requests/accountRequests.js";

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  initWelcomePopup();
  initCreatepodcastButton();
  const darkModeToggle = document.getElementById("dark-mode-toggle");
  const goToEmailSection = document.getElementById("goToEmailSection");
  const podNameSection = document.getElementById("pod-name-section");
  const podNameForm = document.getElementById("podNameForm");
  const podRssInput = document.getElementById("podRss");
  const podNameInput = document.getElementById("podName");
  const creditsContainer = document.getElementById("creditsContainer");
  const podcastContainer = document.getElementById("podcast-container");

  let currentRssData = null;
  let currentlyPlayingAudio = null;
  let currentlyPlayingId = null;
  let loadingBar;

  // Initialize loading bar
  loadingBar = createLoadingBar();

  // Dark Mode Toggle
  if (darkModeToggle) {
    darkModeToggle.addEventListener("click", () => {
      document.body.classList.toggle("dark-mode");
      if (document.body.classList.contains("dark-mode")) {
        darkModeToggle.textContent = "☀️";
      } else {
        darkModeToggle.textContent = "🌙";
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
            if (podcastContainer) {
              podcastContainer.innerHTML = `
                <div class="loading-container">
                  <div class="loading-spinner"></div>
                  <div class="loading-text">Loading podcast data...</div>
                </div>
              `;
              podcastContainer.classList.remove("hidden");
            }

            const rssData = await fetchRSSData(rssUrl);
            console.log("Fetched RSS data:", rssData);
            currentRssData = rssData;

            if (podNameInput) {
              podNameInput.value = rssData.title;
            }

            if (podcastContainer) {
              displayPodcastPreview(rssData);
            }
          } catch (error) {
            console.error("Error processing RSS feed:", error);
            if (podcastContainer) {
              podcastContainer.innerHTML = `
                <div class="error-container">
                  <strong>Error loading podcast:</strong> ${error.message}
                </div>
              `;
            }
          }
        }
      }, 500),
    );
  }

  // Go to Email Section Button
  if (goToEmailSection) {
    goToEmailSection.addEventListener("click", async () => {
      goToEmailSection.disabled = true;
      goToEmailSection.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

      const podName = podNameInput ? podNameInput.value.trim() : "";
      const podRss = podRssInput ? podRssInput.value.trim() : "";

      if (!podName || !podRss) {
        alert("Please enter all required fields: Podcast Name and RSS URL.");
        goToEmailSection.disabled = false;
        goToEmailSection.innerHTML = "Next";
        return;
      }

      try {
        loadingBar.showLoadingPopup();
        console.log("Fetching RSS data");
        const rssData = await fetchRSSData(podRss);
        podNameInput.value = rssData.title;
        const imageUrl = rssData.imageUrl;

        const podcastData = {
          podName,
          rssFeed: podRss,
          imageUrl,
          description: rssData.description,
          socialMedia: rssData.socialMedia,
          category: rssData.categories?.[0]?.main || "",
          author: rssData.author,
          title: rssData.title,
          language: rssData.language,
          copyright_info: rssData.copyright_info,
          link: rssData.link,
          generator: rssData.generator,
          lastBuildDate: rssData.lastBuildDate,
          itunesType: rssData.itunesType,
          itunesOwner: rssData.itunesOwner,
          ownerName: rssData.itunesOwner?.name || null,
          hostName: rssData.hostName || null,
          googleCal: rssData.googleCal || null,
          podUrl: rssData.podUrl || null,
          guestUrl: rssData.guestUrl || null,
          email: rssData.itunesOwner?.email || null,
          logoUrl: rssData.logoUrl || null,
        };

        loadingBar.processStep(0);
        console.log("Sending podcast data:", podcastData);
        loadingBar.processStep(1);

        const response = await addPodcast(podcastData);
        console.log("Received response from addPodcast:", response);
        loadingBar.processStep(2);

        const podcastId = response.podcast_id;
        const episodes = rssData.episodes || [];
        for (const episode of episodes) {
          console.log("Registering episode:", episode);
          try {
            const registerResponse = await registerEpisode({
              podcastId,
              title: episode.title,
              description: episode.description,
              publishDate: episode.pubDate,
              duration: episode.duration,
              audioUrl: episode.audio.url,
              fileSize: episode.audio.length,
              fileType: episode.audio.type,
              guid: episode.guid,
              season: episode.season || null,
              episode: episode.episode || null,
              episodeType: episode.episodeType || null,
              explicit: episode.explicit || null,
              imageUrl: episode.image || episode.imageUrl || "/placeholder.svg?height=300&width=300",
              keywords: episode.keywords || null,
              chapters: episode.chapters || null,
              link: episode.link || null,
              subtitle: episode.subtitle || null,
              summary: episode.summary || null,
              author: episode.author || null,
              isHidden: episode.isHidden || null,
              status: "published",
              isImported: true,
            });
            console.log("Episode registered successfully:", registerResponse);
          } catch (error) {
            console.error("Error registering episode:", error);
          }
        }

        loadingBar.processStep(3);

        try {
          console.log("Sending invitation email");
          await sendInvitationEmail();
          console.log("Invitation email sent successfully");
        } catch (error) {
          console.error("Error sending invitation email:", error);
        }

        setTimeout(() => {
          loadingBar.hideLoadingPopup();
          sessionStorage.setItem("showWelcomePopup", "true");
          window.location.href = "/podcastmanagement";
        }, 1000);
      } catch (error) {
        loadingBar.hideLoadingPopup();
        goToEmailSection.disabled = false;
        goToEmailSection.innerHTML = "Next";
        console.error("Error processing podcast data:", error);
        alert("Something went wrong. Please try again.");
      }
    });
  }

  // Calendar Connection Button
  const connectCalendarButton = document.getElementById("connectCalendar");
  if (connectCalendarButton) {
    connectCalendarButton.addEventListener("click", (event) => {
      event.preventDefault();
      try {
        window.location.href = "/connect_google_calendar";
      } catch (error) {
        console.error("Error connecting to Google Calendar:", error);
        alert("Failed to connect to Google Calendar. Please try again.");
      }
    });
  }

  // Save Google refresh token after OAuth flow
  const urlParams = new URLSearchParams(window.location.search);
  const googleToken = urlParams.get("googleToken");
  if (googleToken) {
    try {
      fetch("/save_google_refresh_token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refreshToken: googleToken }),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.message) {
            console.log("Google refresh token saved successfully.");
          } else {
            console.error("Error saving Google refresh token:", data.error);
          }
        });
    } catch (error) {
      console.error("Error saving Google refresh token:", error);
    }
  }

  // Function to display podcast preview with enhanced UI
  function displayPodcastPreview(rssData) {
    if (!podcastContainer) return;

    const spotifyLink = rssData.socialMedia?.find(
      (social) => social.url.includes("spotify.com") || social.platform === "spotify",
    );
    const appleLink = rssData.socialMedia?.find(
      (social) => social.url.includes("apple.com/podcast") || social.platform === "apple",
    );

    const socialMediaLinks =
      rssData.socialMedia && rssData.socialMedia.length > 0
        ? rssData.socialMedia
            .filter((social) => !social.url.includes("spotify.com") && !social.url.includes("apple.com/podcast"))
            .map((social) => {
              const platform = social.platform || "website";
              const icon = getPlatformIcon(platform);
              return `
              <a href="${social.url}" target="_blank" class="social-link ${platform}" rel="noreferrer">
                <i class="${icon}"></i>
                ${capitalizeFirstLetter(platform)}
              </a>
            `;
            })
            .join("")
        : "";

    const categoriesHtml = rssData.categories
      ? rssData.categories
          .map((cat) => {
            const subCats = cat.subcategories.length > 0 ? ` (${cat.subcategories.join(", ")})` : "";
            return `<span class="podcast-meta-item"><i class="fas fa-tag"></i> ${cat.main}${subCats}</span>`;
          })
          .join("")
      : "";

    const languageDisplay = rssData.language === "en" ? "English" : rssData.language;

    const episodesHtml = rssData.episodes
      ? rssData.episodes
          .map((episode, index) => {
            const pubDate = new Date(episode.pubDate);
            const formattedDate = isNaN(pubDate) ? episode.pubDate : pubDate.toLocaleDateString();

            let formattedDuration = "";
            if (episode.duration) {
              const hours = Math.floor(episode.duration / 3600);
              const minutes = Math.floor((episode.duration % 3600) / 60);
              const seconds = episode.duration % 60;
              formattedDuration = `${hours > 0 ? `${hours}:` : ""}${minutes
                .toString()
                .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
            }

            const episodeId = `episode-${index}-${Date.now()}`;

            return `
              <div class="episode-card" data-episode-id="${episodeId}">
                <div class="episode-image-container">
                  <img src="${
                    episode.image || "/placeholder.svg?height=300&width=300"
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
                    <span><i class="fas fa-calendar"></i> ${formattedDate}</span>
                    ${formattedDuration ? `<span><i class="fas fa-clock"></i> ${formattedDuration}</span>` : ""}
                    ${
                      episode.season && episode.episode
                        ? `<span><i class="fas fa-list-ol"></i> S${episode.season} E${episode.episode}</span>`
                        : ""
                    }
                    ${
                      episode.explicit === "Yes"
                        ? `<span class="explicit-tag"><i class="fas fa-exclamation-circle"></i> Explicit</span>`
                        : ""
                    }
                  </div>
                  <div class="episode-description" id="desc-${episodeId}">
                    ${episode.summary || episode.description || "No description available."}
                  </div>
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
                      <source src="${episode.audio?.url}" type="${episode.audio?.type || "audio/mpeg"}">
                      Your browser does not support the audio element.
                    </audio>
                  </div>
                </div>
              </div>
            `;
          })
          .join("")
      : "";

    podcastContainer.innerHTML = `
      <div class="podcast-header">
        <img src="${
          rssData.imageUrl || "/placeholder.svg?height=300&width=300"
        }" alt="${rssData.title}" class="podcast-cover">
        <div class="podcast-info">
          <h2 class="podcast-title">${rssData.title}</h2>
          ${rssData.author ? `<p class="podcast-author">By ${rssData.author}</p>` : ""}
          <div class="podcast-meta">
            ${categoriesHtml}
            ${
              rssData.language
                ? `<span class="podcast-meta-item"><i class="fas fa-globe"></i> ${languageDisplay}</span>`
                : ""
            }
            <span class="podcast-meta-item"><i class="fas fa-microphone"></i> ${
              (rssData.episodes || []).length
            } Episodes</span>
          </div>
          <div class="podcast-actions">
            ${
              spotifyLink
                ? `<a href="${spotifyLink.url}" target="_blank" class="podcast-action-btn spotify" rel="noreferrer"><i class="fab fa-spotify"></i> Spotify</a>`
                : ""
            }
            ${
              appleLink
                ? `<a href="${appleLink.url}" target="_blank" class="podcast-action-btn apple" rel="noreferrer"><i class="fab fa-apple"></i> Apple Podcasts</a>`
                : ""
            }
            ${
              rssData.link
                ? `<a href="${rssData.link}" target="_blank" class="podcast-action-btn" rel="noreferrer"><i class="fas fa-globe"></i> Website</a>`
                : ""
            }
          </div>
        </div>
      </div>
      <div class="podcast-content">
        <div class="podcast-details">
          ${rssData.description ? `<div class="podcast-description">${rssData.description}</div>` : ""}
          ${rssData.copyright_info ? `<p class="podcast-copyright">© ${rssData.copyright_info}</p>` : ""}
          ${
            rssData.itunesOwner?.name || rssData.itunesOwner?.email
              ? `
              <h3 class="podcast-section-title">Owner</h3>
              <div class="podcast-owner">
                ${rssData.itunesOwner.name ? `<p><i class="fas fa-user"></i> ${rssData.itunesOwner.name}</p>` : ""}
                ${
                  rssData.itunesOwner.email
                    ? `<p><i class="fas fa-envelope"></i> <a href="mailto:${rssData.itunesOwner.email}">${rssData.itunesOwner.email}</a></p>`
                    : ""
                }
              </div>
            `
              : ""
          }
          ${
            rssData.generator || rssData.lastBuildDate
              ? `
              <h3 class="podcast-section-title">Details</h3>
              <div class="podcast-details">
                ${rssData.generator ? `<p><i class="fas fa-cogs"></i> Generated by: ${rssData.generator}</p>` : ""}
                ${
                  rssData.lastBuildDate
                    ? `<p><i class="fas fa-clock"></i> Last Updated: ${new Date(
                        rssData.lastBuildDate,
                      ).toLocaleString()}</p>`
                    : ""
                }
              </div>
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
        <div class="episodes-list">
          <div class="episodes-header">
            <h2>Episodes</h2>
          </div>
          ${episodesHtml}
        </div>
      </div>
    `;

    setupEpisodeInteractions();
  }

  async function initWelcomePopup() {
    try {
      // Skip if popup was already shown in this session
      if (sessionStorage.getItem("popupShown") === "true") {
        console.log("Popup already shown in this session, skipping.");
        return;
      }

      const wrapper = await fetchAccount();
      const user = wrapper.account;
      const showWelcomePopup = sessionStorage.getItem("showWelcomePopup") === "true";

      // Show popup only if isFirstLogin is true or showWelcomePopup flag is set
      if (user.isFirstLogin || showWelcomePopup) {
        const welcomePopup = document.getElementById("welcome-popup");
        const closeWelcomePopup = document.getElementById("close-welcome-popup");
        const getStartedBtn = document.getElementById("get-started-btn");

        if (!welcomePopup) {
          console.error("Welcome popup element not found");
          return;
        }

        // Mark popup as shown and clear showWelcomePopup flag
        sessionStorage.setItem("popupShown", "true");
        sessionStorage.removeItem("showWelcomePopup");

        welcomePopup.style.display = "flex";

        // Helper function to close popup and update state
        const closePopup = async () => {
          welcomePopup.style.display = "none";
          await disableWelcomePopup();
        };

        // Close button
        closeWelcomePopup.addEventListener("click", closePopup);

        // Get Started button
        getStartedBtn.addEventListener("click", closePopup);

        // Click outside popup
        welcomePopup.addEventListener("click", async (e) => {
          if (e.target === welcomePopup) {
            await closePopup();
          }
        });
      }
    } catch (error) {
      console.error("Error initializing welcome popup:", error);
    }
  }

  async function disableWelcomePopup() {
    try {
      const data = { isFirstLogin: false };
      await updateAccount(data);
      console.log("isFirstLogin set to false");
    } catch (error) {
      console.error("Error disabling welcome popup:", error);
      // Fallback to prevent popup on reload
      sessionStorage.setItem("popupShown", "true");
    }
  }

  function setupEpisodeInteractions() {
    const playButtons = document.querySelectorAll(".episode-play-btn, .episode-btn.primary");
    playButtons.forEach((button) => {
      button.addEventListener("click", function () {
        const audioUrl = this.dataset.audioUrl;
        const episodeId = this.dataset.episodeId;

        if (audioUrl && episodeId) {
          playEpisode(episodeId, audioUrl);
        }
      });
    });

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

  function playEpisode(episodeId, audioUrl) {
    if (currentlyPlayingAudio) {
      currentlyPlayingAudio.pause();
      if (currentlyPlayingId) {
        const prevIndicator = document.getElementById(`now-playing-${currentlyPlayingId}`);
        if (prevIndicator) {
          prevIndicator.classList.remove("active");
        }

        const prevPlayButtons = document.querySelectorAll(`[data-episode-id="${currentlyPlayingId}"]`);
        prevPlayButtons.forEach((button) => {
          if (button.classList.contains("primary")) {
            button.innerHTML = '<i class="fas fa-play"></i> Play';
          } else if (button.classList.contains("episode-play-btn")) {
            button.innerHTML = '<i class="fas fa-play"></i>';
          }
        });

        const prevPlayer = document.getElementById(`player-${currentlyPlayingId}`);
        if (prevPlayer) {
          prevPlayer.classList.remove("active");
        }
      }
    }

    if (episodeId === currentlyPlayingId) {
      currentlyPlayingAudio = null;
      currentlyPlayingId = null;
      return;
    }

    const audioPlayer = document.getElementById(`player-${episodeId}`);
    if (audioPlayer) {
      audioPlayer.classList.add("active");
      const audio = audioPlayer.querySelector("audio");

      if (audio) {
        audio.play();
        currentlyPlayingAudio = audio;
        currentlyPlayingId = episodeId;

        const playButtons = document.querySelectorAll(`[data-episode-id="${episodeId}"]`);
        playButtons.forEach((button) => {
          if (button.classList.contains("primary")) {
            button.innerHTML = '<i class="fas fa-pause"></i> Pause';
          } else if (button.classList.contains("episode-play-btn")) {
            button.innerHTML = '<i class="fas fa-pause"></i>';
          }
        });

        const nowPlaying = document.getElementById(`now-playing-${episodeId}`);
        if (nowPlaying) {
          nowPlaying.classList.add("active");
        }

        audio.onended = () => {
          playButtons.forEach((button) => {
            if (button.classList.contains("primary")) {
              button.innerHTML = '<i class="fas fa-play"></i> Play';
            } else if (button.classList.contains("episode-play-btn")) {
              button.innerHTML = '<i class="fas fa-play"></i>';
            }
          });

          if (nowPlaying) {
            nowPlaying.classList.remove("active");
          }

          currentlyPlayingAudio = null;
          currentlyPlayingId = null;
        };
      }
    }
  }
    
  function getPlatformIcon(platform) {
    const icons = {
      twitter: "fab fa-twitter",
      facebook: "fab fa-facebook-f",
      instagram: "fab fa-instagram",
      youtube: "fab fa-youtube",
      linkedin: "fab fa-linkedin-in",
      website: "fas fa-globe",
      spotify: "fab fa-spotify",
      apple: "fab fa-apple",
    };
    return icons[platform.toLowerCase()] || "fas fa-link";
  }

  function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  }

  function debounce(func, wait) {
    let timeout;
    return function (...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), wait);
    };
  }
});

function initCreatepodcastButton() {
  const createPodcastButton = document.getElementById("createPodcast");
  if (createPodcastButton) {  
      createPodcastButton.addEventListener("click", () => {
      sessionStorage.setItem("Addpodcast", "true");
      window.location.href = "/podcastmanagement";
    });
  }}

function connectGoogleCalendar() {
  const connectCalendarButton = document.getElementById("connectCalendar");
  if (connectCalendarButton) {
    connectCalendarButton.disabled = true;
    connectCalendarButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...';
  }

  fetch("/connect_google_calendar")
    .then((response) => {
      if (response.redirected) {
        window.location.href = response.url;
      } else {
        return response.json().then((data) => {
          throw new Error(data.error || "Failed to connect to Google Calendar");
        });
      }
    })
    .catch((error) => {
      console.error("Error connecting to Google Calendar:", error);
      alert("Error connecting to Google Calendar: " + error.message);

      if (connectCalendarButton) {
        connectCalendarButton.disabled = false;
        connectCalendarButton.innerHTML = "Connect Google Calendar";
      }
    });
}

document.addEventListener("DOMContentLoaded", () => {
  const connectCalendarButton = document.getElementById("connectCalendar");
  if (connectCalendarButton) {
    connectCalendarButton.addEventListener("click", (event) => {
      event.preventDefault();
      connectGoogleCalendar();
    });
  }

  const urlParams = new URLSearchParams(window.location.search);
  const googleToken = urlParams.get("googleToken");

  if (googleToken) {
    console.log("Google Calendar connected successfully!");
  }
});