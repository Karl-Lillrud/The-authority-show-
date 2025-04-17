"use client"

import { fetchPodcasts } from "/static/requests/podcastRequests.js"
import { fetchAllEpisodes, fetchEpisodesByPodcast } from "/static/requests/episodeRequest.js"
import {
  fetchTasks,
  fetchTask,
  saveTask,
  updateTask,
  deleteTask,
  fetchLocalDefaultTasks,
  addDefaultTasksToEpisode,
} from "/static/requests/podtaskRequest.js"

document.addEventListener("DOMContentLoaded", async () => {
  // State management
  const state = {
    podcasts: [],
    episodes: [],
    tasks: [],
    templates: [],
    activePodcast: null,
    activeTemplate: null,
    activeTab: "tasks",
    selectedEpisode: null,
    selectedTask: null,
    showTimeline: true,
    expandedTasks: {},
    completedTasks: {},
  }

  // Initialize the UI
  await initData()
  initUI()

  async function initData() {
    try {
      console.log("Fetching data from database...")

      // Fetch podcasts
      const podcastsData = await fetchPodcasts()
      console.log("Podcasts data:", podcastsData)
      state.podcasts = podcastsData.podcast || [] // Note: using podcast instead of podcasts based on your other files

      if (state.podcasts.length > 0) {
        state.activePodcast = state.podcasts[0]

        // Fetch episodes for the active podcast
        const episodesData = await fetchEpisodesByPodcast(state.activePodcast._id) // Note: using _id instead of id based on your other files
        console.log("Episodes data:", episodesData)
        state.episodes = episodesData || []

        if (state.episodes.length > 0) {
          state.selectedEpisode = state.episodes[0]

          // Fetch tasks for the selected episode
          const tasksData = await fetchTasks()
          console.log("Tasks data:", tasksData)

          // Filter tasks for the selected episode
          state.tasks = tasksData
            ? tasksData.filter(
                (task) => task.episodeId === state.selectedEpisode._id || task.episodeId === state.selectedEpisode.id,
              )
            : []
        }
      } else {
        // If no podcasts, try to fetch all episodes
        const allEpisodes = await fetchAllEpisodes()
        console.log("All episodes data:", allEpisodes)
        state.episodes = allEpisodes || []

        if (state.episodes.length > 0) {
          state.selectedEpisode = state.episodes[0]

          // Fetch tasks for the selected episode
          const tasksData = await fetchTasks()
          console.log("Tasks data:", tasksData)

          // Filter tasks for the selected episode
          state.tasks = tasksData
            ? tasksData.filter(
                (task) => task.episodeId === state.selectedEpisode._id || task.episodeId === state.selectedEpisode.id,
              )
            : []
        }
      }

      // Fetch default tasks for templates
      const defaultTasksData = await fetchLocalDefaultTasks()
      console.log("Default tasks data:", defaultTasksData)

      // Create template from default tasks
      state.templates = [
        {
          id: "default-template",
          name: "Default Podcast Template",
          description: "Standard workflow for podcast episodes",
          tasks: Array.isArray(defaultTasksData)
            ? defaultTasksData.map((taskName, index) => ({
                id: `default-${index}`,
                name: taskName,
                description: `Default task: ${taskName}`,
                status: "not-started",
                dueDate: "Before recording",
                assignee: "Unassigned",
              }))
            : [],
        },
      ]

      state.activeTemplate = state.templates[0]

      console.log("Initialized data:", {
        podcasts: state.podcasts,
        episodes: state.episodes,
        tasks: state.tasks,
        templates: state.templates,
      })
    } catch (error) {
      console.error("Error initializing data:", error)
      alert("Failed to load data. Please refresh the page.")
    }
  }

  function initUI() {
    // Check if we have the necessary data to initialize the UI
    if (!state.activeTemplate) {
      console.warn("Cannot initialize UI: Missing template data")
      return
    }

    // Even if we don't have podcasts or episodes, we can still show the UI with empty states
    console.log("Initializing UI with available data")

    // Populate podcast selector
    populatePodcastSelector()

    // Populate episodes list for the active podcast
    populateEpisodesList()

    // Populate episode dropdown
    populateEpisodeDropdown()

    // Populate task list
    renderTaskList()

    // Populate kanban board
    renderKanbanBoard()

    // Populate timeline
    renderTimeline()

    // Set up tab switching
    setupTabs()

    // Set up timeline toggle
    setupTimelineToggle()

    // Set up episode dropdown
    setupEpisodeDropdown()

    // Update progress bar
    updateProgressBar()
  }

  function populatePodcastSelector() {
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
          <i class="fas fa-podcast"></i>
          <span class="podcast-name">${podcast.podName || podcast.name || "Unnamed Podcast"}</span>
        </div>
        <div class="podcast-meta">${podcast.episodeCount || 0} episodes • ${podcast.description || ""}</div>
      `
      item.addEventListener("click", () => selectPodcast(podcast))
      podcastSelector.appendChild(item)
    })
  }

  function populateEpisodesList() {
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
        <span class="episode-number">#${episode.number || 1}</span>
        <div class="episode-info">
          <div class="episode-name">${episode.title || "Untitled Episode"}</div>
          <div class="episode-date">${episode.recordingDate || episode.recordingAt || episode.publishDate || "Not scheduled"}</div>
        </div>
        <span class="episode-status ${episode.status?.toLowerCase() || "planning"}">${episode.status || "Planning"}</span>
      `
      item.addEventListener("click", () => selectEpisode(episode))
      episodesList.appendChild(item)
    })
  }

  function populateEpisodeDropdown() {
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
      item.innerHTML = `<span class="font-medium">Episode ${episode.number || 1}:</span> ${episode.title || "Untitled Episode"}`
      item.addEventListener("click", () => {
        selectEpisode(episode)
        toggleEpisodeDropdown()
      })
      dropdown.appendChild(item)
    })
  }

  function renderTaskList() {
    const taskList = document.getElementById("taskList")
    if (!taskList) return

    taskList.innerHTML = ""

    // Check if we have tasks for the selected episode
    const episodeTasks = state.tasks.filter(
      (task) => task.episodeId === state.selectedEpisode?._id || task.episodeId === state.selectedEpisode?.id,
    )

    // If we have episode-specific tasks, use those; otherwise, use template tasks
    const tasksToRender = episodeTasks.length > 0 ? episodeTasks : state.activeTemplate?.tasks || []

    if (tasksToRender.length === 0) {
      taskList.innerHTML = `
        <div class="empty-task-list">
          <p>No tasks available</p>
          <div class="task-actions">
            <button class="btn add-task-btn" id="add-new-task">
              <i class="fas fa-plus"></i> Add Task
            </button>
            <button class="btn import-tasks-btn" id="import-default-tasks">
              <i class="fas fa-download"></i> Import Default Tasks
            </button>
          </div>
        </div>
      `

      // Add event listeners for the buttons
      const addTaskBtn = document.getElementById("add-new-task")
      if (addTaskBtn) {
        addTaskBtn.addEventListener("click", () =>
          showAddTaskPopup(state.selectedEpisode?._id || state.selectedEpisode?.id),
        )
      }

      const importTasksBtn = document.getElementById("import-default-tasks")
      if (importTasksBtn) {
        importTasksBtn.addEventListener("click", () =>
          showImportTasksPopup(state.selectedEpisode?._id || state.selectedEpisode?.id),
        )
      }

      return
    }

    // Add task management actions at the top
    const taskActions = document.createElement("div")
    taskActions.className = "task-management-actions"
    taskActions.innerHTML = `
      <div class="task-header">
        <h3>Tasks</h3>
        <div class="task-header-actions">
          <button class="btn import-tasks-btn" id="import-default-tasks">
            <i class="fas fa-download"></i> Import
          </button>
          <button class="btn add-task-btn" id="add-new-task">
            <i class="fas fa-plus"></i> Add Task
          </button>
        </div>
      </div>
    `
    taskList.appendChild(taskActions)

    // Add event listeners for the buttons
    const addTaskBtn = document.getElementById("add-new-task")
    if (addTaskBtn) {
      addTaskBtn.addEventListener("click", () =>
        showAddTaskPopup(state.selectedEpisode?._id || state.selectedEpisode?.id),
      )
    }

    const importTasksBtn = document.getElementById("import-default-tasks")
    if (importTasksBtn) {
      importTasksBtn.addEventListener("click", () =>
        showImportTasksPopup(state.selectedEpisode?._id || state.selectedEpisode?.id),
      )
    }

    // Render each task
    tasksToRender.forEach((task) => {
      const isCompleted = state.completedTasks[task.id || task._id] || task.status === "completed"
      const isExpanded = state.expandedTasks[task.id || task._id] || false

      const taskItem = document.createElement("div")
      taskItem.className = "task-item"
      taskItem.dataset.taskId = task.id || task._id
      taskItem.innerHTML = `
        <div class="task-header ${isCompleted ? "completed" : ""}">
          <div class="task-checkbox ${isCompleted ? "checked" : ""}" data-task-id="${task.id || task._id}">
            ${isCompleted ? '<i class="fas fa-check"></i>' : ""}
          </div>
          <button class="task-expand" data-task-id="${task.id || task._id}">
            <i class="fas fa-chevron-${isExpanded ? "down" : "right"}"></i>
          </button>
          <div class="task-content">
            <div class="task-name ${isCompleted ? "completed" : ""}">${task.name}</div>
            ${
              !isExpanded
                ? `
              <div class="task-meta">
                <div class="task-meta-item">
                  <i class="fas fa-clock"></i>
                  <span>${task.dueDate || "No due date"}</span>
                </div>
                <div class="task-meta-item">
                  <i class="fas fa-user"></i>
                  <span>${task.assignee || "Unassigned"}</span>
                </div>
                ${
                  task.dependencies && task.dependencies.length > 0
                    ? `
                  <span class="task-badge">${task.dependencies.length} ${task.dependencies.length === 1 ? "dependency" : "dependencies"}</span>
                `
                    : ""
                }
              </div>
            `
                : ""
            }
          </div>
          <div class="task-actions">
            ${task.hasDependencyWarning ? '<i class="fas fa-exclamation-circle text-warning"></i>' : ""}
            <button class="task-action-btn edit-task-btn" title="Edit Task" data-task-id="${task.id || task._id}">
              <i class="fas fa-edit"></i>
            </button>
            <button class="task-action-btn delete-task-btn" title="Delete Task" data-task-id="${task.id || task._id}">
              <i class="fas fa-trash"></i>
            </button>
            ${
              task.workspaceEnabled
                ? `
              <button class="btn-icon text-primary workspace-btn" data-workspace-task-id="${task.id || task._id}">
                <i class="fas fa-laptop"></i>
              </button>
            `
                : ""
            }
          </div>
        </div>
        
        <div class="task-details ${isExpanded ? "expanded" : ""}">
          <p class="task-description">${task.description || "No description available"}</p>
          
          ${
            task.dependencies && task.dependencies.length > 0
              ? `
            <div class="task-dependencies">
              <h4 class="task-dependencies-title">Dependencies:</h4>
              <ul class="task-dependencies-list">
                ${task.dependencies
                  .map(
                    (dep) => `
                  <li class="task-dependencies-item"><span>•</span> ${dep}</li>
                `,
                  )
                  .join("")}
              </ul>
            </div>
          `
              : ""
          }
          
          <div class="task-footer">
            <div class="task-footer-meta">
              <div class="task-meta-item">
                <i class="fas fa-clock"></i>
                <span>Due: ${task.dueDate || "No due date"}</span>
              </div>
              <div class="task-meta-item">
                <i class="fas fa-user"></i>
                <span>Assigned to: ${task.assignee || "Unassigned"}</span>
              </div>
            </div>
            
            <div class="task-footer-actions">
              <button class="btn btn-outline btn-sm">
                <i class="fas fa-comment"></i>
                <span>Comments (${task.comments?.length || 0})</span>
              </button>
              
              ${
                task.workspaceEnabled
                  ? `
                <button class="btn btn-outline btn-sm workspace-btn" data-workspace-task-id="${task.id || task._id}">
                  <i class="fas fa-laptop"></i>
                  <span>Open in Workspace</span>
                </button>
              `
                  : ""
              }
            </div>
          </div>
        </div>
      `

      taskList.appendChild(taskItem)
    })

    // Add workflow actions at the bottom
    const workflowActions = document.createElement("div")
    workflowActions.className = "workflow-actions"
    workflowActions.innerHTML = `
      <button class="btn save-workflow-btn" id="save-workflow">
        <i class="fas fa-save"></i> Save Workflow
      </button>
      <button class="btn import-workflow-btn" id="import-workflow">
        <i class="fas fa-download"></i> Import Workflow
      </button>
    `
    taskList.appendChild(workflowActions)

    // Add event listeners for workflow buttons
    const saveWorkflowBtn = document.getElementById("save-workflow")
    if (saveWorkflowBtn) {
      saveWorkflowBtn.addEventListener("click", () =>
        saveWorkflow(state.selectedEpisode?._id || state.selectedEpisode?.id),
      )
    }

    const importWorkflowBtn = document.getElementById("import-workflow")
    if (importWorkflowBtn) {
      importWorkflowBtn.addEventListener("click", () =>
        importWorkflow(state.selectedEpisode?._id || state.selectedEpisode?.id),
      )
    }

    // Add event listeners for task interactions
    setupTaskInteractions()
  }

  function renderKanbanBoard() {
    const kanbanBoard = document.getElementById("kanbanBoard")
    if (!kanbanBoard) return

    kanbanBoard.innerHTML = ""

    const columns = [
      { id: "todo", title: "To Do", color: "kanban-column-todo" },
      { id: "in-progress", title: "In Progress", color: "kanban-column-progress" },
      { id: "ready", title: "Ready for Publishing", color: "kanban-column-ready" },
      { id: "published", title: "Published", color: "kanban-column-published" },
    ]

    // Check if we have tasks for the selected episode
    const episodeTasks = state.tasks.filter(
      (task) => task.episodeId === state.selectedEpisode?._id || task.episodeId === state.selectedEpisode?.id,
    )

    // If we have episode-specific tasks, use those; otherwise, use template tasks
    const tasksToRender = episodeTasks.length > 0 ? episodeTasks : state.activeTemplate?.tasks || []

    // Group tasks by status
    const tasksByStatus = {
      todo:
        tasksToRender.filter((task) => task.status === "not-started" || task.status === "incomplete" || !task.status) ||
        [],
      "in-progress": tasksToRender.filter((task) => task.status === "in-progress") || [],
      ready: tasksToRender.filter((task) => task.status === "ready") || [],
      published: tasksToRender.filter((task) => task.status === "completed") || [],
    }

    columns.forEach((column) => {
      const columnDiv = document.createElement("div")
      columnDiv.className = `kanban-column ${column.color}`
      columnDiv.innerHTML = `
        <div class="kanban-column-header">
          <span>${column.title}</span>
          <span class="badge">${tasksByStatus[column.id].length}</span>
        </div>
        <div class="kanban-column-content" data-column-id="${column.id}">
          ${
            tasksByStatus[column.id].length === 0
              ? `<div class="kanban-empty">No tasks</div>`
              : tasksByStatus[column.id]
                  .map(
                    (task) => `
              <div class="kanban-task" draggable="true" data-task-id="${task.id || task._id}">
                <div class="kanban-task-header">
                  <h3 class="kanban-task-title">${task.name}</h3>
                  <div class="dropdown">
                    <button class="btn-icon dropdown-toggle">
                      <i class="fas fa-ellipsis-h"></i>
                    </button>
                  </div>
                </div>
                <div class="kanban-task-meta">
                  <div class="task-meta-item">
                    <i class="fas fa-clock"></i>
                    <span>${task.dueDate || "No due date"}</span>
                  </div>
                </div>
                <div class="kanban-task-footer">
                  <div class="kanban-task-assignee ${
                    task.assignee === "John Doe"
                      ? "bg-blue"
                      : task.assignee === "Alice Smith"
                        ? "bg-green"
                        : task.assignee === "Bob Johnson"
                          ? "bg-purple"
                          : ""
                  }">
                    ${task.assignee ? task.assignee.split(" ").map((name) => name[0]) : "UN"}
                  </div>
                  ${
                    task.workspaceEnabled
                      ? `
                    <button class="btn-icon text-primary workspace-btn" data-workspace-task-id="${task.id || task._id}">
                      <i class="fas fa-laptop"></i>
                    </button>
                  `
                      : ""
                  }
                </div>
              </div>
            `,
                  )
                  .join("")
          }
        </div>
      `

      kanbanBoard.appendChild(columnDiv)
    })

    // Set up drag and drop for kanban tasks
    setupKanbanDragDrop()
  }

  function renderTimeline() {
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
      (task) => task.episodeId === state.selectedEpisode?._id || task.episodeId === state.selectedEpisode?.id,
    )

    // If we have episode-specific tasks, use those; otherwise, use template tasks
    const tasksToRender = episodeTasks.length > 0 ? episodeTasks : state.activeTemplate?.tasks || []

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
      // Sort "before recording" dates first
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

      timelineItem.innerHTML = `
        <div class="timeline-node ${isRecordingDay ? "recording-day" : ""}">
          ${isRecordingDay ? '<i class="fas fa-circle"></i>' : ""}
        </div>
        <div class="timeline-date">${date}</div>
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

  function setupTabs() {
    const tabButtons = document.querySelectorAll(".tab-btn")
    const tabPanes = document.querySelectorAll(".tab-pane")

    tabButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const tabId = button.getAttribute("data-tab")

        // Update active state
        tabButtons.forEach((btn) => btn.classList.remove("active"))
        tabPanes.forEach((pane) => pane.classList.remove("active"))

        button.classList.add("active")
        document.getElementById(`${tabId}-tab`)?.classList.add("active")

        state.activeTab = tabId
      })
    })
  }

  function setupTimelineToggle() {
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

  function setupEpisodeDropdown() {
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

  function toggleEpisodeDropdown() {
    const dropdown = document.getElementById("episodeDropdown")
    if (dropdown) {
      dropdown.classList.toggle("show")
    }
  }

  async function selectPodcast(podcast) {
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
      populatePodcastSelector()
      populateEpisodesList()
      populateEpisodeDropdown()

      // Update episode display
      updateEpisodeDisplay()
    } catch (error) {
      console.error("Error fetching episodes for podcast:", error)
      alert("Failed to load episodes for the selected podcast.")
    }
  }

  async function selectEpisode(episode) {
    state.selectedEpisode = episode

    try {
      // Fetch tasks for the selected episode
      const tasksData = await fetchTasks()
      console.log("Tasks data for selected episode:", tasksData)

      // Filter tasks for the selected episode
      state.tasks = tasksData
        ? tasksData.filter((task) => task.episodeId === episode._id || task.episodeId === episode.id)
        : []

      // Update UI
      populateEpisodesList()
      updateEpisodeDisplay()
      renderTaskList()
      renderKanbanBoard()
      renderTimeline()
    } catch (error) {
      console.error("Error fetching tasks for episode:", error)
    }
  }

  function updateEpisodeDisplay() {
    if (!state.selectedEpisode) return

    // Update header
    const currentEpisodeNumber = document.getElementById("currentEpisodeNumber")
    const episodeTitle = document.getElementById("episodeTitle")
    const recordingDate = document.getElementById("recordingDate")

    if (currentEpisodeNumber) {
      currentEpisodeNumber.textContent = `Episode ${state.selectedEpisode.number || 1}`
    }

    if (episodeTitle) {
      episodeTitle.textContent = state.selectedEpisode.title || "Untitled Episode"
    }

    if (recordingDate) {
      recordingDate.textContent = `Recording Date: ${state.selectedEpisode.recordingDate || state.selectedEpisode.recordingAt || "Not scheduled"}`
    }

    // Update progress bar
    updateProgressBar()

    // Update timeline
    renderTimeline()
  }

  function updateProgressBar() {
    if (!state.selectedEpisode) return

    // Check if we have tasks for the selected episode
    const episodeTasks = state.tasks.filter(
      (task) => task.episodeId === state.selectedEpisode._id || task.episodeId === state.selectedEpisode.id,
    )

    // If we have episode-specific tasks, use those; otherwise, use template tasks
    const tasksToRender = episodeTasks.length > 0 ? episodeTasks : state.activeTemplate?.tasks || []

    // Calculate completed tasks
    const completedTasks =
      tasksToRender.filter((task) => task.status === "completed" || state.completedTasks[task.id || task._id]).length ||
      0

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

  function setupTaskInteractions() {
    // Task checkbox toggle
    document.querySelectorAll(".task-checkbox").forEach((checkbox) => {
      checkbox.addEventListener("click", () => {
        const taskId = checkbox.getAttribute("data-task-id")
        toggleTaskCompletion(taskId)
      })
    })

    // Task expand/collapse
    document.querySelectorAll(".task-expand").forEach((button) => {
      button.addEventListener("click", () => {
        const taskId = button.getAttribute("data-task-id")
        toggleTaskExpansion(taskId)
      })
    })

    // Edit task buttons
    document.querySelectorAll(".edit-task-btn").forEach((button) => {
      button.addEventListener("click", () => {
        const taskId = button.getAttribute("data-task-id")
        showEditTaskPopup(taskId)
      })
    })

    // Delete task buttons
    document.querySelectorAll(".delete-task-btn").forEach((button) => {
      button.addEventListener("click", () => {
        const taskId = button.getAttribute("data-task-id")
        confirmDeleteTask(taskId)
      })
    })

    // Workspace buttons
    document.querySelectorAll(".workspace-btn, [data-workspace-task-id]").forEach((button) => {
      button.addEventListener("click", () => {
        const taskId = button.getAttribute("data-workspace-task-id")
        openTaskInWorkspace(taskId)
      })
    })
  }

  async function toggleTaskCompletion(taskId) {
    // Find the task in either state.tasks or template tasks
    let task = state.tasks.find((t) => t.id === taskId || t._id === taskId)

    // If not found in state.tasks, check template tasks
    if (!task && state.activeTemplate) {
      task = state.activeTemplate.tasks.find((t) => t.id === taskId || t._id === taskId)
    }

    if (!task) return

    // Toggle completion state
    const newStatus = task.status === "completed" ? "incomplete" : "completed"
    state.completedTasks[taskId] = newStatus === "completed"

    // If this is a real task (not a template task), update it in the database
    if (task.episodeId) {
      try {
        await updateTask(taskId, { status: newStatus })
        console.log(`Task ${taskId} status updated to ${newStatus}`)
      } catch (error) {
        console.error("Error updating task status:", error)
        // Revert the state change if the API call fails
        state.completedTasks[taskId] = !state.completedTasks[taskId]
      }
    }

    // Update UI
    renderTaskList()
    renderKanbanBoard()
    renderTimeline()
    updateProgressBar()
  }

  function toggleTaskExpansion(taskId) {
    state.expandedTasks[taskId] = !state.expandedTasks[taskId]
    renderTaskList()
  }

  function openTaskInWorkspace(taskId) {
    // Find the task in either state.tasks or template tasks
    let task = state.tasks.find((t) => t.id === taskId || t._id === taskId)

    // If not found in state.tasks, check template tasks
    if (!task && state.activeTemplate) {
      task = state.activeTemplate.tasks.find((t) => t.id === taskId || t._id === taskId)
    }

    if (task) {
      state.selectedTask = task

      // Switch to workspace tab
      document.querySelector('.tab-btn[data-tab="workspace"]')?.click()

      // Render workspace with selected task
      renderWorkspace()
    }
  }

  function setupKanbanDragDrop() {
    const draggables = document.querySelectorAll(".kanban-task")
    const dropZones = document.querySelectorAll(".kanban-column-content")

    draggables.forEach((draggable) => {
      draggable.addEventListener("dragstart", () => {
        draggable.classList.add("dragging")
      })

      draggable.addEventListener("dragend", () => {
        draggable.classList.remove("dragging")
      })
    })

    dropZones.forEach((zone) => {
      zone.addEventListener("dragover", (e) => {
        e.preventDefault()
        zone.classList.add("drag-over")
      })

      zone.addEventListener("dragleave", () => {
        zone.classList.remove("drag-over")
      })

      zone.addEventListener("drop", (e) => {
        e.preventDefault()
        zone.classList.remove("drag-over")

        const dragging = document.querySelector(".dragging")
        if (dragging) {
          const taskId = dragging.getAttribute("data-task-id")
          const columnId = zone.getAttribute("data-column-id")

          // Update task status based on column
          updateTaskStatus(taskId, columnId)

          // Re-render kanban board
          renderKanbanBoard()

          // Update task list and timeline to reflect status changes
          renderTaskList()
          renderTimeline()
          updateProgressBar()
        }
      })
    })
  }

  async function updateTaskStatus(taskId, columnId) {
    // Find the task in either state.tasks or template tasks
    let task = state.tasks.find((t) => t.id === taskId || t._id === taskId)

    // If not found in state.tasks, check template tasks
    if (!task && state.activeTemplate) {
      task = state.activeTemplate.tasks.find((t) => t.id === taskId || t._id === taskId)
    }

    if (!task) return

    let newStatus
    switch (columnId) {
      case "todo":
        newStatus = "not-started"
        break
      case "in-progress":
        newStatus = "in-progress"
        break
      case "ready":
        newStatus = "ready"
        break
      case "published":
        newStatus = "completed"
        break
      default:
        newStatus = "not-started"
    }

    // Update task status
    task.status = newStatus

    // If this is a real task (not a template task), update it in the database
    if (task.episodeId) {
      try {
        await updateTask(taskId, { status: newStatus })
        console.log(`Task ${taskId} status updated to ${newStatus}`)
      } catch (error) {
        console.error("Error updating task status:", error)
      }
    }
  }

  function renderWorkspace() {
    const workspaceArea = document.getElementById("workspaceArea")
    if (!workspaceArea) return

    if (!state.selectedTask) {
      workspaceArea.innerHTML = `
        <div class="workspace-placeholder">
          <i class="fas fa-laptop"></i>
          <h3>No task selected</h3>
          <p>Select a task from the task list to open it in the workspace. Tasks with the <i class="fas fa-laptop"></i> icon can be worked on directly in this workspace.</p>
        </div>
      `
      return
    }

    const task = state.selectedTask

    // Determine which workspace to show based on task type
    let workspaceContent = ""

    if (task.type === "audio-editing") {
      workspaceContent = renderAudioEditingWorkspace(task)
    } else if (task.type === "transcription") {
      workspaceContent = renderTranscriptionWorkspace(task)
    } else {
      workspaceContent = renderGenericWorkspace(task)
    }

    workspaceArea.innerHTML = workspaceContent

    // Set up workspace interactions
    setupWorkspaceInteractions()
  }

  function renderAudioEditingWorkspace(task) {
    return `
      <div class="workspace-content">
        <div class="workspace-header">
          <div>
            <h3 class="workspace-title">${task.name}</h3>
            <p class="workspace-subtitle">Audio editing workspace</p>
          </div>
          <button class="btn btn-primary">
            <i class="fas fa-save"></i>
            <span>Save Changes</span>
          </button>
        </div>
        
        <div class="card mb-4">
          <div class="card-content">
            <div class="audio-file">
              <i class="fas fa-file-audio text-primary audio-icon"></i>
              <div>
                <h4 class="audio-title">Episode${state.selectedEpisode?.number || 1}_raw.mp3</h4>
                <p class="audio-meta">48:32 • 44.1kHz • Stereo</p>
              </div>
            </div>
            
            <div class="audio-waveform">
              <div class="waveform-placeholder">Audio waveform visualization</div>
            </div>
            
            <div class="audio-controls">
              <div class="playback-controls">
                <button class="btn btn-outline btn-icon"><i class="fas fa-backward"></i></button>
                <button id="playButton" class="btn btn-primary btn-icon play-btn"><i class="fas fa-play"></i></button>
                <button class="btn btn-outline btn-icon"><i class="fas fa-forward"></i></button>
              </div>
              
              <div class="volume-control">
                <i class="fas fa-volume-up"></i>
                <input type="range" min="0" max="100" value="80" class="volume-slider">
              </div>
              
              <div class="time-display">12:34 / 48:32</div>
            </div>
          </div>
        </div>
        
        <div class="workspace-tabs">
          <div class="workspace-tab-list">
            <button class="workspace-tab active" data-workspace-tab="tools">AI Tools</button>
            <button class="workspace-tab" data-workspace-tab="effects">Effects</button>
            <button class="workspace-tab" data-workspace-tab="markers">Markers</button>
          </div>
          
          <div class="workspace-tab-content active" id="tools-tab">
            <div class="card">
              <div class="card-content">
                <h4 class="workspace-section-title">
                  <i class="fas fa-magic text-primary"></i>
                  <span>AI Audio Enhancement</span>
                </h4>
                
                <div class="enhancement-controls">
                  <div class="enhancement-slider">
                    <div class="enhancement-slider-header">
                      <label for="enhancement-level" class="enhancement-label">
                        <i class="fas fa-sparkles text-warning"></i>
                        <span>Enhancement Level</span>
                      </label>
                      <span class="enhancement-value">50%</span>
                    </div>
                    <input type="range" id="enhancement-level" min="0" max="100" value="50" class="enhancement-range">
                  </div>
                  
                  <div class="enhancement-options">
                    <div class="enhancement-option">
                      <input type="checkbox" id="noise-reduction" checked>
                      <label for="noise-reduction">Noise Reduction</label>
                    </div>
                    <div class="enhancement-option">
                      <input type="checkbox" id="echo-reduction">
                      <label for="echo-reduction">Echo Reduction</label>
                    </div>
                    <div class="enhancement-option">
                      <input type="checkbox" id="voice-enhancement" checked>
                      <label for="voice-enhancement">Voice Enhancement</label>
                    </div>
                  </div>
                  
                  <button id="applyAiBtn" class="btn btn-primary btn-full">
                    <i class="fas fa-magic"></i>
                    <span>Apply AI Enhancement</span>
                  </button>
                  
                  <div class="enhancement-note">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>AI enhancement uses machine learning to improve audio quality. Results may vary based on the original recording quality.</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="workspace-actions">
              <button class="btn btn-outline">
                <i class="fas fa-headphones"></i>
                <span>Preview Changes</span>
              </button>
              
              <div class="workspace-action-group">
                <button class="btn btn-outline">
                  <i class="fas fa-check-circle"></i>
                  <span>Mark as Complete</span>
                </button>
                <button class="btn btn-primary">
                  <i class="fas fa-save"></i>
                  <span>Save & Export</span>
                </button>
              </div>
            </div>
          </div>
          
          <div class="workspace-tab-content" id="effects-tab">
            <div class="card">
              <div class="card-content">
                <h4 class="workspace-section-title">Audio Effects</h4>
                <p class="workspace-description">Standard audio effects like EQ, compression, and normalization would be available here.</p>
              </div>
            </div>
          </div>
          
          <div class="workspace-tab-content" id="markers-tab">
            <div class="card">
              <div class="card-content">
                <h4 class="workspace-section-title">Audio Markers</h4>
                <p class="workspace-description">Add markers to important points in your audio for easier navigation and editing.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    `
  }

  function renderTranscriptionWorkspace(task) {
    return `
      <div class="workspace-content">
        <div class="workspace-header">
          <div>
            <h3 class="workspace-title">${task.name}</h3>
            <p class="workspace-subtitle">Transcription workspace</p>
          </div>
          <button class="btn btn-primary">
            <i class="fas fa-save"></i>
            <span>Save Transcript</span>
          </button>
        </div>
        
        <div class="transcription-grid">
          <div class="card">
            <div class="card-content">
              <div class="audio-file">
                <i class="fas fa-file-audio text-primary audio-icon"></i>
                <div>
                  <h4 class="audio-title">Episode${state.selectedEpisode?.number || 1}_final.mp3</h4>
                  <p class="audio-meta">48:32 • 44.1kHz • Stereo</p>
                </div>
              </div>
              
              <div class="mini-player">
                <button id="playButton" class="btn btn-outline btn-icon play-btn">
                  <i class="fas fa-play"></i>
                </button>
                <div class="mini-player-progress">
                  <div class="mini-player-bar" style="width: 25%"></div>
                </div>
                <span class="mini-player-time">12:34</span>
              </div>
              
              <div class="transcription-options">
                <h4 class="workspace-section-title">
                  <i class="fas fa-magic text-primary"></i>
                  <span>AI Transcription</span>
                </h4>
                <button id="generateTranscriptBtn" class="btn btn-outline btn-sm">
                  <span>Generate Transcript</span>
                </button>
                
                <div class="transcription-option">
                  <input type="checkbox" id="speaker-detection" checked>
                  <label for="speaker-detection">Speaker Detection</label>
                </div>
                
                <div class="transcription-option">
                  <input type="checkbox" id="punctuation" checked>
                  <label for="punctuation">Auto Punctuation</label>
                </div>
              </div>
            </div>
          </div>
          
          <div class="card">
            <div class="card-content">
              <div class="transcript-header">
                <i class="fas fa-file-alt text-primary transcript-icon"></i>
                <div>
                  <h4 class="transcript-title">Transcript</h4>
                  <p class="transcript-meta">Edit and review the generated transcript</p>
                </div>
              </div>
              
              <textarea class="transcript-editor" placeholder="Transcript will appear here after generation..."></textarea>
              
              <div class="transcript-actions">
                <button class="btn btn-outline btn-sm">
                  <i class="fas fa-file-export"></i>
                  <span>Export as Text</span>
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <div class="workspace-actions">
          <button class="btn btn-outline">
            <i class="fas fa-microphone"></i>
            <span>Record Additional Notes</span>
          </button>
          
          <button class="btn btn-primary">
            <i class="fas fa-check-circle"></i>
            <span>Mark Task as Complete</span>
          </button>
        </div>
      </div>
    `
  }

  function renderGenericWorkspace(task) {
    return `
      <div class="workspace-generic">
        <div class="workspace-generic-icon">
          <i class="fas fa-laptop"></i>
        </div>
        <h3 class="workspace-generic-title">${task.name}</h3>
        <p class="workspace-generic-description">
          This task doesn't have a specialized workspace yet. You can still track its progress and mark it as complete.
        </p>
        <button class="btn btn-primary">
          <i class="fas fa-check-circle"></i>
          <span>Mark Task as Complete</span>
        </button>
      </div>
    `
  }

  function setupWorkspaceInteractions() {
    // Play/pause button
    const playButton = document.getElementById("playButton")
    if (playButton) {
      playButton.addEventListener("click", togglePlayback)
    }

    // Apply AI button
    const applyAiBtn = document.getElementById("applyAiBtn")
    if (applyAiBtn) {
      applyAiBtn.addEventListener("click", applyAiEnhancement)
    }

    // Generate transcript button
    const generateTranscriptBtn = document.getElementById("generateTranscriptBtn")
    if (generateTranscriptBtn) {
      generateTranscriptBtn.addEventListener("click", generateTranscript)
    }

    // Workspace tabs
    const workspaceTabs = document.querySelectorAll(".workspace-tab")
    if (workspaceTabs.length > 0) {
      workspaceTabs.forEach((tab) => {
        tab.addEventListener("click", () => {
          const tabId = tab.getAttribute("data-workspace-tab")

          // Update active state
          workspaceTabs.forEach((t) => t.classList.remove("active"))
          document.querySelectorAll(".workspace-tab-content").forEach((c) => c.classList.remove("active"))

          tab.classList.add("active")
          document.getElementById(`${tabId}-tab`)?.classList.add("active")
        })
      })
    }
  }

  function togglePlayback() {
    const playButton = document.getElementById("playButton")
    if (!playButton) return

    const isPlaying = playButton.classList.contains("playing")

    if (isPlaying) {
      playButton.classList.remove("playing")
      playButton.innerHTML = '<i class="fas fa-play"></i>'
    } else {
      playButton.classList.add("playing")
      playButton.innerHTML = '<i class="fas fa-pause"></i>'
    }
  }

  function applyAiEnhancement() {
    const button = document.getElementById("applyAiBtn")
    if (!button) return

    button.disabled = true
    button.innerHTML = '<span class="spinner">⟳</span> Processing...'

    // Simulate AI processing
    setTimeout(() => {
      button.disabled = false
      button.innerHTML = '<i class="fas fa-magic"></i> Apply AI Enhancement'
      alert("AI enhancement applied successfully!")
    }, 2000)
  }

  function generateTranscript() {
    const button = document.getElementById("generateTranscriptBtn")
    if (!button) return

    button.disabled = true
    button.textContent = "Processing..."

    // Simulate transcript generation
    setTimeout(() => {
      button.disabled = false
      button.textContent = "Generate Transcript"

      const textarea = document.querySelector(".transcript-editor")
      if (textarea) {
        textarea.value = `Host: Welcome to Episode ${state.selectedEpisode?.number || 1} of our podcast, where we discuss ${state.selectedEpisode?.title || "our topic"}.\n\nGuest: Thanks for having me! I'm excited to share my thoughts on this topic.\n\nHost: Let's start by talking about the key points we outlined in our prep session...`
      }
    }, 2000)
  }

  // Task Management Functions
  async function showAddTaskPopup(episodeId) {
    if (!episodeId) {
      console.error("No episode ID provided for adding task")
      return
    }

    const popupHTML = `
      <div id="task-popup" class="popup">
        <div class="popup-content">
          <div class="modal-header">
            <h2>Add New Task</h2>
            <button class="close-btn">&times;</button>
          </div>
          <div class="popup-body">
            <form id="task-form">
              <input type="hidden" id="task-episode-id" value="${episodeId}">
              <div class="form-group">
                <label for="task-title">Task Title</label>
                <input type="text" id="task-title" class="form-control" placeholder="What needs to be done?" required>
              </div>
              <div class="form-group">
                <label for="task-description">Description</label>
                <textarea id="task-description" class="form-control" placeholder="Add more details about this task..."></textarea>
              </div>
              <div class="form-group">
                <label for="task-due-date">Due Date</label>
                <select id="task-due-date" class="form-control">
                  <option value="Before recording">Before Recording</option>
                  <option value="Recording day">Recording Day</option>
                  <option value="After recording">After Recording</option>
                </select>
              </div>
              <div class="modal-footer">
                <button type="button" id="cancel-add-btn" class="btn cancel-btn">Cancel</button>
                <button type="submit" class="btn save-btn">
                  <i class="fas fa-check"></i> Create Task
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    `

    document.body.insertAdjacentHTML("beforeend", popupHTML)
    const popup = document.getElementById("task-popup")

    // Show the popup
    popup.style.display = "flex"

    // Add class to animate in
    setTimeout(() => {
      popup.querySelector(".popup-content").classList.add("show")
    }, 10)

    // Close button event
    const closeBtn = popup.querySelector(".close-btn")
    closeBtn.addEventListener("click", () => {
      closePopup(popup)
    })

    // Cancel button event
    const cancelBtn = document.getElementById("cancel-add-btn")
    cancelBtn.addEventListener("click", () => {
      closePopup(popup)
    })

    // Close when clicking outside
    popup.addEventListener("click", (e) => {
      if (e.target === popup) {
        closePopup(popup)
      }
    })

    // Form submission
    const form = document.getElementById("task-form")
    form.addEventListener("submit", async (e) => {
      e.preventDefault()
      const title = document.getElementById("task-title").value
      const description = document.getElementById("task-description").value
      const dueDate = document.getElementById("task-due-date").value

      const taskData = {
        name: title,
        description,
        episodeId: episodeId,
        dueDate: dueDate,
        status: "not-started",
      }

      try {
        // Show loading state
        const saveBtn = form.querySelector(".save-btn")
        const originalText = saveBtn.innerHTML
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...'
        saveBtn.disabled = true

        const result = await saveTask(taskData)
        console.log("Task saved:", result)

        // Refresh tasks
        const tasksData = await fetchTasks()
        state.tasks = tasksData ? tasksData.filter((task) => task.episodeId === episodeId) : []

        closePopup(popup)
        renderTaskList()
        renderKanbanBoard()
        renderTimeline()
        updateProgressBar()
      } catch (error) {
        console.error("Error saving task:", error)
        // Reset button state
        const saveBtn = form.querySelector(".save-btn")
        saveBtn.innerHTML = originalText
        saveBtn.disabled = false
        alert("Failed to save task. Please try again.")
      }
    })
  }

  async function showEditTaskPopup(taskId) {
    try {
      const response = await fetchTask(taskId)

      if (!response || !response[0] || !response[0].podtask) {
        console.error("Task not found:", taskId)
        return
      }

      const task = response[0].podtask
      console.log("Fetched task data:", task)

      const { name, description, status, dueDate } = task

      const modalHTML = `
        <div id="edit-task-modal" class="popup">
          <div class="popup-content">
            <div class="modal-header">
              <h2>Edit Task</h2>
              <button class="close-btn">&times;</button>
            </div>
            <div class="popup-body">
              <form id="edit-task-form">
                <input type="hidden" id="edit-task-id" value="${taskId}">
                <div class="form-group">
                  <label for="edit-task-title">Task Title</label>
                  <input type="text" id="edit-task-title" class="form-control" value="${name || ""}" required>
                </div>
                <div class="form-group">
                  <label for="edit-task-description">Description</label>
                  <textarea id="edit-task-description" class="form-control">${description || ""}</textarea>
                </div>
                <div class="form-group">
                  <label for="edit-task-due-date">Due Date</label>
                  <select id="edit-task-due-date" class="form-control">
                    <option value="Before recording" ${dueDate === "Before recording" ? "selected" : ""}>Before Recording</option>
                    <option value="Recording day" ${dueDate === "Recording day" ? "selected" : ""}>Recording Day</option>
                    <option value="After recording" ${dueDate === "After recording" ? "selected" : ""}>After Recording</option>
                  </select>
                </div>
                <div class="form-group">
                  <label for="edit-task-status">Status</label>
                  <select id="edit-task-status" class="form-control">
                    <option value="not-started" ${status === "not-started" || status === "incomplete" ? "selected" : ""}>Not Started</option>
                    <option value="in-progress" ${status === "in-progress" ? "selected" : ""}>In Progress</option>
                    <option value="ready" ${status === "ready" ? "selected" : ""}>Ready</option>
                    <option value="completed" ${status === "completed" ? "selected" : ""}>Completed</option>
                  </select>
                </div>
                <div class="modal-footer">
                  <button type="button" id="cancel-edit-btn" class="btn cancel-btn">Cancel</button>
                  <button type="submit" class="btn save-btn">
                    <i class="fas fa-save"></i> Save Changes
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      `

      document.body.insertAdjacentHTML("beforeend", modalHTML)

      const modal = document.getElementById("edit-task-modal")
      modal.style.display = "flex"

      setTimeout(() => {
        modal.querySelector(".popup-content").classList.add("show")
      }, 10)

      const closeBtn = modal.querySelector(".close-btn")
      closeBtn.addEventListener("click", () => closeEditModal(modal))

      const cancelBtn = document.getElementById("cancel-edit-btn")
      cancelBtn.addEventListener("click", () => closeEditModal(modal))

      modal.addEventListener("click", (e) => {
        if (e.target === modal) {
          closeEditModal(modal)
        }
      })

      const form = document.getElementById("edit-task-form")
      form.addEventListener("submit", async (e) => {
        e.preventDefault()

        const title = document.getElementById("edit-task-title").value
        const description = document.getElementById("edit-task-description").value
        const dueDate = document.getElementById("edit-task-due-date").value
        const status = document.getElementById("edit-task-status").value

        const taskData = {
          name: title,
          description,
          dueDate,
          status,
        }

        try {
          // Show loading state
          const saveBtn = form.querySelector(".save-btn")
          const originalText = saveBtn.innerHTML
          saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...'
          saveBtn.disabled = true

          await updateTask(taskId, taskData)
          console.log("Task updated:", taskData)

          // Refresh tasks
          const tasksData = await fetchTasks()
          state.tasks = tasksData
            ? tasksData.filter(
                (task) => task.episodeId === state.selectedEpisode._id || task.episodeId === state.selectedEpisode.id,
              )
            : []

          closeEditModal(modal)
          renderTaskList()
          renderKanbanBoard()
          renderTimeline()
          updateProgressBar()
        } catch (error) {
          console.error("Error updating task:", error)
          // Reset button state
          const saveBtn = form.querySelector(".save-btn")
          saveBtn.innerHTML = originalText
          saveBtn.disabled = false
          alert("Failed to update task. Please try again.")
        }
      })
    } catch (error) {
      console.error("Error fetching task for editing:", error)
      alert("Failed to load task for editing. Please try again.")
    }
  }

  function closeEditModal(modal) {
    modal.querySelector(".popup-content").classList.remove("show")
    setTimeout(() => {
      modal.style.display = "none"
      modal.remove()
    }, 200)
  }

  async function confirmDeleteTask(taskId) {
    const confirmDelete = confirm("Are you sure you want to delete this task?")
    if (confirmDelete) {
      try {
        await deleteTask(taskId)
        console.log("Task deleted:", taskId)

        // Refresh tasks
        const tasksData = await fetchTasks()
        state.tasks = tasksData
          ? tasksData.filter(
              (task) => task.episodeId === state.selectedEpisode._id || task.episodeId === state.selectedEpisode.id,
            )
          : []

        renderTaskList()
        renderKanbanBoard()
        renderTimeline()
        updateProgressBar()
      } catch (error) {
        console.error("Error deleting task:", error)
        alert("Failed to delete task. Please try again.")
      }
    }
  }

  async function showImportTasksPopup(episodeId) {
    if (!episodeId) {
      console.error("No episode ID provided for importing tasks")
      return
    }

    const popupHTML = `
      <div id="import-tasks-popup" class="popup">
        <div class="popup-content">
          <div class="modal-header">
            <h2>Import Default Tasks</h2>
            <button class="close-btn">&times;</button>
          </div>
          <div class="popup-body">
            <p>Importing default tasks will add a set of predefined tasks to this episode.</p>
            <p>Are you sure you want to continue?</p>
          </div>
          <div class="modal-footer">
            <button type="button" id="cancel-import-btn" class="btn cancel-btn">Cancel</button>
            <button type="button" id="confirm-import-btn" class="btn save-btn">
              <i class="fas fa-download"></i> Import Tasks
            </button>
          </div>
        </div>
      </div>
    `

    document.body.insertAdjacentHTML("beforeend", popupHTML)
    const popup = document.getElementById("import-tasks-popup")

    // Show the popup
    popup.style.display = "flex"

    // Add class to animate in
    setTimeout(() => {
      popup.querySelector(".popup-content").classList.add("show")
    }, 10)

    // Close button event
    const closeBtn = popup.querySelector(".close-btn")
    closeBtn.addEventListener("click", () => {
      closePopup(popup)
    })

    // Cancel button event
    const cancelBtn = document.getElementById("cancel-import-btn")
    cancelBtn.addEventListener("click", () => {
      closePopup(popup)
    })

    // Close when clicking outside
    popup.addEventListener("click", (e) => {
      if (e.target === popup) {
        closePopup(popup)
      }
    })

    // Confirm import button event
    const confirmImportBtn = document.getElementById("confirm-import-btn")
    confirmImportBtn.addEventListener("click", async () => {
      try {
        // Show loading state
        const originalText = confirmImportBtn.innerHTML
        confirmImportBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Importing...'
        confirmImportBtn.disabled = true

        await addDefaultTasksToEpisode(episodeId)
        console.log("Default tasks added to episode:", episodeId)

        // Refresh tasks
        const tasksData = await fetchTasks()
        state.tasks = tasksData ? tasksData.filter((task) => task.episodeId === episodeId) : []

        closePopup(popup)
        renderTaskList()
        renderKanbanBoard()
        renderTimeline()
        updateProgressBar()
      } catch (error) {
        console.error("Error importing default tasks:", error)
        // Reset button state
        confirmImportBtn.innerHTML = originalText
        confirmImportBtn.disabled = false
        alert("Failed to import default tasks. Please try again.")
      }
    })
  }

  function closePopup(popup) {
    popup.querySelector(".popup-content").classList.remove("show")
    setTimeout(() => {
      popup.style.display = "none"
      popup.remove()
    }, 200)
  }

  async function saveWorkflow(episodeId) {
    console.log("Saving workflow for episode:", episodeId)
    alert("Workflow saved successfully!")
  }

  async function importWorkflow(episodeId) {
    console.log("Importing workflow for episode:", episodeId)
    alert("Workflow imported successfully!")
  }
})
