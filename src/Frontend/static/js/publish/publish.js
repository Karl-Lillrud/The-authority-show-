import { publishEpisode } from "/static/requests/publishRequests.js"
import { fetchEpisode } from "/static/requests/episodeRequest.js"
import { showNotification } from "/static/js/components/notifications.js"
import { fetchPodcasts } from "/static/requests/podcastRequests.js"
import { fetchEpisodesByPodcast } from "/static/requests/episodeRequest.js"

// Placeholder for SVGs that might be used on the publish page or in shared components like header/footer
// if they are not handled by a global script loaded in base.html.
// Example: const svgPublish = { headerLogo: '<svg>...</svg>', userIcon: '<svg>...</svg>' };
const svgPublish = {}

function initializePublishPageSVGs() {
  // This function can be used to inject SVGs into placeholders.
  // For example, if your header (from base.html) has <span class="icon-placeholder" data-icon="headerLogo"></span>:
  // document.querySelectorAll('.icon-placeholder').forEach(el => {
  //     const iconName = el.dataset.icon;
  //     if (svgPublish[iconName]) {
  //         el.innerHTML = svgPublish[iconName];
  //     }
  // });
  // console.log("Attempted to initialize publish page SVGs.");
}

document.addEventListener("DOMContentLoaded", () => {
  const podcastSelect = document.getElementById("podcast-select")
  const episodeSelect = document.getElementById("episode-select")
  const episodeDetailsPreview = document.getElementById("episode-details-preview")
  const previewTitle = document.getElementById("preview-title")
  const previewDescription = document.getElementById("preview-description")
  const previewImage = document.getElementById("preview-image")
  const previewAudio = document.getElementById("preview-audio")
  const publishNowBtn = document.getElementById("publish-now-btn")
  const publishStatusDiv = document.getElementById("publish-status")
  const publishLogPre = document.getElementById("publish-log")
  const platformToggles = document.querySelectorAll('.platform-toggle input[type="checkbox"]')
  const publishNotes = document.getElementById("publish-notes")

  // Load podcasts into the dropdown using /get_podcasts
  async function loadPodcasts() {
    try {
      podcastSelect.innerHTML = '<option value="">Loading podcasts...</option>'
      const podcastData = await fetchPodcasts()
      const podcasts = podcastData.podcast || []
      podcastSelect.innerHTML = '<option value="">-- Select a Podcast --</option>'
      podcasts.forEach(podcast => {
        if (podcast && podcast._id && podcast.podName) {
          const option = document.createElement("option")
          option.value = podcast._id
          option.textContent = podcast.podName
          podcastSelect.appendChild(option)
        }
      })
      podcastSelect.disabled = podcasts.length === 0
    } catch (error) {
      console.error("Error loading podcasts:", error)
      podcastSelect.innerHTML = '<option value="">Error loading podcasts</option>'
      podcastSelect.disabled = true
      episodeSelect.disabled = true
    }
  }

  // Load episodes for the selected podcast using /episodes/by_podcast/<podcast_id>
  async function loadEpisodesForPodcast(podcastId) {
    episodeSelect.innerHTML = '<option value="">Loading episodes...</option>'
    episodeSelect.disabled = true
    episodeDetailsPreview.classList.add("hidden")
    if (!podcastId) {
      episodeSelect.innerHTML = '<option value="">Select a podcast first...</option>'
      return
    }
    try {
      const episodes = await fetchEpisodesByPodcast(podcastId)
      episodeSelect.innerHTML = '<option value="">-- Select an Episode --</option>'
      if (episodes && episodes.length > 0) {
        episodes.forEach(episode => {
          if (episode && episode._id && episode.title) {
            const option = document.createElement("option")
            option.value = episode._id
            option.textContent = `${episode.title} (${episode.status || ""})`
            episodeSelect.appendChild(option)
          }
        })
        episodeSelect.disabled = false
      } else {
        episodeSelect.innerHTML = '<option value="">No episodes found for this podcast</option>'
        episodeSelect.disabled = true
      }
    } catch (error) {
      console.error("Error loading episodes:", error)
      episodeSelect.innerHTML = '<option value="">Error loading episodes</option>'
      episodeSelect.disabled = true
    }
  }

  async function loadEpisodes() {
    try {
      const episodes = await fetchAllEpisodes()
      episodeSelect.innerHTML = '<option value="">-- Select an Episode --</option>'
      episodes.forEach((episode) => {
        // Filter for episodes that are ready to be published
        if (episode.status === "Edited" || episode.status === "Ready to Publish" || episode.status === "Scheduled") {
          const option = document.createElement("option")
          option.value = episode._id
          option.textContent = `${episode.title} (${episode.status})`
          episodeSelect.appendChild(option)
        }
      })
    } catch (error) {
      console.error("Error loading episodes:", error)
      episodeSelect.innerHTML = '<option value="">Error loading episodes</option>'
      addToLog("Error loading episodes. Please try again.")
    }
  }

  async function loadEpisodePreview(episodeId) {
    if (!episodeId) {
      episodeDetailsPreview.classList.add("hidden")
      return
    }
    try {
      const episode = await fetchEpisode(episodeId)
      if (episode) {
        previewTitle.textContent = episode.title || "No title"
        previewDescription.textContent = episode.description || "No description available."

        if (episode.image_url) {
          previewImage.src = episode.image_url
          previewImage.classList.remove("hidden")
        } else {
          previewImage.classList.add("hidden")
        }

        if (episode.audio_url) {
          previewAudio.src = episode.audio_url
          previewAudio.classList.remove("hidden")
        } else {
          previewAudio.classList.add("hidden")
        }
        episodeDetailsPreview.classList.remove("hidden")
      } else {
        episodeDetailsPreview.classList.add("hidden")
        addToLog(`Could not load preview for episode ID: ${episodeId}`)
      }
    } catch (error) {
      console.error("Error loading episode preview:", error)
      episodeDetailsPreview.classList.add("hidden")
      addToLog(`Error loading preview for episode ID: ${episodeId}.`)
    }
  }

  function addToLog(message) {
    publishStatusDiv.classList.remove("hidden")
    const timestamp = new Date().toLocaleTimeString()
    publishLogPre.textContent += `[${timestamp}] ${message}\n`
    publishLogPre.scrollTop = publishLogPre.scrollHeight // Auto-scroll
  }

  podcastSelect.addEventListener("change", (event) => {
    const podcastId = event.target.value
    loadEpisodesForPodcast(podcastId)
    episodeSelect.value = ""
    episodeDetailsPreview.classList.add("hidden")
  })

  episodeSelect.addEventListener("change", (event) => {
    loadEpisodePreview(event.target.value)
  })

  publishNowBtn.addEventListener("click", async () => {
    const episodeId = episodeSelect.value
    const notes = publishNotes.value
    const selectedPlatforms = []
    platformToggles.forEach((toggle) => {
      if (toggle.checked) {
        selectedPlatforms.push(toggle.dataset.platform)
      }
    })

    if (!episodeId) {
      showNotification("Error", "Please select an episode to publish.", "error")
      addToLog("Publishing failed: No episode selected.")
      return
    }
    if (selectedPlatforms.length === 0) {
      showNotification("Error", "Please select at least one platform to publish to.", "error")
      addToLog("Publishing failed: No platforms selected.")
      return
    }

    publishNowBtn.disabled = true
    publishNowBtn.textContent = "Publishing..."
    addToLog(`Starting publishing process for episode ID: ${episodeId}`)
    addToLog(`Selected platforms: ${selectedPlatforms.join(", ")}`)
    if (notes) {
      addToLog(`Publish notes: ${notes}`)
    }

    try {
      const result = await publishEpisode(episodeId, selectedPlatforms, notes)
      if (result.success) {
        addToLog(`Successfully published episode: ${result.message}`)
        showNotification("Success", `Episode published successfully! ${result.message}`, "success")
        // Optionally, update episode status in the dropdown or reload episodes
        loadEpisodes()
        episodeDetailsPreview.classList.add("hidden")
        episodeSelect.value = ""
        publishNotes.value = ""
      } else {
        addToLog(`Publishing failed: ${result.error || "Unknown error"}`)
        showNotification("Error", `Failed to publish episode. ${result.error || "Unknown error"}`, "error")
      }
    } catch (error) {
      console.error("Error publishing episode:", error)
      addToLog(`Critical error during publishing: ${error.message}`)
      showNotification("Error", `An error occurred during publishing: ${error.message}`, "error")
    } finally {
      publishNowBtn.disabled = false
      publishNowBtn.textContent = "Publish Now"
    }
  })

  function initializeSvgIcons() {
    // Sidebar menu icons
    document.getElementById("back-to-dashboard-icon").innerHTML = svgIcons.backToDashboard
    document.getElementById("podcasts-icon").innerHTML = svgIcons.podcasts
    document.getElementById("episodes-icon").innerHTML = svgIcons.episodes
    document.getElementById("publish-icon").innerHTML = svgIcons.publish
    document.getElementById("guests-icon").innerHTML = svgIcons.guests

    // Action button icons
    document.getElementById("add-icon-podcast").innerHTML = svgIcons.add
    document.getElementById("add-icon-episode").innerHTML = svgIcons.add
    document.getElementById("add-icon-guest").innerHTML = svgIcons.add

    // Toggle sidebar icon
    document.getElementById("toggle-sidebar-icon").innerHTML = svgIcons.toggleSidebar
  }

  // Setup mobile sidebar
  function setupMobileSidebar() {
    const sidebarContainer = document.getElementById("sidebar-container")
    const openSidebarArrowBtn = document.getElementById("openSidebarArrowBtn")
    const pmSidebarOverlay = document.getElementById("pmSidebarOverlay")
    const pmSidebarCloseBtn = document.getElementById("pmSidebarCloseBtn")

    if (!sidebarContainer || !openSidebarArrowBtn || !pmSidebarOverlay || !pmSidebarCloseBtn) {
      console.warn("Mobile sidebar toggle elements not all found. Skipping mobile sidebar setup.")
      return
    }

    const openSidebar = () => {
      sidebarContainer.classList.add("is-open")
      pmSidebarOverlay.classList.add("is-visible")
      sidebarContainer.classList.add("sidebar-animate-in")
      if (window.innerWidth <= 992) {
        document.body.style.overflow = "hidden"
      }
      openSidebarArrowBtn.style.display = "none"
      pmSidebarCloseBtn.style.display = "flex"
    }

    const closeSidebar = () => {
      sidebarContainer.classList.add("sidebar-animate-out")

      setTimeout(() => {
        sidebarContainer.classList.remove("is-open")
        sidebarContainer.classList.remove("sidebar-animate-in")
        sidebarContainer.classList.remove("sidebar-animate-out")
        pmSidebarOverlay.classList.remove("is-visible")
        document.body.style.overflow = ""
        if (window.innerWidth <= 992) {
          openSidebarArrowBtn.style.display = "flex"
        }
        pmSidebarCloseBtn.style.display = "none"
      }, 300)
    }

    pmSidebarCloseBtn.style.display = "none"

    if (window.innerWidth <= 992) {
      openSidebarArrowBtn.style.display = "flex"
    }

    openSidebarArrowBtn.addEventListener("click", openSidebar)
    pmSidebarOverlay.addEventListener("click", closeSidebar)
    pmSidebarCloseBtn.addEventListener("click", closeSidebar)

    window.addEventListener("resize", () => {
      if (window.innerWidth > 992) {
        document.body.style.overflow = ""
        openSidebarArrowBtn.style.display = "none"
      } else {
        if (!sidebarContainer.classList.contains("is-open")) {
          openSidebarArrowBtn.style.display = "flex"
        } else {
          openSidebarArrowBtn.style.display = "none"
        }
      }
    })

    if (window.innerWidth <= 992) {
      openSidebarArrowBtn.style.display = "flex"
    } else {
      openSidebarArrowBtn.style.display = "none"
    }
  }

  // Initial load
  loadPodcasts()
  initializePublishPageSVGs() // Initialize SVGs for the publish page
  setupMobileSidebar()
})
