import { fetchRSSData, addPodcast } from "../../requests/podcastRequests.js" // Updated import
import { sendInvitationEmail } from "../../requests/invitationRequests.js"
import { registerEpisode } from "../../requests/episodeRequest.js"
import { createLoadingBar } from "../../js/components/loading-bar.js" // Updated import
import { fetchAccount, updateAccount } from "/static/requests/accountRequests.js";

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  initWelcomePopup();
  const darkModeToggle = document.getElementById("dark-mode-toggle")
  const goToEmailSection = document.getElementById("goToEmailSection")
  const podNameSection = document.getElementById("pod-name-section")
  const podNameForm = document.getElementById("podNameForm")
  const podRssInput = document.getElementById("podRss")
  const podNameInput = document.getElementById("podName")
  const creditsContainer = document.getElementById("creditsContainer")
  const podcastContainer = document.getElementById("podcast-container")

  let currentRssData = null
  let currentlyPlayingAudio = null
  let currentlyPlayingId = null
  let loadingBar

  // Initialize loading bar
  loadingBar = createLoadingBar()

  // Dark Mode Toggle
  if (darkModeToggle) {
    darkModeToggle.addEventListener("click", () => {
      document.body.classList.toggle("dark-mode")

      // Update moon/sun emoji based on dark mode state
      if (document.body.classList.contains("dark-mode")) {
        darkModeToggle.textContent = "☀️" // Sun for dark mode
      } else {
        darkModeToggle.textContent = "🌙" // Moon for light mode
      }
    })
  }

  // RSS Feed Input Handler
  if (podRssInput) {
    podRssInput.addEventListener(
      "input",
      debounce(async function () {
        const rssUrl = this.value.trim()
        if (rssUrl) {
          try {
            // Show loading indicator
            if (podcastContainer) {
              podcastContainer.innerHTML = `
                <div class="loading-container">
                  <div class="loading-spinner"></div>
                  <div class="loading-text">Loading podcast data...</div>
                </div>
              `
              podcastContainer.classList.remove("hidden")
            }

            // Fetch RSS data
            const rssData = await fetchRSSData(rssUrl)
            console.log("Fetched RSS data:", rssData) // Added log
            currentRssData = rssData

            // Set the podcast name
            if (podNameInput) {
              podNameInput.value = rssData.title
            }

            // Display podcast preview if container exists
            if (podcastContainer) {
              displayPodcastPreview(rssData)
            }
          } catch (error) {
            console.error("Error processing RSS feed:", error)
            if (podcastContainer) {
              podcastContainer.innerHTML = `
                <div class="error-container">
                  <strong>Error loading podcast:</strong> ${error.message}
                </div>
              `
            }
          }
        }
      }, 500),
    )
  }

  // Go to Email Section Button
  if (goToEmailSection) {
    goToEmailSection.addEventListener("click", async () => {
      // Add loading spinner on Next button
      goToEmailSection.disabled = true
      goToEmailSection.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...'

      const podName = podNameInput ? podNameInput.value.trim() : ""
      const podRss = podRssInput ? podRssInput.value.trim() : ""

      if (!podName || !podRss) {
        alert("Please enter all required fields: Podcast Name and RSS URL.")
        // Restore button if validation fails
        goToEmailSection.disabled = false
        goToEmailSection.innerHTML = "Next"
        return
      }

      try {
        // Show loading popup
        loadingBar.showLoadingPopup()

        console.log("Fetching RSS data")
        const rssData = await fetchRSSData(podRss)
        podNameInput.value = rssData.title // Set the title correctly
        const imageUrl = rssData.imageUrl // Get the imageUrl from RSS

        // Prepare complete podcast data to send
        const podcastData = {
          podName: podName,
          rssFeed: podRss,
          imageUrl: imageUrl,
          description: rssData.description,
          socialMedia: rssData.socialMedia,
          category: rssData.categories?.[0]?.main || "", // Use main category
          author: rssData.author,
          title: rssData.title,
          language: rssData.language,
          copyright_info: rssData.copyright_info,
          link: rssData.link, // Added
          generator: rssData.generator, // Added
          lastBuildDate: rssData.lastBuildDate, // Added
          itunesType: rssData.itunesType, // Added
          itunesOwner: rssData.itunesOwner, // Added
          ownerName: rssData.itunesOwner?.name || null,
          hostName: rssData.hostName || null,
          googleCal: rssData.googleCal || null,
          podUrl: rssData.podUrl || null,
          guestUrl: rssData.guestUrl || null,
          email: rssData.itunesOwner?.email || null,
          logoUrl: rssData.logoUrl || null,
        }

        // Process first step - Registering episode
        loadingBar.processStep(0)

        console.log("Sending podcast data:", podcastData) // Added log
        // Process second step - Sending data
        loadingBar.processStep(1)

        const response = await addPodcast(podcastData) // Updated function call
        console.log("Received response from addPodcast:", response) // Added log

        // Process third step - Received response
        loadingBar.processStep(2)

        // Save episodes to the server
        const podcastId = response.podcast_id // Ensure correct field name
        const episodes = rssData.episodes || []
        for (const episode of episodes) {
          console.log("Registering episode:", episode) // Added log
          try {
            const registerResponse = await registerEpisode({
              podcastId: podcastId,
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
              status: 'published',
              isImported: true // ✅ Explicitly mark as imported
            })
            
            console.log("Episode registered successfully:", registerResponse) // Added log
          } catch (error) {
            console.error("Error registering episode:", error) // Added log
          }
        }

        // Process fourth step - Episode registered successfully
        loadingBar.processStep(3)

        // Send invitation email
        try {
          console.log("Sending invitation email") // Added log
          await sendInvitationEmail()
          console.log("Invitation email sent successfully") // Added log
        } catch (error) {
          console.error("Error sending invitation email:", error) // Added log
        }

        // Short delay to show the completed loading bar
        setTimeout(() => {
          // Hide loading popup
          loadingBar.hideLoadingPopup()

          // Redirect to podcastmanagement (updated redirection)
          sessionStorage.setItem("showWelcomePopup", "true")
          window.location.href = "/podcastmanagement" // Redirect now to podcastmanagement
        }, 1000)
      } catch (error) {
        // On error, restore button state and hide loading popup
        loadingBar.hideLoadingPopup()
        goToEmailSection.disabled = false
        goToEmailSection.innerHTML = "Next"
        console.error("Error processing podcast data:", error)
        alert("Something went wrong. Please try again.")
      }
    })
  }

  // Calendar Connection Button
  const connectCalendarButton = document.getElementById("connectCalendar")
  if (connectCalendarButton) {
    connectCalendarButton.addEventListener("click", (event) => {
      event.preventDefault()

      try {
        // Redirect the user to the backend endpoint, which will handle the OAuth redirection
        window.location.href = "/connect_google_calendar"
      } catch (error) {
        console.error("Error connecting to Google Calendar:", error)
        alert("Failed to connect to Google Calendar. Please try again.")
      }
    })
  }

  // Save Google refresh token after OAuth flow
  const urlParams = new URLSearchParams(window.location.search)
  const googleToken = urlParams.get("googleToken")
  if (googleToken) {
    try {
      fetch("/save_google_refresh_token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refreshToken: googleToken }), // Save as refreshToken
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.message) {
            console.log("Google refresh token saved successfully.")
          } else {
            console.error("Error saving Google refresh token:", data.error)
          }
        })
    } catch (error) {
      console.error("Error saving Google refresh token:", error)
    }
  }

  // Function to display podcast preview with enhanced UI
  function displayPodcastPreview(rssData) {
    if (!podcastContainer) return

    // Find Spotify and Apple Podcast links
    const spotifyLink = rssData.socialMedia?.find(
      (social) => social.url.includes("spotify.com") || social.platform === "spotify",
    )
    const appleLink = rssData.socialMedia?.find(
      (social) => social.url.includes("apple.com/podcast") || social.platform === "apple",
    )

    // Format social media links
    const socialMediaLinks =
      rssData.socialMedia && rssData.socialMedia.length > 0
        ? rssData.socialMedia
            .filter((social) => !social.url.includes("spotify.com") && !social.url.includes("apple.com/podcast"))
            .map((social) => {
              const platform = social.platform || "website"
              const icon = getPlatformIcon(platform)
              return `
              <a href="${social.url}" target="_blank" class="social-link ${platform}" rel="noreferrer">
                <i class="${icon}"></i>
                ${capitalizeFirstLetter(platform)}
              </a>
            `
            })
            .join("")
        : ""

    // Format categories with subcategories
    const categoriesHtml = rssData.categories
      ? rssData.categories
          .map((cat) => {
            const subCats = cat.subcategories.length > 0 ? ` (${cat.subcategories.join(", ")})` : ""
            return `<span class="podcast-meta-item"><i class="fas fa-tag"></i> ${cat.main}${subCats}</span>`
          })
          .join("")
      : ""

    // Format language display
    const languageDisplay = rssData.language === "en" ? "English" : rssData.language

    // Format episodes
    const episodesHtml = rssData.episodes
      ? rssData.episodes
          .map((episode, index) => {
            // Format date
            const pubDate = new Date(episode.pubDate)
            const formattedDate = isNaN(pubDate) ? episode.pubDate : pubDate.toLocaleDateString()

            // Format duration from seconds to HH:MM:SS
            let formattedDuration = ""
            if (episode.duration) {
              const hours = Math.floor(episode.duration / 3600)
              const minutes = Math.floor((episode.duration % 3600) / 60)
              const seconds = episode.duration % 60
              formattedDuration = `${hours > 0 ? `${hours}:` : ""}${minutes
                .toString()
                .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`
            }

            // Generate unique ID for this episode
            const episodeId = `episode-${index}-${Date.now()}`

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
            `
          })
          .join("")
      : ""

    // Build the complete HTML for the unified container
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
    `

    // Setup episode interactions after rendering
    setupEpisodeInteractions()
  }

  async function initWelcomePopup() {
    try {
      const wrapper = await fetchAccount();
      const user = wrapper.account;
      if (user.isFirstLogin) {
        const welcomePopup = document.getElementById("welcome-popup");
        const closeWelcomePopup = document.getElementById("close-welcome-popup");
        const getStartedBtn = document.getElementById("get-started-btn");
        if (!welcomePopup) return;
        welcomePopup.style.display = "flex";
  
        closeWelcomePopup.addEventListener("click", () => {
          welcomePopup.style.display = "none";
          disableWelcomePopup();
        });
  
        getStartedBtn.addEventListener("click", () => {
          welcomePopup.style.display = "none";
          disableWelcomePopup();
        });
  
        welcomePopup.addEventListener("click", (e) => {
          if (e.target === welcomePopup) {
            welcomePopup.style.display = "none";
            disableWelcomePopup();
          }
        });
            return;
      }
    } catch (error) {
      console.error("Error initializing welcome popup:", error);
    }
  }
  
  async function disableWelcomePopup() {
    try {
      const data = { isFirstLogin: false }  
      await updateAccount(data);
    } catch (error) {
      console.error("Error disabling welcome popup:", error);
    }
  }

  // Function to setup episode interactions
  function setupEpisodeInteractions() {
    // Play buttons
    const playButtons = document.querySelectorAll(".episode-play-btn, .episode-btn.primary")
    playButtons.forEach((button) => {
      button.addEventListener("click", function () {
        const audioUrl = this.dataset.audioUrl
        const episodeId = this.dataset.episodeId

        if (audioUrl && episodeId) {
          playEpisode(episodeId, audioUrl)
        }
      })
    })

    // Toggle description buttons
    const toggleButtons = document.querySelectorAll(".toggle-description")
    toggleButtons.forEach((button) => {
      button.addEventListener("click", function () {
        const descId = this.dataset.descId
        const descElement = document.getElementById(descId)

        if (descElement) {
          descElement.classList.toggle("expanded")
          this.innerHTML = descElement.classList.contains("expanded")
            ? '<i class="fas fa-chevron-up"></i> Less'
            : '<i class="fas fa-ellipsis-h"></i> More'
        }
      })
    })
  }

  // Function to play episode audio
  function playEpisode(episodeId, audioUrl) {
    // Stop currently playing audio if any
    if (currentlyPlayingAudio) {
      currentlyPlayingAudio.pause()

      // Reset previous now playing indicator
      if (currentlyPlayingId) {
        const prevIndicator = document.getElementById(`now-playing-${currentlyPlayingId}`)
        if (prevIndicator) {
          prevIndicator.classList.remove("active")
        }

        // Reset play button icon
        const prevPlayButtons = document.querySelectorAll(`[data-episode-id="${currentlyPlayingId}"]`)
        prevPlayButtons.forEach((button) => {
          if (button.classList.contains("primary")) {
            button.innerHTML = '<i class="fas fa-play"></i> Play'
          } else if (button.classList.contains("episode-play-btn")) {
            button.innerHTML = '<i class="fas fa-play"></i>'
          }
        })

        // Hide audio player
        const prevPlayer = document.getElementById(`player-${currentlyPlayingId}`)
        if (prevPlayer) {
          prevPlayer.classList.remove("active")
        }
      }
    }

    // If clicking the same episode that's already playing, just stop it
    if (episodeId === currentlyPlayingId) {
      currentlyPlayingAudio = null
      currentlyPlayingId = null
      return
    }

    // Show audio player for this episode
    const audioPlayer = document.getElementById(`player-${episodeId}`)
    if (audioPlayer) {
      audioPlayer.classList.add("active")
      const audio = audioPlayer.querySelector("audio")

      if (audio) {
        audio.play()
        currentlyPlayingAudio = audio
        currentlyPlayingId = episodeId

        // Update play button icons
        const playButtons = document.querySelectorAll(`[data-episode-id="${episodeId}"]`)
        playButtons.forEach((button) => {
          if (button.classList.contains("primary")) {
            button.innerHTML = '<i class="fas fa-pause"></i> Pause'
          } else if (button.classList.contains("episode-play-btn")) {
            button.innerHTML = '<i class="fas fa-pause"></i>'
          }
        })

        // Show now playing indicator
        const nowPlaying = document.getElementById(`now-playing-${episodeId}`)
        if (nowPlaying) {
          nowPlaying.classList.add("active")
        }

        // Handle audio ending
        audio.onended = () => {
          // Reset play button icons
          playButtons.forEach((button) => {
            if (button.classList.contains("primary")) {
              button.innerHTML = '<i class="fas fa-play"></i> Play'
            } else if (button.classList.contains("episode-play-btn")) {
              button.innerHTML = '<i class="fas fa-play"></i>'
            }
          })

          // Hide now playing indicator
          if (nowPlaying) {
            nowPlaying.classList.remove("active")
          }

          currentlyPlayingAudio = null
          currentlyPlayingId = null
        }
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
      apple: "fab fa-apple",
    }
    return icons[platform.toLowerCase()] || "fas fa-link"
  }

  // Helper function to capitalize first letter
  function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1)
  }

  // Debounce function to prevent too many API calls
  function debounce(func, wait) {
    let timeout
    return function (...args) {
      clearTimeout(timeout)
      timeout = setTimeout(() => func.apply(this, args), wait)
    }
  }
})

