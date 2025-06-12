"use client"
import { fetchEpisodesByPodcast } from "/static/requests/episodeRequest.js"
import { fetchTasks } from "/static/requests/podtaskRequest.js"

export function updateProgressBar(state) {
  if (!state.selectedEpisode) return

  // Check if we have tasks for the selected episode
  const episodeTasks = state.tasks.filter(
    (task) => task.episodeId === state.selectedEpisode._id || task.episodeId === state.selectedEpisode.id,
  )

  // Only use tasks that belong to the current episode
  const tasksToRender = episodeTasks

  // Calculate completed tasks
  const completedTasks =
    tasksToRender.filter((task) => task.status === "completed" || state.completedTasks[task.id || task._id]).length || 0

  const totalTasks = tasksToRender.length || 0
  const percentage = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0

  const progressText = document.getElementById("progressText")
  const progressBar = document.getElementById("progressBar")

  if (progressText) {
    progressText.textContent = `${completedTasks} of ${totalTasks} tasks completed (${percentage}%)`
  }

  if (progressBar) {
    // Ensure the progress bar is orange by setting the background color directly
    progressBar.style.backgroundColor = percentage === 100 ? "#ff6b1a" : "#ff7f3f"
    progressBar.style.width = `${percentage}%`
    progressBar.style.height = "100%"

    // Add special styling for completed progress bar
    if (percentage === 100) {
      progressBar.classList.add("completed")
    } else {
      progressBar.classList.remove("completed")
    }
  }
}

export function updateEpisodeDisplay(state) {
  if (!state.selectedEpisode) return

  // Store the selected episode ID in localStorage
  if (state.selectedEpisode._id || state.selectedEpisode.id) {
    const episodeId = state.selectedEpisode._id || state.selectedEpisode.id
    localStorage.setItem("selected_episode_id", episodeId)
    console.log("✅ Selected episode ID stored in localStorage from updateEpisodeDisplay:", episodeId)
  }

  // Update header
  const currentEpisodeNumber = document.getElementById("currentEpisodeNumber")
  const episodeTitle = document.getElementById("episodeTitle")
  const recordingDate = document.getElementById("recordingDate")

  if (episodeTitle) {
    episodeTitle.textContent = state.selectedEpisode.title || "Untitled Episode"
  }

  if (recordingDate) {
    recordingDate.textContent = `Recording Date: ${state.selectedEpisode.recordingDate || state.selectedEpisode.recordingAt || "Not scheduled"}`
  }

  // Update progress bar
  updateProgressBar(state)
}

export async function selectEpisode(episode, state, updateUI) {
  state.selectedEpisode = episode

  // Store the selected episode ID in local storage
  if (episode._id || episode.id) {
    const episodeId = episode._id || episode.id
    localStorage.setItem("selected_episode_id", episodeId)
    console.log("✅ Selected episode ID stored in local storage:", episodeId)
  }

  try {
    // Fetch tasks for the selected episode
    const tasksData = await fetchTasks()
    console.log("Tasks data for selected episode:", tasksData)

    // Filter tasks for the selected episode
    state.tasks = tasksData
      ? tasksData.filter((task) => task.episodeId === episode._id || task.episodeId === episode.id)
      : []

    console.log(
      "Tasks with assignment data:",
      state.tasks.map((task) => ({
        name: task.name,
        assignee: task.assignee,
        assigneeName: task.assigneeName,
        assignedAt: task.assignedAt,
      })),
    )

    // Update UI
    updateUI()
  } catch (error) {
    console.error("Error fetching tasks for episode:", error)
  }
}

export async function selectPodcast(podcast, state, updateUI) {
  state.activePodcast = podcast

  try {
    // Fetch episodes for the selected podcast
    const episodesData = await fetchEpisodesByPodcast(podcast._id)
    console.log("Episodes for selected podcast:", episodesData)
    state.episodes = episodesData || []

    // Find the first episode of this podcast
    if (state.episodes.length > 0) {
      state.selectedEpisode = state.episodes[0]

      // Fetch tasks for the selected episode
      const tasksData = await fetchTasks()
      console.log("Tasks data for selected episode:", tasksData)

      // Filter tasks for the selected episode
      state.tasks = tasksData
        ? tasksData.filter(
            (task) => task.episodeId === state.selectedEpisode._id || task.episodeId === state.selectedEpisode.id,
          )
        : []
    } else {
      state.selectedEpisode = null
      state.tasks = []
    }

    // Update UI
    updateUI()
  } catch (error) {
    console.error("Error fetching episodes for podcast:", error)
    alert("Failed to load episodes for the selected podcast.")
  }
}

