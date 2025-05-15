"use client"
import { fetchEpisodesByPodcast } from "/static/requests/episodeRequest.js"
import { fetchTasks } from "/static/requests/podtaskRequest.js"
import { formatDueDate } from "/static/js/episode-to-do/utils.js"

// Timeline functionality
export function renderTimeline(state) {
  const timeline = document.getElementById("timeline")
  if (!timeline) return

  timeline.innerHTML = ""

  if (!state.selectedEpisode) {
    timeline.innerHTML = "<p>No episode selected</p>"
    return
  }

  // Update timeline header dates
  const timelineRecordingDate = document.getElementById("timelineRecordingDate")
  const timelineReleaseDate = document.getElementById("timelineReleaseDate")

  if (timelineRecordingDate) {
    timelineRecordingDate.textContent =
      state.selectedEpisode.recordingDate || state.selectedEpisode.recordingAt || "Not scheduled"
  }

  if (timelineReleaseDate) {
    timelineReleaseDate.textContent =
      state.selectedEpisode.releaseDate || state.selectedEpisode.publishDate || "Not scheduled"
  }

  // Check if we have tasks for the selected episode
  const episodeTasks = state.tasks.filter(
    (task) => task.episodeId === state.selectedEpisode._id || task.episodeId === state.selectedEpisode?.id,
  )

  // Only use tasks that belong to the current episode
  const tasksToRender = episodeTasks

  // Group tasks by due date
  const tasksByDueDate = {}
  tasksToRender.forEach((task) => {
    if (!task.dueDate) return

    if (!tasksByDueDate[task.dueDate]) {
      tasksByDueDate[task.dueDate] = []
    }
    tasksByDueDate[task.dueDate].push(task)
  })

  // Sort dates for timeline
  const sortedDates = Object.keys(tasksByDueDate).sort((a, b) => {
    // Sort "before" dates first
    if (a.includes("before") && b.includes("after")) return -1
    if (a.includes("after") && b.includes("before")) return 1

    // Extract number of days
    const daysA = Number.parseInt(a.match(/\d+/)?.[0] || "0")
    const daysB = Number.parseInt(b.match(/\d+/)?.[0] || "0")

    // For "before" dates, higher number comes first
    if (a.includes("before") && b.includes("before")) return daysB - daysA

    // For "after" dates, lower number comes first
    if (a.includes("after") && b.includes("after")) return daysA - daysB

    // Recording day is in the middle
    if (a === "Recording day") return b.includes("before") ? 1 : -1
    if (b === "Recording day") return a.includes("before") ? -1 : 1

    // If both are actual dates, sort chronologically
    try {
      const dateA = new Date(a)
      const dateB = new Date(b)
      if (!isNaN(dateA) && !isNaN(dateB)) {
        return dateA - dateB
      }
    } catch (e) {
      // If date parsing fails, fall back to string comparison
    }

    return 0
  })

  if (sortedDates.length === 0) {
    timeline.innerHTML = "<p>No tasks with due dates available</p>"
    return
  }

  sortedDates.forEach((date) => {
    const timelineItem = document.createElement("div")
    timelineItem.className = "timeline-item"

    const isRecordingDay = date === "Recording day"
    const formattedDate = formatDueDate(date)

    timelineItem.innerHTML = `
      <div class="timeline-node ${isRecordingDay ? "recording-day" : ""}">
        ${isRecordingDay ? '<i class="fas fa-circle"></i>' : ""}
      </div>
      <div class="timeline-date">${formattedDate}</div>
      <div class="timeline-tasks">
        ${tasksByDueDate[date]
          .map(
            (task) => `
          <div class="timeline-task ${task.status === "completed" ? "completed" : ""}">
            ${
              task.status === "completed"
                ? '<i class="fas fa-check-circle text-success"></i>'
                : '<i class="far fa-circle text-muted"></i>'
            }
            <span>${task.name}</span>
          </div>
        `,
          )
          .join("")}
      </div>
    `

    timeline.appendChild(timelineItem)
  })
}

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
    progressBar.style.width = `${percentage}%`
  }
}

export function setupTimelineToggle(state) {
  const toggleBtn = document.getElementById("toggleTimelineBtn")
  const sidebar = document.getElementById("timelineSidebar")

  if (!toggleBtn || !sidebar) return

  toggleBtn.addEventListener("click", () => {
    state.showTimeline = !state.showTimeline

    if (state.showTimeline) {
      sidebar.classList.remove("collapsed")
      toggleBtn.innerHTML = '<i class="fas fa-chevron-right"></i>'
    } else {
      sidebar.classList.add("collapsed")
      toggleBtn.innerHTML = '<i class="fas fa-chevron-left"></i>'
    }
  })
}

export function updateEpisodeDisplay(state) {
  if (!state.selectedEpisode) return

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

  // Update timeline
  renderTimeline(state)
}

export async function selectEpisode(episode, state, updateUI) {
  state.selectedEpisode = episode;

  // Store the selected episode ID in local storage
  if (episode._id || episode.id) {
    const episodeId = episode._id || episode.id;
    localStorage.setItem("selected_episode_id", episodeId);
    console.log("✅ Selected episode ID stored in local storage:", episodeId);
  }

  try {
    // Fetch tasks for the selected episode
    const tasksData = await fetchTasks();
    console.log("Tasks data for selected episode:", tasksData);

    // Filter tasks for the selected episode
    state.tasks = tasksData
      ? tasksData.filter((task) => task.episodeId === episode._id || task.episodeId === episode.id)
      : [];

    console.log(
      "Tasks with assignment data:",
      state.tasks.map((task) => ({
        name: task.name,
        assignee: task.assignee,
        assigneeName: task.assigneeName,
        assignedAt: task.assignedAt,
      }))
    );

    // Update UI
    updateUI();
  } catch (error) {
    console.error("Error fetching tasks for episode:", error);
  }
}

export async function selectPodcast(podcast, state, updateUI) {
  state.activePodcast = podcast

  try {
    // Fetch episodes for the selected podcast
    let episodesData = await fetchEpisodesByPodcast(podcast._id)
    console.log("Episodes for selected podcast:", episodesData)
    // Sort episodes by publishDate or recordingDate descending (newest first)
    episodesData = (episodesData || []).sort((a, b) => {
      const dateA = new Date(a.publishDate || a.recordingDate || a.recordingAt || 0)
      const dateB = new Date(b.publishDate || b.recordingDate || b.recordingAt || 0)
      return dateB - dateA
    })
    state.episodes = episodesData

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
  let podcastEpisodes = state.episodes.filter(
    (ep) => ep.podcastId === state.activePodcast._id || ep.podcast_id === state.activePodcast._id,
  )

  // Sort episodes by publishDate or recordingDate descending (newest first)
  podcastEpisodes = podcastEpisodes.sort((a, b) => {
    const dateA = new Date(a.publishDate || a.recordingDate || a.recordingAt || 0)
    const dateB = new Date(b.publishDate || b.recordingDate || b.recordingAt || 0)
    return dateB - dateA
  })

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
  let podcastEpisodes = state.episodes.filter(
    (ep) => ep.podcastId === state.activePodcast._id || ep.podcast_id === state.activePodcast._id,
  )

  // Sort episodes by publishDate or recordingDate descending (newest first)
  podcastEpisodes = podcastEpisodes.sort((a, b) => {
    const dateA = new Date(a.publishDate || a.recordingDate || a.recordingAt || 0)
    const dateB = new Date(b.publishDate || b.recordingDate || b.recordingAt || 0)
    return dateB - dateA
  })

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