function connectGoogleCalendar() {
  // Show loading state
  const connectCalendarButton = document.getElementById("connectCalendar")
  if (connectCalendarButton) {
    connectCalendarButton.disabled = true
    connectCalendarButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...'
  }

  // Redirect to the Google OAuth flow
  fetch("/connect_google_calendar")
    .then((response) => {
      if (response.redirected) {
        window.location.href = response.url
      } else {
        return response.json().then((data) => {
          throw new Error(data.error || "Failed to connect to Google Calendar")
        })
      }
    })
    .catch((error) => {
      console.error("Error connecting to Google Calendar:", error)
      alert("Error connecting to Google Calendar: " + error.message)

      // Reset button state
      if (connectCalendarButton) {
        connectCalendarButton.disabled = false
        connectCalendarButton.innerHTML = "Connect Google Calendar"
      }
    })
}

// Add event listener when the DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  const connectCalendarButton = document.getElementById("connectCalendar")
  if (connectCalendarButton) {
    connectCalendarButton.addEventListener("click", (event) => {
      event.preventDefault()
      connectGoogleCalendar()
    })
  }

  // Check for googleToken in URL parameters (after OAuth callback)
  const urlParams = new URLSearchParams(window.location.search)
  const googleToken = urlParams.get("googleToken")

  if (googleToken) {
    console.log("Google Calendar connected successfully!")
    // You can display a success message or update UI elements here
  }
})
