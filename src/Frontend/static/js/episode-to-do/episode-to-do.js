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
  deleteWorkflow,
} from "/static/requests/podtaskRequest.js"
import { fetchProfile } from "/static/requests/accountRequests.js"

document.addEventListener("DOMContentLoaded", async () => {
  // State management
  const state = {
    podcasts: [],
    episodes: [],
    tasks: [],
    templates: [],
    workflows: [], // Added to store workflows
    activePodcast: null,
    activeTemplate: null,
    activeTab: "tasks",
    selectedEpisode: null,
    selectedTask: null,
    showTimeline: true,
    expandedTasks: {},
    completedTasks: {},
    currentUser: {
      id: "current-user", // In a real app, get this from your auth system
      name: "Current User", // In a real app, get this from your auth system
    },
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
                assignee: null,
                assigneeName: null,
                comments: [],
                dependencies: [], // Added dependencies array
              }))
            : [],
        },
      ]

      state.activeTemplate = state.templates[0]

      // Fetch workflows from the database
      try {
        const workflowsResponse = await fetch("/get_workflows", {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        })

        if (workflowsResponse.ok) {
          const workflowsData = await workflowsResponse.json()
          state.workflows = workflowsData.workflows || []
          console.log("Workflows data:", state.workflows)
        }
      } catch (error) {
        console.error("Error fetching workflows:", error)
        state.workflows = []
      }

      console.log("Initialized data:", {
        podcasts: state.podcasts,
        episodes: state.episodes,
        tasks: state.tasks,
        templates: state.templates,
        workflows: state.workflows,
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

    // Set up modal buttons
    setupModalButtons()

    // Add global CSS for modals
    addModalStyles()

    // Add flatpickr CSS and JS
    addFlatpickrStyles()
  }

  // Add global CSS for modals
  function addModalStyles() {
    const style = document.createElement("style")
    style.textContent = `
      .popup {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
      }
      
      .popup-content {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        width: 90%;
        max-width: 500px;
        max-height: 90vh;
        overflow: auto;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        position: relative;
        transform: scale(0.9);
        opacity: 0;
        transition: transform 0.3s, opacity 0.3s;
      }
      
      .popup-content.show {
        transform: scale(1);
        opacity: 1;
      }
      
      .popup-content.hide {
        transform: scale(0.9);
        opacity: 0;
      }
      
      .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 1px solid #eee;
      }
      
      .modal-header h2 {
        margin: 0;
        font-size: 1.5rem;
      }
      
      .close-btn {
        background: none;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        color: #666;
      }
      
      .close-btn:hover {
        color: #333;
      }
      
      .popup-body {
        margin-bottom: 20px;
      }
      
      .modal-footer {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        padding-top: 15px;
        border-top: 1px solid #eee;
      }
      
      .form-group {
        margin-bottom: 15px;
      }
      
      .form-group label {
        display: block;
        margin-bottom: 5px;
        font-weight: 500;
      }
      
      .form-control {
        width: 100%;
        padding: 8px 12px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 1rem;
      }
      
      textarea.form-control {
        min-height: 100px;
        resize: vertical;
      }
      
      .btn {
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        font-weight: 500;
        transition: background-color 0.2s;
      }
      
      .save-btn {
        background-color: #4CAF50;
        color: white;
        border: none;
      }
      
      .save-btn:hover {
        background-color: #45a049;
      }
      
      .cancel-btn {
        background-color: #f1f1f1;
        color: #333;
        border: 1px solid #ddd;
      }
      
      .cancel-btn:hover {
        background-color: #e7e7e7;
      }
      
      .help-text {
        font-size: 0.8rem;
        color: #666;
        margin-top: 5px;
      }
      
      /* Dependency visualization styles */
      .task-dependency-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 4px;
        padding: 8px 12px;
        margin-top: 8px;
        color: #856404;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      
      .task-dependency-list {
        margin: 5px 0;
        padding-left: 20px;
      }
      
      .task-dependency-item {
        display: flex;
        align-items: center;
        gap: 5px;
        margin-bottom: 3px;
      }
      
      .dependency-status {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
      }
      
      .dependency-status.completed {
        background-color: #4CAF50;
      }
      
      .dependency-status.pending {
        background-color: #f0ad4e;
      }
      
      .task-checkbox.disabled {
        opacity: 0.5;
        cursor: not-allowed;
        background-color: #f8f9fa;
      }
    `
    document.head.appendChild(style)
  }

  // Add flatpickr for date/time picker
  function addFlatpickrStyles() {
    // Add flatpickr CSS
    const flatpickrCSS = document.createElement("link")
    flatpickrCSS.rel = "stylesheet"
    flatpickrCSS.href = "https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css"
    document.head.appendChild(flatpickrCSS)

    // Add flatpickr theme (optional)
    const flatpickrTheme = document.createElement("link")
    flatpickrTheme.rel = "stylesheet"
    flatpickrTheme.href = "https://cdn.jsdelivr.net/npm/flatpickr/dist/themes/material_blue.css"
    document.head.appendChild(flatpickrTheme)

    // Add flatpickr JS
    const flatpickrScript = document.createElement("script")
    flatpickrScript.src = "https://cdn.jsdelivr.net/npm/flatpickr"
    document.head.appendChild(flatpickrScript)
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
          ${podcast.imageUrl ? `<img src="${podcast.imageUrl}" alt="${podcast.podName || podcast.name || "Podcast"}" class="podcast-image" style="width: 40px; height: 40px; border-radius: 8px; margin-right: 10px;">` : '<i class="fas fa-podcast"></i>'}
          <span class="podcast-name">${podcast.podName || podcast.name || "Unnamed Podcast"}</span>
        </div>
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
      item.innerHTML = `<span class="font-medium">${episode.title || "Untitled Episode"}</span>`
      item.addEventListener("click", () => {
        selectEpisode(episode)
        toggleEpisodeDropdown()
      })
      dropdown.appendChild(item)
    })
  }

  // Fix the renderTaskList function to ensure buttons work even when there are no tasks
  function renderTaskList() {
    const taskList = document.getElementById("taskList")
    if (!taskList) return

    taskList.innerHTML = ""

    // Check if we have tasks for the selected episode
    const episodeTasks = state.tasks.filter(
      (task) => task.episodeId === state.selectedEpisode?._id || task.episodeId === state.selectedEpisode?.id,
    )

    // Only use tasks that belong to the current episode
    const tasksToRender = episodeTasks

    // Check task dependencies
    const completedTaskIds = new Set(
      tasksToRender.filter((task) => task.status === "completed").map((task) => task.id || task._id),
    )

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
      addTaskBtn.addEventListener("click", () => showAddTaskModal())
    }

    const importTasksBtn = document.getElementById("import-default-tasks")
    if (importTasksBtn) {
      importTasksBtn.addEventListener("click", () => showImportTasksModal())
    }

    // Render tasks or empty state
    if (tasksToRender.length === 0) {
      const emptyState = document.createElement("div")
      emptyState.className = "empty-task-list"
      emptyState.innerHTML = `<p>No tasks available</p>`
      taskList.appendChild(emptyState)
    } else {
      // Render each task
      tasksToRender.forEach((task) => {
        const isCompleted = state.completedTasks[task.id || task._id] || task.status === "completed"
        const isExpanded = state.expandedTasks[task.id || task._id] || false
        const isAssignedToCurrentUser = task.assignee === state.currentUser.id

        // Check if this task has dependencies that aren't completed
        const hasDependencyWarning =
          task.dependencies &&
          task.dependencies.length > 0 &&
          !task.dependencies.every((depId) => completedTaskIds.has(depId))

        // Get dependency names for display
        const dependencyNames =
          task.dependencies && task.dependencies.length > 0
            ? task.dependencies.map((depId) => {
                const depTask = tasksToRender.find((t) => (t.id || t._id) === depId)
                return depTask ? depTask.name : "Unknown Task"
              })
            : []

        // Get dependency statuses for display
        const dependencyStatuses =
          task.dependencies && task.dependencies.length > 0
            ? task.dependencies.map((depId) => {
                const depTask = tasksToRender.find((t) => (t.id || t._id) === depId)
                return depTask ? (depTask.status === "completed" ? "completed" : "pending") : "pending"
              })
            : []

        const taskItem = document.createElement("div")
        taskItem.className = "task-item"
        taskItem.dataset.taskId = task.id || task._id
        taskItem.innerHTML = `
    <div class="task-header ${isCompleted ? "completed" : ""}">
      <div class="task-checkbox ${isCompleted ? "checked" : ""} ${hasDependencyWarning && !isCompleted ? "disabled" : ""}" data-task-id="${task.id || task._id}">
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
      <span>${formatDueDate(task.dueDate) || "No due date"}</span>
    </div>
    <div class="task-meta-item">
      <i class="fas fa-user"></i>
      <span>${task.assignedAt || "Unassigned"}</span>
    </div>
    ${
      task.comments && task.comments.length > 0
        ? `
      <span class="task-badge">${task.comments.length} ${task.comments.length === 1 ? "comment" : "comments"}</span>
    `
        : ""
    }
    ${
      hasDependencyWarning
        ? `
      <span class="task-badge warning">Waiting for dependencies</span>
    `
        : ""
    }
  </div>
`
            : ""
        }
      </div>
      <div class="task-actions">
        ${hasDependencyWarning ? '<i class="fas fa-exclamation-triangle text-warning" title="This task has incomplete dependencies"></i>' : ""}
        <button class="task-action-btn edit-task-btn" title="Edit Task" data-task-id="${task.id || task._id}">
          <i class="fas fa-edit"></i>
        </button>
        <button class="task-action-btn delete-task-btn" title="Delete Task" data-task-id="${task.id || task._id}">
          <i class="fas fa-trash"></i>
        </button>
        <button class="task-action-btn assign-task-btn" title="${isAssignedToCurrentUser ? "Unassign Task" : "Assign to me"}" data-task-id="${task.id || task._id}">
          <i class="fas ${isAssignedToCurrentUser ? "fa-user-minus" : "fa-user-plus"}"></i>
        </button>
      </div>
    </div>
    
    <div class="task-details ${isExpanded ? "expanded" : ""}">
      <p class="task-description">${task.description || "No description available"}</p>
      
      ${
        dependencyNames.length > 0
          ? `
        <div class="task-dependencies">
          <h4>Dependencies:</h4>
          <ul class="task-dependency-list">
            ${dependencyNames
              .map(
                (name, index) => `
              <li class="task-dependency-item">
                <span class="dependency-status ${dependencyStatuses[index]}"></span>
                ${name} <span class="dependency-status-text">(${dependencyStatuses[index] === "completed" ? "Completed" : "Pending"})</span>
              </li>
            `,
              )
              .join("")}
          </ul>
          ${
            hasDependencyWarning
              ? `
            <div class="task-dependency-warning">
              <i class="fas fa-exclamation-triangle"></i>
              <span>This task cannot be completed until all dependencies are completed.</span>
            </div>
          `
              : ""
          }
        </div>
      `
          : ""
      }
      
      <div class="task-footer">
        <div class="task-footer-meta">
          <div class="task-meta-item">
            <i class="fas fa-clock"></i>
            <span>Due: ${formatDueDate(task.dueDate) || "No due date"}</span>
          </div>
          <div class="task-meta-item">
            <i class="fas fa-user"></i>
            <span>Assigned to: ${task.assignedAt || "Unassigned"}</span>
          </div>
        </div>
        
        <div class="task-footer-actions">
          <button class="btn btn-outline btn-sm add-comment-btn" data-task-id="${task.id || task._id}">
            <i class="fas fa-comment"></i>
            <span>Add Comment</span>
          </button>
        </div>
      </div>
      
      ${renderTaskComments(task)}
    </div>
  `

        taskList.appendChild(taskItem)
      })
    }

    // Always add workflow actions at the bottom
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
      saveWorkflowBtn.addEventListener("click", () => saveWorkflow())
    }

    const importWorkflowBtn = document.getElementById("import-workflow")
    if (importWorkflowBtn) {
      importWorkflowBtn.addEventListener("click", () => showImportWorkflowModal())
    }

    // Add event listeners for task interactions
    setupTaskInteractions()
  }

  // Helper function to format due date
  function formatDueDate(dueDate) {
    if (!dueDate) return ""

    // If it's a relative date (like "Before recording"), return as is
    if (
      typeof dueDate === "string" &&
      (dueDate.includes("before") || dueDate.includes("after") || dueDate.includes("Recording day"))
    ) {
      return dueDate
    }

    // If it's a timestamp, format it
    try {
      const date = new Date(dueDate)
      if (!isNaN(date.getTime())) {
        return date.toLocaleString()
      }
    } catch (e) {
      // If parsing fails, return the original string
    }

    return dueDate
  }

  function renderTaskComments(task) {
    if (!task.comments || task.comments.length === 0) {
      return `
        <div class="task-comments">
          <h4 class="comments-title">Comments</h4>
          <p class="no-comments">No comments yet</p>
        </div>
      `
    }

    const commentsHTML = task.comments
      .map(
        (comment) => `
      <div class="comment-item">
        <div class="comment-header">
          <span class="comment-author">${comment.userName || "Anonymous"}</span>
          <span class="comment-date">${new Date(comment.createdAt).toLocaleString()}</span>
        </div>
        <div class="comment-text">${comment.text}</div>
      </div>
    `,
      )
      .join("")

    return `
      <div class="task-comments">
        <h4 class="comments-title">Comments (${task.comments.length})</h4>
        <div class="comments-list">
          ${commentsHTML}
        </div>
      </div>
    `
  }

  // Fix the renderKanbanBoard function to have only 3 columns and no settings button
  function renderKanbanBoard() {
    const kanbanBoard = document.getElementById("kanbanBoard")
    if (!kanbanBoard) return

    kanbanBoard.innerHTML = ""

    // Define columns for the Kanban board - simplified to 3 columns
    const columns = [
      { id: "todo", title: "To Do", color: "kanban-column-todo" },
      { id: "in-progress", title: "In Progress", color: "kanban-column-progress" },
      { id: "completed", title: "Completed", color: "kanban-column-published" },
    ]

    // Check if we have tasks for the selected episode
    const episodeTasks = state.tasks.filter(
      (task) => task.episodeId === state.selectedEpisode?._id || task.episodeId === state.selectedEpisode?.id,
    )

    // Only use tasks that belong to the current episode
    const tasksToRender = episodeTasks

    // Group tasks by status
    const tasksByStatus = {
      todo:
        tasksToRender.filter((task) => task.status === "not-started" || task.status === "incomplete" || !task.status) ||
        [],
      "in-progress": tasksToRender.filter((task) => task.status === "in-progress") || [],
      completed: tasksToRender.filter((task) => task.status === "completed" || task.status === "published") || [],
    }

    // Check task dependencies
    const completedTaskIds = new Set(
      tasksToRender.filter((task) => task.status === "completed").map((task) => task.id || task._id),
    )

    // Create the board header with title only (no settings)
    const boardHeader = document.createElement("div")
    boardHeader.className = "board-header"
    boardHeader.innerHTML = `<h2>Kanban Board</h2>`
    kanbanBoard.appendChild(boardHeader)

    // Create the columns container with fixed width for each column
    const columnsContainer = document.createElement("div")
    columnsContainer.className = "kanban-columns"
    columnsContainer.style.display = "grid"
    columnsContainer.style.gridTemplateColumns = "1fr 1fr 1fr" // Equal width for all 3 columns
    columnsContainer.style.gap = "16px"
    kanbanBoard.appendChild(columnsContainer)

    columns.forEach((column) => {
      const columnDiv = document.createElement("div")
      columnDiv.className = `kanban-column ${column.color}`
      columnDiv.style.minHeight = "300px" // Ensure minimum height
      columnDiv.innerHTML = `
        <div class="kanban-column-header">
          <span>${column.title}</span>
        </div>
        <div class="kanban-column-content" data-column-id="${column.id}">
          ${
            tasksByStatus[column.id].length === 0
              ? `<div class="kanban-empty">No tasks</div>`
              : tasksByStatus[column.id]
                  .map((task) => {
                    // Check if this task has dependencies that aren't completed
                    const hasDependencyWarning =
                      task.dependencies &&
                      task.dependencies.length > 0 &&
                      !task.dependencies.every((depId) => completedTaskIds.has(depId))

                    return `
                        <div class="kanban-task ${hasDependencyWarning ? "has-dependency-warning" : ""}" draggable="true" data-task-id="${task.id || task._id}">
                          <div class="kanban-task-header">
                            <h3 class="kanban-task-title">${task.name}</h3>
                            ${hasDependencyWarning ? '<i class="fas fa-exclamation-triangle text-warning" title="This task has incomplete dependencies"></i>' : ""}
                          </div>
                          <div class="kanban-task-meta">
                            <div class="task-meta-item">
                              <i class="fas fa-clock"></i>
                              <span>${formatDueDate(task.dueDate) || "No due date"}</span>
                            </div>
                          </div>
                          <div class="kanban-task-footer">
                            <div class="kanban-task-assignee ${task.assignee ? "assigned" : ""}">
                              ${task.assigneeName || "Unassigned"}
                            </div>
                            ${
                              task.comments && task.comments.length > 0
                                ? `
                              <div class="kanban-task-comments">
                                <i class="fas fa-comment"></i> ${task.comments.length}
                              </div>
                            `
                                : ""
                            }
                          </div>
                        </div>
                      `
                  })
                  .join("")
          }
        </div>
      `

      columnsContainer.appendChild(columnDiv)
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

        // If the workflow tab is selected, render the workflow editor
        if (tabId === "dependencies") {
          renderWorkflowEditor()
        }
      })
    })

    // Update the dependencies tab button to say "Edit Workflow"
    const dependenciesTabBtn = document.querySelector('.tab-btn[data-tab="dependencies"]')
    if (dependenciesTabBtn) {
      dependenciesTabBtn.innerHTML = `
        <i class="fas fa-file-alt"></i>
        <span>Edit Workflow</span>
      `
    }
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

    // Only use tasks that belong to the current episode
    const tasksToRender = episodeTasks

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

    // Assign task buttons
    document.querySelectorAll(".assign-task-btn").forEach((button) => {
      button.addEventListener("click", () => {
        const taskId = button.getAttribute("data-task-id")
        toggleTaskAssignment(taskId)
      })
    })

    // Add comment buttons
    document.querySelectorAll(".add-comment-btn").forEach((button) => {
      button.addEventListener("click", () => {
        const taskId = button.getAttribute("data-task-id")
        showAddCommentModal(taskId)
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

    // Check if this task has dependencies that aren't completed
    if (task.dependencies && task.dependencies.length > 0 && task.status !== "completed") {
      const completedTaskIds = new Set(state.tasks.filter((t) => t.status === "completed").map((t) => t.id || t._id))

      const hasUncompletedDependencies = !task.dependencies.every((depId) => completedTaskIds.has(depId))

      if (hasUncompletedDependencies) {
        // Show a more detailed error message with the list of incomplete dependencies
        const incompleteDependencies = task.dependencies
          .filter((depId) => !completedTaskIds.has(depId))
          .map((depId) => {
            const depTask = state.tasks.find((t) => (t.id || t._id) === depId)
            return depTask ? depTask.name : "Unknown Task"
          })

        alert(
          `This task cannot be completed until its dependencies are completed:\n\n${incompleteDependencies.join("\n")}`,
        )
        return
      }
    }

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

  async function toggleTaskAssignment(taskId) {
    // Find the task
    const task = state.tasks.find((t) => t.id === taskId || t._id === taskId)
    if (!task) return

    try {
      // Get the current assignment status
      const isCurrentlyAssigned = task.assignee === state.currentUser.id

      if (isCurrentlyAssigned) {
        // If already assigned to current user, unassign
        await updateTask(taskId, {
          assignee: null,
          assigneeName: null,
          assignedAt: null,
        })

        // Update local state
        task.assignee = null
        task.assigneeName = null
        task.assignedAt = null
      } else {
        // Show loading state on the button
        const button = document.querySelector(`.assign-task-btn[data-task-id="${taskId}"]`)
        if (button) {
          const originalHTML = button.innerHTML
          button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>'
          button.disabled = true
        }

        // Fetch the user's profile to get their full name
        const profileData = await fetchProfile()
        console.log("Fetched profile data:", profileData)

        // Extract user information from profile data
        const userId = profileData.user?._id || profileData._id || state.currentUser.id

        // Get the full name from profile - handle both camelCase and snake_case formats
        const fullName =
          profileData.user?.fullName ||
          profileData.user?.full_name ||
          profileData.fullName ||
          profileData.full_name ||
          "Unknown User"

        console.log(`Using name: ${fullName} for task assignment`)

        // Update task in the database - use assignedAt as the source of truth
        await updateTask(taskId, {
          assignee: userId,
          assigneeName: fullName, // Keep this for backward compatibility
          assignedAt: fullName, // This is now the primary field for assignment
        })

        // Update local state
        task.assignee = userId
        task.assigneeName = fullName
        task.assignedAt = fullName

        // Reset button state
        if (button) {
          button.innerHTML = '<i class="fas fa-user-minus"></i>'
          button.disabled = false
        }
      }

      // Update UI
      renderTaskList()
      renderKanbanBoard()
    } catch (error) {
      console.error("Error updating task assignment:", error)
      alert("Failed to update task assignment. Please try again.")

      // Reset button state in case of error
      const button = document.querySelector(`.assign-task-btn[data-task-id="${taskId}"]`)
      if (button) {
        button.innerHTML = '<i class="fas fa-user-plus"></i>'
        button.disabled = false
      }
    }
  }

  // Fixed: Make the comment modal a proper popup
  function showAddCommentModal(taskId) {
    // Find the task
    const task = state.tasks.find((t) => t.id === taskId || t._id === taskId)
    if (!task) return

    const modalHTML = `
      <div id="add-comment-modal" class="popup">
        <div class="popup-content">
          <div class="modal-header">
            <h2>Add Comment</h2>
            <button class="close-btn">&times;</button>
          </div>
          <div class="popup-body">
            <form id="add-comment-form">
              <input type="hidden" id="comment-task-id" value="${taskId}">
              <div class="form-group">
                <label for="comment-text">Comment</label>
                <textarea id="comment-text" class="form-control" placeholder="Write your comment here..." required></textarea>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" id="cancel-comment-btn" class="btn cancel-btn">Cancel</button>
            <button type="button" id="save-comment-btn" class="btn save-btn">Add Comment</button>
          </div>
        </div>
      </div>
    `

    document.body.insertAdjacentHTML("beforeend", modalHTML)
    const popup = document.getElementById("add-comment-modal")

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
    const cancelBtn = document.getElementById("cancel-comment-btn")
    cancelBtn.addEventListener("click", () => {
      closePopup(popup)
    })

    // Close when clicking outside
    popup.addEventListener("click", (e) => {
      if (e.target === popup) {
        closePopup(popup)
      }
    })

    // Save comment event
    document.getElementById("save-comment-btn").addEventListener("click", async () => {
      const commentText = document.getElementById("comment-text").value.trim()
      if (!commentText) return

      try {
        const saveBtn = document.getElementById("save-comment-btn")
        const originalText = saveBtn.innerHTML
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...'
        saveBtn.disabled = true

        // Create new comment object
        const newComment = {
          id: Date.now().toString(),
          text: commentText,
          userId: state.currentUser.id,
          userName: state.currentUser.name,
          createdAt: new Date().toISOString(),
        }

        // Add comment to task
        task.comments = task.comments || []
        task.comments.push(newComment)

        // Update task in database
        await updateTask(taskId, { comments: task.comments })

        closePopup(popup)
        renderTaskList()
        renderKanbanBoard()
      } catch (error) {
        console.error("Error adding comment:", error)
        alert("Failed to add comment. Please try again.")

        const saveBtn = document.getElementById("save-comment-btn")
        saveBtn.disabled = false
        saveBtn.innerHTML = originalText
      } finally {
        const saveBtn = document.getElementById("save-comment-btn")
        if (saveBtn) {
          saveBtn.disabled = false
          saveBtn.innerHTML = "Add Comment"
        }
      }
    })
  }

  // Helper function to close any popup with animation
  function closePopup(popup) {
    const popupContent = popup.querySelector(".popup-content")
    popupContent.classList.remove("show")
    popupContent.classList.add("hide")

    // Remove popup after animation completes
    setTimeout(() => {
      if (popup && popup.parentNode) {
        popup.parentNode.removeChild(popup)
      }
    }, 300)
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

          // Check if this task has dependencies and is being moved to completed
          if (columnId === "completed") {
            const task = state.tasks.find((t) => (t.id || t._id) === taskId)
            if (task && task.dependencies && task.dependencies.length > 0) {
              const completedTaskIds = new Set(
                state.tasks.filter((t) => t.status === "completed").map((t) => t.id || t._id),
              )

              const hasUncompletedDependencies = !task.dependencies.every((depId) => completedTaskIds.has(depId))

              if (hasUncompletedDependencies) {
                // Show error and prevent the drop
                alert("This task cannot be completed until all its dependencies are completed.")
                return
              }
            }
          }

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

  // Update the updateTaskStatus function to handle only 3 columns
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
      case "completed":
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

  function setupModalButtons() {
    // Create modal containers if they don't exist
    if (!document.getElementById("modal-container")) {
      const modalContainer = document.createElement("div")
      modalContainer.id = "modal-container"
      document.body.appendChild(modalContainer)
    }
  }

  // Render the workflow editor (replacing the dependencies tab)
  function renderWorkflowEditor() {
    const dependencyView = document.getElementById("dependencyView")
    if (!dependencyView) return

    dependencyView.innerHTML = ""

    // Create the workflow editor UI
    const workflowEditorHTML = `
      <div class="workflow-editor">
        <div class="workflow-header">
          <h3>Edit Workflow</h3>
          <p>Select a workflow to edit or create a new one from the current tasks.</p>
        </div>
        
        <div class="workflow-selector">
          <label for="workflow-select">Select Workflow:</label>
          <select id="workflow-select" class="form-control">
            <option value="">-- Select a workflow --</option>
            ${state.workflows
              .map((workflow) => `<option value="${workflow._id}">${workflow.name || "Unnamed Workflow"}</option>`)
              .join("")}
          </select>
          <button id="load-workflow-btn" class="btn btn-primary" disabled>
            <i class="fas fa-download"></i> Load Workflow
          </button>
        </div>
        
        <div class="workflow-tasks-container">
          <div class="workflow-tasks-header">
            <h4>Workflow Tasks</h4>
            <button id="add-workflow-task-btn" class="btn btn-sm btn-primary" disabled>
              <i class="fas fa-plus"></i> Add Task
            </button>
          </div>
          <div id="workflow-tasks" class="workflow-tasks">
            <p class="empty-state">Select a workflow to view and edit its tasks</p>
          </div>
        </div>
        
        <div class="workflow-actions">
          <button id="save-workflow-changes-btn" class="btn btn-success" disabled>
            <i class="fas fa-save"></i> Save Changes
          </button>
          <button id="delete-workflow-btn" class="btn btn-danger" disabled>
            <i class="fas fa-trash"></i> Delete Workflow
          </button>
        </div>
      </div>
    `

    dependencyView.innerHTML = workflowEditorHTML

    // Set up event listeners
    const workflowSelect = document.getElementById("workflow-select")
    const loadWorkflowBtn = document.getElementById("load-workflow-btn")
    const createWorkflowBtn = document.getElementById("create-workflow-btn")
    const saveChangesBtn = document.getElementById("save-workflow-changes-btn")
    const deleteWorkflowBtn = document.getElementById("delete-workflow-btn")

    if (workflowSelect) {
      workflowSelect.addEventListener("change", () => {
        loadWorkflowBtn.disabled = !workflowSelect.value
        deleteWorkflowBtn.disabled = !workflowSelect.value
      })
    }

    if (loadWorkflowBtn) {
      loadWorkflowBtn.addEventListener("click", () => {
        const workflowId = workflowSelect.value
        if (workflowId) {
          loadWorkflowForEditing(workflowId)
        }
      })
    }

    if (createWorkflowBtn) {
      createWorkflowBtn.addEventListener("click", () => {
        showCreateWorkflowModal()
      })
    }

    if (saveChangesBtn) {
      saveChangesBtn.addEventListener("click", () => {
        saveWorkflowChanges()
      })
    }

    // Add event listener for delete workflow button
    if (deleteWorkflowBtn) {
      deleteWorkflowBtn.addEventListener("click", () => {
        const workflowId = workflowSelect.value
        if (workflowId) {
          confirmDeleteWorkflow(workflowId)
        }
      })
    }

    // Add event listener for add task button
    const addWorkflowTaskBtn = document.getElementById("add-workflow-task-btn")
    if (addWorkflowTaskBtn) {
      addWorkflowTaskBtn.addEventListener("click", () => {
        const workflowId = workflowSelect.value
        if (workflowId) {
          addTaskToWorkflow(workflowId)
        }
      })
    }

    // Add CSS for the workflow editor
    const style = document.createElement("style")
    style.textContent = `
      .workflow-editor {
        padding: 15px;
      }
      .workflow-header {
        margin-bottom: 20px;
      }
      .workflow-selector {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 20px;
      }
      .workflow-selector select {
        flex: 1;
      }
      .workflow-tasks-container {
        margin-bottom: 20px;
      }
      .workflow-tasks {
        min-height: 200px;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 10px;
        background-color: #f9f9f9;
      }
      .workflow-task-item {
        display: flex;
        align-items: center;
        padding: 10px;
        border-bottom: 1px solid #eee;
        background-color: white;
        margin-bottom: 8px;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      }
      .workflow-task-item:last-child {
        border-bottom: none;
      }
      .workflow-task-name {
        flex: 1;
        font-weight: 500;
      }
      .workflow-task-actions {
        display: flex;
        gap: 5px;
      }
      .workflow-actions {
        display: flex;
        justify-content: space-between;
        margin-top: 20px;
      }
      .empty-state {
        text-align: center;
        color: #888;
        padding: 20px;
      }
      .btn-danger {
        background-color: #dc3545;
        color: white;
        border: none;
      }
      .btn-danger:hover {
        background-color: #c82333;
      }
      .workflow-tasks-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
      }
      .btn-primary {
        background-color: #007bff;
        color: white;
        border: none;
      }
      .btn-primary:hover {
        background-color: #0069d9;
      }
      .btn-sm {
        padding: 4px 8px;
        font-size: 0.875rem;
      }
    `
    document.head.appendChild(style)
  }

  // Add function to confirm and delete a workflow
  async function confirmDeleteWorkflow(workflowId) {
    if (confirm("Are you sure you want to delete this workflow? This action cannot be undone.")) {
      try {
        const deleteBtn = document.getElementById("delete-workflow-btn")
        const originalText = deleteBtn.innerHTML
        deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...'
        deleteBtn.disabled = true

        // Call the API to delete the workflow
        await deleteWorkflow(workflowId)

        // Remove the workflow from the state
        state.workflows = state.workflows.filter((w) => w._id !== workflowId)

        // Update the workflow selector
        const workflowSelect = document.getElementById("workflow-select")
        if (workflowSelect) {
          const optionToRemove = workflowSelect.querySelector(`option[value="${workflowId}"]`)
          if (optionToRemove) {
            workflowSelect.removeChild(optionToRemove)
          }
          workflowSelect.value = ""
        }

        // Clear the workflow tasks display
        const workflowTasks = document.getElementById("workflow-tasks")
        if (workflowTasks) {
          workflowTasks.innerHTML = `<p class="empty-state">Select a workflow to view and edit its tasks</p>`
        }

        // Disable buttons
        const saveChangesBtn = document.getElementById("save-workflow-changes-btn")
        if (saveChangesBtn) {
          saveChangesBtn.disabled = true
        }

        deleteBtn.disabled = true
        deleteBtn.innerHTML = originalText

        alert("Workflow deleted successfully!")
      } catch (error) {
        console.error("Error deleting workflow:", error)
        alert("Failed to delete workflow. Please try again.")

        const deleteBtn = document.getElementById("delete-workflow-btn")
        deleteBtn.disabled = false
        deleteBtn.innerHTML = '<i class="fas fa-trash"></i> Delete Workflow'
      }
    }
  }

  // Load a workflow for editing
  async function loadWorkflowForEditing(workflowId) {
    try {
      // Find the workflow in the state
      const workflow = state.workflows.find((w) => w._id === workflowId)

      if (!workflow) {
        console.error("Workflow not found:", workflowId)
        return
      }

      console.log("Loading workflow for editing:", workflow)

      const workflowTasksContainer = document.getElementById("workflow-tasks")
      const saveChangesBtn = document.getElementById("save-workflow-changes-btn")

      if (workflowTasksContainer) {
        // Clear the container
        workflowTasksContainer.innerHTML = ""

        // Check if workflow has tasks
        if (!workflow.tasks || workflow.tasks.length === 0) {
          workflowTasksContainer.innerHTML = `<p class="empty-state">This workflow has no tasks</p>`
          return
        }

        // Render each task in the workflow
        workflow.tasks.forEach((task) => {
          const taskItem = document.createElement("div")
          taskItem.className = "workflow-task-item"
          taskItem.dataset.taskId = task._id || task.id

          taskItem.innerHTML = `
            <div class="workflow-task-name">${task.name || "Unnamed Task"}</div>
            <div class="workflow-task-meta">
              <div class="task-meta-item">
                <i class="fas fa-clock"></i>
                <span>${formatDueDate(task.dueDate) || "No due date"}</span>
              </div>
            </div>
            <div class="workflow-task-actions">
              <button class="btn btn-sm btn-outline edit-workflow-task-btn" data-task-id="${task._id || task.id}">
                <i class="fas fa-edit"></i>
              </button>
              <button class="btn btn-sm btn-outline remove-workflow-task-btn" data-task-id="${task._id || task.id}">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          `

          workflowTasksContainer.appendChild(taskItem)
        })

        // Add event listeners for task actions
        document.querySelectorAll(".edit-workflow-task-btn").forEach((btn) => {
          btn.addEventListener("click", () => {
            const taskId = btn.getAttribute("data-task-id")
            editWorkflowTask(workflowId, taskId)
          })
        })

        document.querySelectorAll(".remove-workflow-task-btn").forEach((btn) => {
          btn.addEventListener("click", () => {
            const taskId = btn.getAttribute("data-task-id")
            removeTaskFromWorkflow(workflowId, taskId)
          })
        })

        // Enable the save changes button
        if (saveChangesBtn) {
          saveChangesBtn.disabled = false
        }

        // Enable the add task button
        const addWorkflowTaskBtn = document.getElementById("add-workflow-task-btn")
        if (addWorkflowTaskBtn) {
          addWorkflowTaskBtn.disabled = false
        }
      }
    } catch (error) {
      console.error("Error loading workflow for editing:", error)
      alert("Failed to load workflow. Please try again.")
    }
  }

  // Edit a task in the workflow
  function editWorkflowTask(workflowId, taskId) {
    // Find the workflow
    const workflow = state.workflows.find((w) => w._id === workflowId)
    if (!workflow) return

    // Find the task in the workflow
    const task = workflow.tasks.find((t) => (t._id || t.id) === taskId)
    if (!task) return

    const modalHTML = `
      <div id="edit-workflow-task-modal" class="popup">
        <div class="popup-content">
          <div class="modal-header">
            <h2>Edit Workflow Task</h2>
            <button class="close-btn">&times;</button>
          </div>
          <div class="popup-body">
            <form id="edit-workflow-task-form">
              <input type="hidden" id="edit-workflow-id" value="${workflowId}">
              <input type="hidden" id="edit-workflow-task-id" value="${taskId}">
              
              <div class="form-group">
                <label for="edit-workflow-task-name">Task Name</label>
                <input type="text" id="edit-workflow-task-name" class="form-control" value="${task.name || ""}" required>
              </div>
              
              <div class="form-group">
                <label for="edit-workflow-task-description">Description</label>
                <textarea id="edit-workflow-task-description" class="form-control">${task.description || ""}</textarea>
              </div>
              
              <div class="form-group">
                <label for="edit-workflow-task-due-date">Due Date</label>
                <input type="text" id="edit-workflow-task-due-date" class="form-control date-picker" value="${task.dueDate || ""}">
                <small class="help-text">Select a specific date and time or use relative terms like "Before recording", "3 days before recording"</small>
              </div>
              
              <div class="form-group">
                <label for="edit-workflow-task-assigned">Assigned To</label>
                <input type="text" id="edit-workflow-task-assigned" class="form-control" value="${task.assigneeName || ""}">
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" id="cancel-edit-workflow-task-btn" class="btn cancel-btn">Cancel</button>
            <button type="button" id="save-workflow-task-btn" class="btn save-btn">Save Changes</button>
          </div>
        </div>
      </div>
    `

    document.body.insertAdjacentHTML("beforeend", modalHTML)
    const popup = document.getElementById("edit-workflow-task-modal")

    // Show the popup
    popup.style.display = "flex"

    // Add class to animate in
    setTimeout(() => {
      popup.querySelector(".popup-content").classList.add("show")

      // Initialize date picker
      if (typeof flatpickr !== "undefined") {
        flatpickr("#edit-workflow-task-due-date", {
          enableTime: true,
          dateFormat: "Y-m-d H:i",
          allowInput: true,
          time_24hr: false,
        })
      }
    }, 10)

    // Close button event
    const closeBtn = popup.querySelector(".close-btn")
    closeBtn.addEventListener("click", () => {
      closePopup(popup)
    })

    // Cancel button event
    const cancelBtn = document.getElementById("cancel-edit-workflow-task-btn")
    cancelBtn.addEventListener("click", () => {
      closePopup(popup)
    })

    // Close when clicking outside
    popup.addEventListener("click", (e) => {
      if (e.target === popup) {
        closePopup(popup)
      }
    })

    // Save changes event
    document.getElementById("save-workflow-task-btn").addEventListener("click", () => {
      const name = document.getElementById("edit-workflow-task-name").value
      const description = document.getElementById("edit-workflow-task-description").value
      const dueDate = document.getElementById("edit-workflow-task-due-date").value
      const assigneeName = document.getElementById("edit-workflow-task-assigned").value

      // Update the task in the workflow
      task.name = name
      task.description = description
      task.dueDate = dueDate
      task.assigneeName = assigneeName

      // Reload the workflow editor
      loadWorkflowForEditing(workflowId)

      // Close the popup
      closePopup(popup)
    })
  }

  // Remove a task from the workflow
  function removeTaskFromWorkflow(workflowId, taskId) {
    // Find the workflow
    const workflow = state.workflows.find((w) => w._id === workflowId)
    if (!workflow) return

    // Confirm removal
    if (confirm("Are you sure you want to remove this task from the workflow?")) {
      // Remove the task from the workflow
      workflow.tasks = workflow.tasks.filter((t) => (t._id || t.id) !== taskId)

      // Reload the workflow editor
      loadWorkflowForEditing(workflowId)
    }
  }

  // Add a new task to the workflow
  function addTaskToWorkflow(workflowId) {
    // Find the workflow
    const workflow = state.workflows.find((w) => w._id === workflowId)
    if (!workflow) return

    const modalHTML = `
      <div id="add-workflow-task-modal" class="popup">
        <div class="popup-content">
          <div class="modal-header">
            <h2>Add Task to Workflow</h2>
            <button class="close-btn">&times;</button>
          </div>
          <div class="popup-body">
            <form id="add-workflow-task-form">
              <input type="hidden" id="add-workflow-id" value="${workflowId}">
            
              <div class="form-group">
                <label for="add-workflow-task-name">Task Name</label>
                <input type="text" id="add-workflow-task-name" class="form-control" placeholder="Enter task name" required>
            </div>
            
            <div class="form-group">
              <label for="add-workflow-task-description">Description</label>
              <textarea id="add-workflow-task-description" class="form-control" placeholder="Describe this task..."></textarea>
            </div>
            
            <div class="form-group">
              <label for="add-workflow-task-due-date">Due Date</label>
              <input type="text" id="add-workflow-task-due-date" class="form-control date-picker" placeholder="Select date and time">
              <small class="help-text">Select a specific date and time or use relative terms like "Before recording", "3 days before recording"</small>
            </div>
            
            <div class="form-group">
              <label for="add-workflow-task-assigned">Assigned To</label>
              <input type="text" id="add-workflow-task-assigned" class="form-control" placeholder="Name of person assigned">
            </div>
          </form>
        </div>
        <div class="modal-footer">
          <button type="button" id="cancel-add-workflow-task-btn" class="btn cancel-btn">Cancel</button>
          <button type="button" id="save-add-workflow-task-btn" class="btn save-btn">Add Task</button>
        </div>
      </div>
    </div>
  `

    document.body.insertAdjacentHTML("beforeend", modalHTML)
    const popup = document.getElementById("add-workflow-task-modal")

    // Show the popup
    popup.style.display = "flex"

    // Add class to animate in
    setTimeout(() => {
      popup.querySelector(".popup-content").classList.add("show")

      // Initialize date picker
      if (typeof flatpickr !== "undefined") {
        flatpickr("#add-workflow-task-due-date", {
          enableTime: true,
          dateFormat: "Y-m-d H:i",
          allowInput: true,
          time_24hr: false,
        })
      }
    }, 10)

    // Close button event
    const closeBtn = popup.querySelector(".close-btn")
    closeBtn.addEventListener("click", () => {
      closePopup(popup)
    })

    // Cancel button event
    const cancelBtn = document.getElementById("cancel-add-workflow-task-btn")
    cancelBtn.addEventListener("click", () => {
      closePopup(popup)
    })

    // Close when clicking outside
    popup.addEventListener("click", (e) => {
      if (e.target === popup) {
        closePopup(popup)
      }
    })

    // Save new task event
    document.getElementById("save-add-workflow-task-btn").addEventListener("click", () => {
      const name = document.getElementById("add-workflow-task-name").value
      const description = document.getElementById("add-workflow-task-description").value
      const dueDate = document.getElementById("add-workflow-task-due-date").value
      const assigneeName = document.getElementById("add-workflow-task-assigned").value

      if (!name) {
        alert("Task name is required")
        return
      }

      // Create a new task with a unique ID
      const newTask = {
        id: `task-${Date.now()}`,
        name: name,
        description: description,
        dueDate: dueDate,
        assigneeName: assigneeName,
        status: "not-started",
        dependencies: [],
      }

      // Add the task to the workflow
      workflow.tasks = workflow.tasks || []
      workflow.tasks.push(newTask)

      // Reload the workflow editor
      loadWorkflowForEditing(workflowId)

      // Close the popup
      closePopup(popup)
    })
  }

  // Save changes to the workflow
  async function saveWorkflowChanges() {
    const workflowSelect = document.getElementById("workflow-select")
    if (!workflowSelect || !workflowSelect.value) return

    const workflowId = workflowSelect.value
    const workflow = state.workflows.find((w) => w._id === workflowId)

    if (!workflow) {
      console.error("Workflow not found:", workflowId)
      return
    }

    try {
      const saveBtn = document.getElementById("save-workflow-changes-btn")
      const originalText = saveBtn.innerHTML
      saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...'
      saveBtn.disabled = true

      // Import the updateWorkflow function if it's not already imported
      // This assumes you've imported other functions from podtaskRequest.js already
      const { updateWorkflow } = await import("/static/requests/podtaskRequest.js")

      // Call the updateWorkflow function with the workflow data
      const result = await updateWorkflow(workflowId, {
        tasks: workflow.tasks,
        name: workflow.name,
        description: workflow.description,
      })

      alert("Workflow updated successfully!")

      // Reset button state
      saveBtn.innerHTML = '<i class="fas fa-save"></i> Save Changes'
      saveBtn.disabled = false
    } catch (error) {
      console.error("Error saving workflow changes:", error)
      alert("Failed to save workflow changes: " + (error.message || "Unknown error"))

      // Reset button state
      const saveBtn = document.getElementById("save-workflow-changes-btn")
      if (saveBtn) {
        saveBtn.innerHTML = '<i class="fas fa-save"></i> Save Changes'
        saveBtn.disabled = false
      }
    }
  }

  // Show modal to create a new workflow
  function showCreateWorkflowModal() {
    if (!state.selectedEpisode) {
      alert("Please select an episode first")
      return
    }

    const modalHTML = `
      <div id="create-workflow-modal" class="popup">
        <div class="popup-content">
          <div class="modal-header">
            <h2>Create New Workflow</h2>
            <button class="close-btn">&times;</button>
          </div>
          <div class="popup-body">
            <form id="create-workflow-form">
              <div class="form-group">
                <label for="new-workflow-name">Workflow Name</label>
                <input type="text" id="new-workflow-name" class="form-control" placeholder="Enter workflow name" required>
              </div>
              <div class="form-group">
                <label for="new-workflow-description">Description</label>
                <textarea id="new-workflow-description" class="form-control" placeholder="Describe this workflow..."></textarea>
              </div>
              <div class="form-group">
                <label>
                  <input type="checkbox" id="use-current-tasks" checked>
                  Use current episode tasks as template
                </label>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" id="cancel-create-workflow-btn" class="btn cancel-btn">Cancel</button>
            <button type="button" id="create-new-workflow-btn" class="btn save-btn">Create Workflow</button>
          </div>
        </div>
      </div>
    `

    document.body.insertAdjacentHTML("beforeend", modalHTML)
    const popup = document.getElementById("create-workflow-modal")

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
    const cancelBtn = document.getElementById("cancel-create-workflow-btn")
    cancelBtn.addEventListener("click", () => {
      closePopup(popup)
    })

    // Close when clicking outside
    popup.addEventListener("click", (e) => {
      if (e.target === popup) {
        closePopup(popup)
      }
    })

    // Create workflow event
    document.getElementById("create-new-workflow-btn").addEventListener("click", async () => {
      const name = document.getElementById("new-workflow-name").value
      const description = document.getElementById("new-workflow-description").value
      const useCurrentTasks = document.getElementById("use-current-tasks").checked

      if (!name) {
        alert("Workflow name is required")
        return
      }

      try {
        const createBtn = document.getElementById("create-new-workflow-btn")
        const originalText = createBtn.innerHTML
        createBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...'
        createBtn.disabled = true

        // Get tasks for this episode if using current tasks
        let tasks = []
        if (useCurrentTasks) {
          const episodeId = state.selectedEpisode._id || state.selectedEpisode.id
          tasks = state.tasks.filter((task) => task.episodeId === episodeId)
        }

        // Call the server to save the workflow
        const response = await fetch("/save_workflow", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: name,
            description: description,
            isTemplate: true,
            tasks: tasks,
          }),
        })

        const result = await response.json()

        if (response.ok) {
          // Add the new workflow to the state
          if (result.workflowId) {
            const newWorkflow = {
              _id: result.workflowId,
              name: name,
              description: description,
              tasks: tasks,
              isTemplate: true,
            }
            state.workflows.push(newWorkflow)

            // Update the workflow selector
            const workflowSelect = document.getElementById("workflow-select")
            if (workflowSelect) {
              const option = document.createElement("option")
              option.value = result.workflowId
              option.textContent = name
              workflowSelect.appendChild(option)
              workflowSelect.value = result.workflowId
            }

            // Load the new workflow for editing
            loadWorkflowForEditing(result.workflowId)
          }

          closePopup(popup)
          alert("Workflow created successfully!")
        } else {
          throw new Error(result.error || "Failed to create workflow")
        }
      } catch (error) {
        console.error("Error creating workflow:", error)
        alert("Failed to create workflow. Please try again.")

        const createBtn = document.getElementById("create-new-workflow-btn")
        createBtn.disabled = false
        createBtn.innerHTML = "Create Workflow"
      }
    })
  }

  // Modal functions
  // Fix the showAddTaskModal function to match the task.js implementation
  async function confirmDeleteTask(taskId) {
    if (confirm("Are you sure you want to delete this task?")) {
      try {
        await deleteTask(taskId)
        // Refresh tasks
        const episodeId = state.selectedEpisode._id || state.selectedEpisode.id
        const tasksData = await fetchTasks()
        state.tasks = tasksData ? tasksData.filter((task) => task.episodeId === episodeId) : []

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

  // Update the showEditTaskPopup function to match the task.js implementation
  async function showEditTaskPopup(taskId) {
    try {
      const response = await fetchTask(taskId)

      if (!response || !response[0] || !response[0].podtask) {
        console.error("Task not found:", taskId)
        return
      }

      const task = response[0].podtask
      console.log("Fetched task data:", task)

      const { name, description, status, dependencies = [], dueDate = "", assignee = null, assigneeName = "" } = task

      // Get all tasks for dependency selection
      const allTasks = state.tasks.filter((t) => t.id !== taskId && t._id !== taskId)

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
                <label for="edit-task-status">Status</label>
                <select id="edit-task-status" class="form-control">
                  <option value="not-started" ${status === "not-started" || status === "incomplete" ? "selected" : ""}>Not Started</option>
                  <option value="in-progress" ${status === "in-progress" ? "selected" : ""}>In Progress</option>
                  <option value="completed" ${status === "completed" ? "selected" : ""}>Completed</option>
                </select>
              </div>
              <div class="form-group">
                <label for="edit-task-due-date">Due Date</label>
                <input type="text" id="edit-task-due-date" class="form-control date-picker" value="${dueDate || ""}">
                <small class="help-text">Select a specific date and time or use relative terms like "Before recording", "3 days before recording"</small>
              </div>
              <div class="form-group">
                <label for="edit-task-assigned">Assigned To</label>
                <input type="text" id="edit-task-assigned" class="form-control" value="${assigneeName || ""}">
              </div>
              <div class="form-group">
                <label for="edit-task-dependencies">Dependencies</label>
                <div class="dependencies-container">
                  <select id="edit-task-dependencies" class="form-control" multiple>
                    ${allTasks.map((t) => `<option value="${t.id || t._id}" ${dependencies && dependencies.includes(t.id || t._id) ? "selected" : ""}>${t.name}</option>`).join("")}
                  </select>
                  <p class="help-text">Hold Ctrl/Cmd to select multiple tasks. This task will only be available when all selected tasks are completed.</p>
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" id="cancel-edit-btn" class="btn cancel-btn">Cancel</button>
            <button type="submit" id="save-edit-btn" class="btn save-btn">
              <i class="fas fa-save"></i> Save Changes
            </button>
          </div>
        </div>
      </div>
    `

      document.body.insertAdjacentHTML("beforeend", modalHTML)
      const popup = document.getElementById("edit-task-modal")

      // Show the popup
      popup.style.display = "flex"

      // Add class to animate in
      setTimeout(() => {
        popup.querySelector(".popup-content").classList.add("show")

        // Initialize date picker
        if (typeof flatpickr !== "undefined") {
          flatpickr("#edit-task-due-date", {
            enableTime: true,
            dateFormat: "Y-m-d H:i",
            allowInput: true,
            time_24hr: false,
          })
        }
      }, 10)

      // Close button event
      const closeBtn = popup.querySelector(".close-btn")
      closeBtn.addEventListener("click", () => {
        closePopup(popup)
      })

      // Cancel button event
      const cancelBtn = document.getElementById("cancel-edit-btn")
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
      const saveBtn = document.getElementById("save-edit-btn")
      saveBtn.addEventListener("click", async () => {
        const title = document.getElementById("edit-task-title").value
        const description = document.getElementById("edit-task-description").value
        const status = document.getElementById("edit-task-status").value
        const dueDate = document.getElementById("edit-task-due-date").value
        const assigneeName = document.getElementById("edit-task-assigned").value

        // Get selected dependencies
        const dependenciesSelect = document.getElementById("edit-task-dependencies")
        const selectedDependencies = Array.from(dependenciesSelect.selectedOptions).map((option) => option.value)

        const taskData = {
          name: title,
          description,
          status,
          dueDate,
          assigneeName,
          dependencies: selectedDependencies,
        }

        try {
          const originalText = saveBtn.innerHTML
          saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...'
          saveBtn.disabled = true

          await updateTask(taskId, taskData)
          closePopup(popup)

          // Refresh tasks
          const episodeId = state.selectedEpisode._id || state.selectedEpisode.id
          const tasksData = await fetchTasks()
          state.tasks = tasksData ? tasksData.filter((task) => task.episodeId === episodeId) : []

          renderTaskList()
          renderKanbanBoard()
          renderTimeline()
          updateProgressBar()
        } catch (error) {
          console.error("Error updating task:", error)
          alert("Failed to update task. Please try again.")

          saveBtn.disabled = false
          saveBtn.innerHTML = originalText
        }
      })
    } catch (error) {
      console.error("Error fetching task for editing:", error)
      alert("Failed to load task for editing. Please try again.")
    }
  }

  // Update the showAddTaskModal function to include dependencies
  function showAddTaskModal() {
    if (!state.selectedEpisode) {
      alert("Please select an episode first")
      return
    }

    const episodeId = state.selectedEpisode._id || state.selectedEpisode.id

    // Get all tasks for dependency selection
    const allTasks = state.tasks.filter((task) => task.episodeId === episodeId)

    const modalHTML = `
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
                <input type="text" id="task-due-date" class="form-control date-picker" placeholder="Select date and time">
                <small class="help-text">Select a specific date and time or use relative terms like "Before recording", "3 days before recording"</small>
              </div>
              <div class="form-group">
                <label for="task-assigned">Assigned To</label>
                <input type="text" id="task-assigned" class="form-control" placeholder="Name of person assigned">
              </div>
              <div class="form-group">
                <label for="task-dependencies">Dependencies</label>
                <div class="dependencies-container">
                  <select id="task-dependencies" class="form-control" multiple ${allTasks.length === 0 ? "disabled" : ""}>
                    ${
                      allTasks.length > 0
                        ? allTasks
                            .map((task) => `<option value="${task.id || task._id}">${task.name}</option>`)
                            .join("")
                        : "<option disabled>No tasks available for dependencies</option>"
                    }
                  </select>
                  <p class="help-text">Hold Ctrl/Cmd to select multiple tasks. This task will only be available when all selected tasks are completed.</p>
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" id="cancel-add-btn" class="btn cancel-btn">Cancel</button>
            <button type="button" id="save-task-btn" class="btn save-btn">
              <i class="fas fa-check"></i> Create Task
            </button>
          </div>
        </div>
      </div>
    `

    document.body.insertAdjacentHTML("beforeend", modalHTML)
    const popup = document.getElementById("task-popup")

    // Show the popup
    popup.style.display = "flex"

    // Add class to animate in
    setTimeout(() => {
      popup.querySelector(".popup-content").classList.add("show")

      // Initialize date picker
      if (typeof flatpickr !== "undefined") {
        flatpickr("#task-due-date", {
          enableTime: true,
          dateFormat: "Y-m-d H:i",
          allowInput: true,
          time_24hr: false,
        })
      }
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
    const saveBtn = document.getElementById("save-task-btn")
    saveBtn.addEventListener("click", async () => {
      const title = document.getElementById("task-title").value
      const description = document.getElementById("task-description").value
      const dueDate = document.getElementById("task-due-date").value
      const assigneeName = document.getElementById("task-assigned").value

      // Get selected dependencies
      const dependenciesSelect = document.getElementById("task-dependencies")
      const selectedDependencies =
        dependenciesSelect && !dependenciesSelect.disabled
          ? Array.from(dependenciesSelect.selectedOptions).map((option) => option.value)
          : []

      const taskData = {
        name: title,
        description,
        episodeId: episodeId,
        dueDate,
        assigneeName,
        dependencies: selectedDependencies,
      }

      try {
        // Show loading state
        const originalText = saveBtn.innerHTML
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...'
        saveBtn.disabled = true

        await saveTask(taskData)
        closePopup(popup)

        // Refresh tasks
        const tasksData = await fetchTasks()
        state.tasks = tasksData ? tasksData.filter((task) => task.episodeId === episodeId) : []

        renderTaskList()
        renderKanbanBoard()
        renderTimeline()
        updateProgressBar()
      } catch (error) {
        console.error("Error saving task:", error)
        // Reset button state
        saveBtn.innerHTML = originalText
        saveBtn.disabled = false
        alert("Failed to save task: " + (error.message || "Unknown error"))
      }
    })
  }

  // Update the showImportTasksModal function to include dependencies
  async function showImportTasksModal() {
    if (!state.selectedEpisode) {
      alert("Please select an episode first")
      return
    }

    const episodeId = state.selectedEpisode._id || state.selectedEpisode.id

    try {
      // Fetch default tasks from your JSON file
      const defaultTasks = await fetchLocalDefaultTasks()

      // Get all existing tasks for dependency selection
      const existingTasks = state.tasks.filter((task) => task.episodeId === episodeId)

      const modalHTML = `
        <div id="import-tasks-popup" class="popup">
          <div class="popup-content">
            <div class="modal-header">
              <h2>Import Default Tasks</h2>
              <button class="close-btn">&times;</button>
            </div>
            <div class="popup-body">
              <p>Select the default tasks you want to import:</p>
              <div class="import-tasks-container">
                ${defaultTasks
                  .map(
                    (task, index) => `
                  <div class="import-task-item">
                    <input type="checkbox" id="import-task-${index}" class="import-task-checkbox" value="${task}">
                    <label for="import-task-${index}" class="import-task-title">${task}</label>
                    
                    <div class="task-dependency-section" style="margin-left: 25px; margin-bottom: 10px;">
                      <label for="task-dep-${index}" style="display: block; font-size: 0.9rem; margin-bottom: 5px;">Dependencies:</label>
                      <select id="task-dep-${index}" class="task-dependency-select form-control" multiple ${existingTasks.length === 0 ? "disabled" : ""}>
                        ${
                          existingTasks.length > 0
                            ? existingTasks.map((t) => `<option value="${t.id || t._id}">${t.name}</option>`).join("")
                            : "<option disabled>No tasks available for dependencies</option>"
                        }
                      </select>
                    </div>
                  </div>
                `,
                  )
                  .join("")}
              </div>
            </div>
            <div class="modal-footer">
              <span class="selected-count">0 selected</span>
              <button id="cancel-import-btn" class="btn cancel-btn">Cancel</button>
              <button id="import-selected-btn" class="btn save-btn" disabled>
                <i class="fas fa-file-import"></i> Import Selected
              </button>
            </div>
          </div>
        </div>
      `

      document.body.insertAdjacentHTML("beforeend", modalHTML)
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

      const checkboxes = popup.querySelectorAll(".import-task-checkbox")
      const selectedCountEl = popup.querySelector(".selected-count")
      const importBtn = document.getElementById("import-selected-btn")

      checkboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", () => {
          const selectedCount = [...checkboxes].filter((cb) => cb.checked).length
          selectedCountEl.textContent = `${selectedCount} selected`
          importBtn.disabled = selectedCount === 0
        })
      })

      importBtn.addEventListener("click", async () => {
        // Get selected tasks as an array of objects with name and dependencies
        const selectedTasks = [...checkboxes]
          .filter((cb) => cb.checked)
          .map((cb, index) => {
            const taskName = cb.value
            const dependencySelect = document.getElementById(`task-dep-${index}`)
            const dependencies =
              dependencySelect && !dependencySelect.disabled
                ? Array.from(dependencySelect.selectedOptions).map((option) => option.value)
                : []

            return {
              name: taskName,
              dependencies: dependencies,
            }
          })

        try {
          // Show loading state
          const originalText = importBtn.innerHTML
          importBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Importing...'
          importBtn.disabled = true

          // Modified to handle task objects with dependencies
          for (const taskObj of selectedTasks) {
            await saveTask({
              name: taskObj.name,
              description: `Default task: ${taskObj.name}`,
              episodeId: episodeId,
              dependencies: taskObj.dependencies,
            })
          }

          closePopup(popup)

          // Refresh tasks
          const tasksData = await fetchTasks()
          state.tasks = tasksData ? tasksData.filter((task) => task.episodeId === episodeId) : []

          renderTaskList()
          renderKanbanBoard()
          renderTimeline()
          updateProgressBar()
        } catch (error) {
          console.error("Error importing default tasks:", error)
          // Reset button state
          importBtn.innerHTML = originalText
          importBtn.disabled = true
        }
      })
    } catch (error) {
      console.error("Error fetching default tasks:", error)
    }
  }

  // Fix the showImportWorkflowModal function to ensure the popup displays correctly
  function showImportWorkflowModal() {
    if (!state.selectedEpisode) {
      alert("Please select an episode first")
      return
    }

    const episodeId = state.selectedEpisode._id || state.selectedEpisode.id

    // First, fetch available workflows from the server
    fetch("/get_workflows", {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    })
      .then((response) => response.json())
      .then((data) => {
        const workflows = data.workflows || []

        const modalHTML = `
        <div id="import-workflow-modal" class="popup">
          <div class="popup-content">
            <div class="modal-header">
              <h2>Select a Workflow to Import</h2>
              <button class="close-btn">&times;</button>
            </div>
            <div class="popup-body">
              <label for="workflow-select">Choose a workflow:</label>
              <select id="workflow-select" class="form-control">
                <option value="">--Select a Workflow--</option>
                ${workflows
                  .map((workflow) => `<option value="${workflow._id}">${workflow.name || "Unnamed Workflow"}</option>`)
                  .join("")}
              </select>
            </div>
            <div class="modal-footer">
              <button type="button" id="cancel-import-btn" class="btn cancel-btn">Cancel</button>
              <button type="button" id="import-selected-btn" class="btn save-btn" disabled>Import Workflow</button>
            </div>
          </div>
        </div>
      `

        document.body.insertAdjacentHTML("beforeend", modalHTML)
        const popup = document.getElementById("import-workflow-modal")

        // Show the popup
        popup.style.display = "flex"

        // Add class to animate in
        setTimeout(() => {
          popup.querySelector(".popup-content").classList.add("show")
        }, 10)

        const importBtn = document.getElementById("import-selected-btn")
        const workflowSelect = document.getElementById("workflow-select")

        workflowSelect.addEventListener("change", () => {
          importBtn.disabled = !workflowSelect.value
        })

        const closeBtn = popup.querySelector(".close-btn")
        closeBtn.addEventListener("click", () => closePopup(popup))

        const cancelBtn = document.getElementById("cancel-import-btn")
        cancelBtn.addEventListener("click", () => closePopup(popup))

        // Close when clicking outside
        popup.addEventListener("click", (e) => {
          if (e.target === popup) {
            closePopup(popup)
          }
        })

        importBtn.addEventListener("click", async () => {
          const workflowId = workflowSelect.value
          if (!workflowId) return

          try {
            const originalText = importBtn.innerHTML
            importBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Importing...'
            importBtn.disabled = true

            // First, get the specific workflow by ID
            const workflowResponse = await fetch(`/get_workflows`, {
              method: "GET",
              headers: { "Content-Type": "application/json" },
            })

            const workflowData = await workflowResponse.json()

            if (!workflowResponse.ok) {
              alert("Failed to fetch workflows: " + workflowData.error)
              return
            }

            // Find the selected workflow in the response
            const selectedWorkflow = workflowData.workflows.find((w) => w._id === workflowId)

            if (!selectedWorkflow) {
              alert("Selected workflow not found")
              return
            }

            // Extract tasks from the selected workflow
            const tasks = selectedWorkflow.tasks

            if (!tasks || tasks.length === 0) {
              alert("No tasks found in this workflow")
              return
            }

            // Debug: Log the tasks to see their structure
            console.log("Tasks to import:", tasks)

            // Add tasks one by one using saveTask
            let addedCount = 0
            for (const task of tasks) {
              // Create a new task object with the required fields
              const taskData = {
                name: task.name || "Imported Task",
                description: task.description || "",
                episodeId: episodeId,
                // Use a default guest ID if none is provided
                guestId: task.guestId,
                // Copy other relevant fields
                status: task.status || "pending",
                priority: task.priority || "medium",
                dueDate: task.dueDate || "",
                assigneeName: task.assigneeName || "",
                dependencies: task.dependencies || [],
              }

              // Save the task
              await saveTask(taskData)
              addedCount++
            }

            if (addedCount > 0) {
              // Refresh tasks
              const tasksData = await fetchTasks()
              state.tasks = tasksData ? tasksData.filter((task) => task.episodeId === episodeId) : []

              renderTaskList()
              renderKanbanBoard()
              renderTimeline()
              updateProgressBar()

              alert(`Successfully imported ${addedCount} tasks from the workflow!`)
              closePopup(popup)
            } else {
              alert("No tasks were imported")
              importBtn.innerHTML = originalText
              importBtn.disabled = false
            }
          } catch (error) {
            console.error("Error importing workflow:", error)
            alert("Failed to import workflow: " + error.message)
            importBtn.innerHTML = '<i class="fas fa-file-import"></i> Import Workflow'
            importBtn.disabled = false
          }
        })
      })
      .catch((error) => {
        console.error("Error fetching workflows:", error)

        // Create a container for the popup if it doesn't exist
        let popupContainer = document.getElementById("popup-container")
        if (!popupContainer) {
          popupContainer = document.createElement("div")
          popupContainer.id = "popup-container"
          document.body.appendChild(popupContainer)
        }

        // Show error modal
        const modalHTML = `
        <div id="import-workflow-modal" class="popup">
          <div class="popup-content">
            <div class="modal-header">
              <h2>Import Workflow</h2>
              <button class="close-btn">&times;</button>
            </div>
            <div class="popup-body">
              <p class="error-message">Failed to fetch workflows. Please try again later.</p>
            </div>
            <div class="modal-footer">
              <button class="btn cancel-btn" id="close-error-btn">Close</button>
            </div>
          </div>
        </div>
      `

        // Add the popup HTML to the container
        popupContainer.innerHTML = modalHTML

        // Get the popup element
        const popup = document.getElementById("import-workflow-modal")

        // Show the popup
        popup.style.display = "flex"

        // Add class to animate in
        setTimeout(() => {
          popup.querySelector(".popup-content").classList.add("show")
        }, 10)

        // Close button event
        const closeBtn = popup.querySelector(".close-btn")
        closeBtn.addEventListener("click", () => closePopup(popup))

        // Close button in footer
        const closeErrorBtn = document.getElementById("close-error-btn")
        closeErrorBtn.addEventListener("click", () => closePopup(popup))

        // Close when clicking outside
        popup.addEventListener("click", (e) => {
          if (e.target === popup) {
            closePopup(popup)
          }
        })
      })
  }

  // Fix the saveWorkflow function to ensure the popup displays correctly
  function saveWorkflow() {
    if (!state.selectedEpisode) {
      alert("Please select an episode first")
      return
    }

    const episodeId = state.selectedEpisode._id || state.selectedEpisode.id

    const modalHTML = `
    <div id="save-workflow-modal" class="popup">
      <div class="popup-content">
        <div class="modal-header">
          <h2>Save Workflow</h2>
          <button class="close-btn">&times;</button>
        </div>
        <div class="popup-body">
          <div class="form-group">
            <label for="workflow-name">Workflow Name</label>
            <input type="text" id="workflow-name" class="form-control" value="Workflow for ${state.selectedEpisode.title || "Episode"}" required>
          </div>
          <div class="form-group">
            <label for="workflow-description">Description</label>
            <textarea id="workflow-description" class="form-control" placeholder="Describe this workflow..."></textarea>
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" id="save-as-template" checked>
              Save as reusable template
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" id="cancel-save-btn" class="btn cancel-btn">Cancel</button>
          <button type="button" id="save-workflow-btn" class="btn save-btn">Save Workflow</button>
        </div>
      </div>
    </div>
  `

    document.body.insertAdjacentHTML("beforeend", modalHTML)
    const popup = document.getElementById("save-workflow-modal")

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
    const cancelBtn = document.getElementById("cancel-save-btn")
    cancelBtn.addEventListener("click", () => {
      closePopup(popup)
    })

    // Close when clicking outside
    popup.addEventListener("click", (e) => {
      if (e.target === popup) {
        closePopup(popup)
      }
    })

    // Save workflow event
    document.getElementById("save-workflow-btn").addEventListener("click", async () => {
      const name = document.getElementById("workflow-name").value
      const description = document.getElementById("workflow-description").value
      const saveAsTemplate = document.getElementById("save-as-template").checked

      if (!name) {
        alert("Workflow name is required")
        return
      }

      try {
        const saveBtn = document.getElementById("save-workflow-btn")
        const originalText = saveBtn.innerHTML
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...'
        saveBtn.disabled = true

        // Get tasks for this episode
        const episodeTasks = state.tasks.filter((task) => task.episodeId === episodeId)

        if (episodeTasks.length === 0) {
          alert("No tasks found for this episode. Please add tasks before saving a workflow.")
          saveBtn.disabled = false
          saveBtn.innerHTML = originalText
          return
        }

        // Call the server to save the workflow
        const response = await fetch("/save_workflow", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: name,
            description: description,
            isTemplate: saveAsTemplate,
            tasks: episodeTasks,
            episodeId: episodeId,
          }),
        })

        const result = await response.json()

        if (response.ok) {
          closePopup(popup)
          alert("Workflow saved successfully!")

          // Add the new workflow to the state
          if (result.workflowId) {
            const newWorkflow = {
              _id: result.workflowId,
              name: name,
              description: description,
              tasks: episodeTasks,
              isTemplate: saveAsTemplate,
            }
            state.workflows.push(newWorkflow)

            // Update the workflow selector if we're on the workflow tab
            if (state.activeTab === "dependencies") {
              const workflowSelect = document.getElementById("workflow-select")
              if (workflowSelect) {
                const option = document.createElement("option")
                option.value = result.workflowId
                option.textContent = name
                workflowSelect.appendChild(option)
              }
            }
          }
        } else {
          throw new Error(result.error || "Failed to save workflow")
        }
      } catch (error) {
        console.error("Error saving workflow:", error)
      }
    })
  }
})