export function populateEpisodesList(state, updateUI) {
  const episodesList = document.getElementById("episodesList")
  if (!episodesList) return

  episodesList.innerHTML = ""

  if (!state.activePodcast || state.episodes.length === 0) {
    episodesList.innerHTML = `<div class="empty-state">No episodes available</div>`
    return
  }

  // Filter episodes for the active podcast
  const podcastEpisodes = state.episodes.filter(
    (ep) => ep.podcastId === state.activePodcast._id || ep.podcast_id === state.activePodcast._id,
  )

  if (podcastEpisodes.length === 0) {
    episodesList.innerHTML = `<div class="empty-state">No episodes for this podcast</div>`
    return
  }

  podcastEpisodes.forEach((episode) => {
    const item = document.createElement("div")
    item.className = `episode-item ${episode._id === state.selectedEpisode?._id ? "active" : ""}`
    item.innerHTML = `
      <div class="episode-info">
        <div class="episode-name">${episode.title || "Untitled Episode"}</div>
        <div class="episode-date">${episode.recordingDate || episode.recordingAt || episode.publishDate || "Not scheduled"}</div>
      </div>
      <span class="episode-status ${episode.status?.toLowerCase() || "planning"}">${episode.status || "Planning"}</span>
    `
    item.addEventListener("click", () => selectEpisode(episode, state, updateUI))
    episodesList.appendChild(item)
  })
}

export function populateEpisodeDropdown(state, updateUI) {
  const dropdown = document.getElementById("episodeDropdown")
  if (!dropdown) return

  dropdown.innerHTML = ""

  if (!state.activePodcast || state.episodes.length === 0) {
    dropdown.innerHTML = `<div class="dropdown-item">No episodes available</div>`
    return
  }

  // Filter episodes for the active podcast
  const podcastEpisodes = state.episodes.filter(
    (ep) => ep.podcastId === state.activePodcast._id || ep.podcast_id === state.activePodcast._id,
  )

  if (podcastEpisodes.length === 0) {
    dropdown.innerHTML = `<div class="dropdown-item">No episodes for this podcast</div>`
    return
  }

  podcastEpisodes.forEach((episode) => {
    const item = document.createElement("div")
    item.className = "dropdown-item"
    item.innerHTML = `<span class="font-medium">${episode.title || "Untitled Episode"}</span>`
    item.addEventListener("click", () => {
      selectEpisode(episode, state, updateUI)
      toggleEpisodeDropdown()
    })
    dropdown.appendChild(item)
  })
}

export function toggleEpisodeDropdown() {
  const dropdown = document.getElementById("episodeDropdown")
  if (dropdown) {
    dropdown.classList.toggle("show")
  }
}

export function setupEpisodeDropdown(state) {
  const dropdownBtn = document.getElementById("episodeDropdownBtn")
  const dropdown = document.getElementById("episodeDropdown")

  if (!dropdownBtn || !dropdown) return

  dropdownBtn.addEventListener("click", toggleEpisodeDropdown)

  // Close dropdown when clicking outside
  document.addEventListener("click", (event) => {
    if (!event.target.closest("#episodeDropdownBtn") && !event.target.closest("#episodeDropdown")) {
      dropdown.classList.remove("show")
    }
  })
}

export function populatePodcastSelector(state, updateUI) {
  const podcastSelector = document.getElementById("podcastSelector")
  if (!podcastSelector) return

  podcastSelector.innerHTML = ""

  if (state.podcasts.length === 0) {
    podcastSelector.innerHTML = `<div class="empty-state">No podcasts available</div>`
    return
  }

  state.podcasts.forEach((podcast) => {
    const item = document.createElement("div")
    item.className = `podcast-item ${podcast._id === state.activePodcast?._id ? "active" : ""}`
    item.innerHTML = `
      <div class="podcast-header">
        ${podcast.imageUrl ? `<img src="${podcast.imageUrl}" alt="${podcast.podName || podcast.name || "Podcast"}" class="podcast-image" style="width: 40px; height: 40px; border-radius: 8px; margin-right: 10px;">` : '<i class="fas fa-podcast"></i>'}
        <span class="podcast-name">${podcast.podName || podcast.name || "Unnamed Podcast"}</span>
      </div>
    `
    item.addEventListener("click", () => selectPodcast(podcast, state, updateUI))
    podcastSelector.appendChild(item)
  })
}
