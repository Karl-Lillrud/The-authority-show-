import { publishEpisode } from "/static/js/publish/publishRequests.js"
import { fetchAllEpisodes, fetchEpisode } from "/static/js/publish/episodeRequests.js"
import { svgIcons } from "/static/js/components/svgIcons.js"
import { showNotification } from "/static/js/components/notifications.js"

document.addEventListener("DOMContentLoaded", () => {
  // Initialize SVG icons
  initializeSvgIcons()

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
  loadEpisodes()
  setupMobileSidebar()
})
