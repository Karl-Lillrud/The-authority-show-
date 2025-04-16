document.addEventListener("DOMContentLoaded", () => {
  // State management
  const state = {
    activePodcast: podcasts[0],
    activeTemplate: templates[0],
    activeTab: "tasks",
    selectedEpisode: episodes.find((ep) => ep.podcastId === podcasts[0].id) || episodes[0],
    selectedTask: null,
    showTimeline: true,
    expandedTasks: {},
    completedTasks: {},
  }

  // Initialize the UI
  initUI()

  function initUI() {
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
    podcastSelector.innerHTML = ""

    podcasts.forEach((podcast) => {
      const item = document.createElement("div")
      item.className = `podcast-item ${podcast.id === state.activePodcast.id ? "active" : ""}`
      item.innerHTML = `
        <div class="podcast-header">
          <i class="fas fa-podcast"></i>
          <span class="podcast-name">${podcast.name}</span>
        </div>
        <div class="podcast-meta">${podcast.episodeCount} episodes • ${podcast.description}</div>
      `
      item.addEventListener("click", () => selectPodcast(podcast))
      podcastSelector.appendChild(item)
    })
  }

  function populateEpisodesList() {
    const episodesList = document.getElementById("episodesList")
    episodesList.innerHTML = ""

    // Filter episodes for the active podcast
    const podcastEpisodes = episodes.filter((ep) => ep.podcastId === state.activePodcast.id)

    podcastEpisodes.forEach((episode) => {
      const item = document.createElement("div")
      item.className = `episode-item ${episode.id === state.selectedEpisode.id ? "active" : ""}`
      item.innerHTML = `
        <span class="episode-number">#${episode.number}</span>
        <div class="episode-info">
          <div class="episode-name">${episode.title}</div>
          <div class="episode-date">${episode.recordingDate}</div>
        </div>
        <span class="episode-status ${episode.status}">${episode.status}</span>
      `
      item.addEventListener("click", () => selectEpisode(episode))
      episodesList.appendChild(item)
    })
  }

  function populateEpisodeDropdown() {
    const dropdown = document.getElementById("episodeDropdown")
    dropdown.innerHTML = ""

    // Filter episodes for the active podcast
    const podcastEpisodes = episodes.filter((ep) => ep.podcastId === state.activePodcast.id)

    podcastEpisodes.forEach((episode) => {
      const item = document.createElement("div")
      item.className = "dropdown-item"
      item.innerHTML = `<span class="font-medium">Episode ${episode.number}:</span> ${episode.title}`
      item.addEventListener("click", () => {
        selectEpisode(episode)
        toggleEpisodeDropdown()
      })
      dropdown.appendChild(item)
    })
  }

  function renderTaskList() {
    const taskList = document.getElementById("taskList")
    taskList.innerHTML = ""

    state.activeTemplate.tasks.forEach((task) => {
      const isCompleted = state.completedTasks[task.id] || task.status === "completed"
      const isExpanded = state.expandedTasks[task.id] || false

      const taskItem = document.createElement("div")
      taskItem.className = "task-item"
      taskItem.innerHTML = `
        <div class="task-header ${isCompleted ? "completed" : ""}">
          <div class="task-checkbox ${isCompleted ? "checked" : ""}" data-task-id="${task.id}">
            ${isCompleted ? '<i class="fas fa-check"></i>' : ""}
          </div>
          <button class="task-expand" data-task-id="${task.id}">
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
                  <span>${task.dueDate}</span>
                </div>
                <div class="task-meta-item">
                  <i class="fas fa-user"></i>
                  <span>${task.assignee}</span>
                </div>
                ${
                  task.dependencies.length > 0
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
            ${
              task.workspaceEnabled
                ? `
              <button class="btn-icon text-primary" data-workspace-task-id="${task.id}">
                <i class="fas fa-laptop"></i>
              </button>
            `
                : ""
            }
            <div class="dropdown">
              <button class="btn-icon dropdown-toggle">
                <i class="fas fa-ellipsis-h"></i>
              </button>
              <!-- Dropdown menu would go here -->
            </div>
          </div>
        </div>
        
        <div class="task-details ${isExpanded ? "expanded" : ""}">
          <p class="task-description">${task.description}</p>
          
          ${
            task.dependencies.length > 0
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
                <span>Due: ${task.dueDate}</span>
              </div>
              <div class="task-meta-item">
                <i class="fas fa-user"></i>
                <span>Assigned to: ${task.assignee}</span>
              </div>
            </div>
            
            <div class="task-footer-actions">
              <button class="btn btn-outline btn-sm">
                <i class="fas fa-comment"></i>
                <span>Comments (2)</span>
              </button>
              
              ${
                task.workspaceEnabled
                  ? `
                <button class="btn btn-outline btn-sm workspace-btn" data-workspace-task-id="${task.id}">
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

    // Add event listeners for task interactions
    setupTaskInteractions()
  }

  function renderKanbanBoard() {
    const kanbanBoard = document.getElementById("kanbanBoard")
    kanbanBoard.innerHTML = ""

    const columns = [
      { id: "todo", title: "To Do", color: "kanban-column-todo" },
      { id: "in-progress", title: "In Progress", color: "kanban-column-progress" },
      { id: "ready", title: "Ready for Publishing", color: "kanban-column-ready" },
      { id: "published", title: "Published", color: "kanban-column-published" },
    ]

    // Group tasks by status
    const tasksByStatus = {
      todo: state.activeTemplate.tasks.filter((task) => task.status === "not-started" || !task.status),
      "in-progress": state.activeTemplate.tasks.filter((task) => task.status === "in-progress"),
      ready: state.activeTemplate.tasks.filter((task) => task.status === "ready"),
      published: state.activeTemplate.tasks.filter((task) => task.status === "completed"),
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
          ${tasksByStatus[column.id]
            .map(
              (task) => `
            <div class="kanban-task" draggable="true" data-task-id="${task.id}">
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
                  <span>${task.dueDate}</span>
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
                  ${
                    task.assignee === "John Doe"
                      ? "JD"
                      : task.assignee === "Alice Smith"
                        ? "AS"
                        : task.assignee === "Bob Johnson"
                          ? "BJ"
                          : ""
                  }
                </div>
                ${
                  task.workspaceEnabled
                    ? `
                  <button class="btn-icon text-primary workspace-btn" data-workspace-task-id="${task.id}">
                    <i class="fas fa-laptop"></i>
                  </button>
                `
                    : ""
                }
              </div>
            </div>
          `,
            )
            .join("")}
        </div>
      `

      kanbanBoard.appendChild(columnDiv)
    })

    // Set up drag and drop for kanban tasks
    setupKanbanDragDrop()
  }

  function renderTimeline() {
    const timeline = document.getElementById("timeline")
    timeline.innerHTML = ""

    // Update timeline header dates
    document.getElementById("timelineRecordingDate").textContent = state.selectedEpisode.recordingDate
    document.getElementById("timelineReleaseDate").textContent = state.selectedEpisode.releaseDate

    // Group tasks by due date
    const tasksByDueDate = {}
    state.activeTemplate.tasks.forEach((task) => {
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
        document.getElementById(`${tabId}-tab`).classList.add("active")

        state.activeTab = tabId
      })
    })
  }

  function setupTimelineToggle() {
    const toggleBtn = document.getElementById("toggleTimelineBtn")
    const sidebar = document.getElementById("timelineSidebar")

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
    dropdown.classList.toggle("show")
  }

  function selectPodcast(podcast) {
    state.activePodcast = podcast

    // Find the first episode of this podcast
    const firstEpisode = episodes.find((ep) => ep.podcastId === podcast.id)
    if (firstEpisode) {
      state.selectedEpisode = firstEpisode
    }

    // Update UI
    populatePodcastSelector()
    populateEpisodesList()
    populateEpisodeDropdown()

    // Update episode display
    updateEpisodeDisplay()
  }

  function selectEpisode(episode) {
    state.selectedEpisode = episode

    // Update UI
    populateEpisodesList()
    updateEpisodeDisplay()
  }

  function updateEpisodeDisplay() {
    // Update header
    document.getElementById("currentEpisodeNumber").textContent = `Episode ${state.selectedEpisode.number}`
    document.getElementById("episodeTitle").textContent = state.selectedEpisode.title
    document.getElementById("recordingDate").textContent = `Recording Date: ${state.selectedEpisode.recordingDate}`

    // Update progress bar
    updateProgressBar()

    // Update timeline
    renderTimeline()
  }

  function updateProgressBar() {
    const { completedTasks, totalTasks } = state.selectedEpisode
    const percentage = Math.round((completedTasks / totalTasks) * 100)

    document.getElementById("progressText").textContent =
      `${completedTasks} of ${totalTasks} tasks completed (${percentage}%)`
    document.getElementById("progressBar").style.width = `${percentage}%`
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

    // Workspace buttons
    document.querySelectorAll(".workspace-btn, [data-workspace-task-id]").forEach((button) => {
      button.addEventListener("click", () => {
        const taskId = button.getAttribute("data-workspace-task-id")
        openTaskInWorkspace(taskId)
      })
    })
  }

  function toggleTaskCompletion(taskId) {
    state.completedTasks[taskId] = !state.completedTasks[taskId]
    renderTaskList()
    renderKanbanBoard()
    renderTimeline()
  }

  function toggleTaskExpansion(taskId) {
    state.expandedTasks[taskId] = !state.expandedTasks[taskId]
    renderTaskList()
  }

  function openTaskInWorkspace(taskId) {
    const task = state.activeTemplate.tasks.find((t) => t.id === taskId)
    if (task) {
      state.selectedTask = task

      // Switch to workspace tab
      document.querySelector('.tab-btn[data-tab="workspace"]').click()

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
        }
      })
    })
  }

  function updateTaskStatus(taskId, columnId) {
    const task = state.activeTemplate.tasks.find((t) => t.id === taskId)
    if (task) {
      switch (columnId) {
        case "todo":
          task.status = "not-started"
          break
        case "in-progress":
          task.status = "in-progress"
          break
        case "ready":
          task.status = "ready"
          break
        case "published":
          task.status = "completed"
          break
      }
    }
  }

  function renderWorkspace() {
    const workspaceArea = document.getElementById("workspaceArea")

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
                <h4 class="audio-title">Episode${state.selectedEpisode.number}_raw.mp3</h4>
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
                  <h4 class="audio-title">Episode${state.selectedEpisode.number}_final.mp3</h4>
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
          document.getElementById(`${tabId}-tab`).classList.add("active")
        })
      })
    }
  }

  function togglePlayback() {
    const playButton = document.getElementById("playButton")
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
    button.disabled = true
    button.textContent = "Processing..."

    // Simulate transcript generation
    setTimeout(() => {
      button.disabled = false
      button.textContent = "Generate Transcript"

      const textarea = document.querySelector(".transcript-editor")
      if (textarea) {
        textarea.value = `Host: Welcome to Episode ${state.selectedEpisode.number} of our podcast, where we discuss ${state.selectedEpisode.title}.\n\nGuest: Thanks for having me! I'm excited to share my thoughts on this topic.\n\nHost: Let's start by talking about the key points we outlined in our prep session...`
      }
    }, 2000)
  }
})

// Podcast data
const podcasts = [
  {
    id: "podcast-1",
    name: "Tech Talk Weekly",
    description: "Weekly discussions about the latest in technology",
    episodeCount: 42,
    coverImage: "tech-talk.jpg",
  },
  {
    id: "podcast-2",
    name: "Creative Minds",
    description: "Interviews with creative professionals",
    episodeCount: 28,
    coverImage: "creative-minds.jpg",
  },
  {
    id: "podcast-3",
    name: "Business Insights",
    description: "Strategies and insights for entrepreneurs",
    episodeCount: 15,
    coverImage: "business-insights.jpg",
  },
]

// Episode data
const episodes = [
  {
    id: "ep-42",
    podcastId: "podcast-1",
    number: 42,
    title: "The Future of Podcasting",
    recordingDate: "2025-05-01",
    releaseDate: "2025-05-08",
    completedTasks: 8,
    totalTasks: 15,
    status: "editing",
  },
  {
    id: "ep-41",
    podcastId: "podcast-1",
    number: 41,
    title: "Interview with Tech Innovator",
    recordingDate: "2025-04-24",
    releaseDate: "2025-05-01",
    completedTasks: 12,
    totalTasks: 15,
    status: "publishing",
  },
  {
    id: "ep-40",
    podcastId: "podcast-1",
    number: 40,
    title: "AI Revolution in Content Creation",
    recordingDate: "2025-04-17",
    releaseDate: "2025-04-24",
    completedTasks: 15,
    totalTasks: 15,
    status: "published",
  },
  {
    id: "ep-39",
    podcastId: "podcast-1",
    number: 39,
    title: "The Science of Sound Design",
    recordingDate: "2025-04-10",
    releaseDate: "2025-04-17",
    completedTasks: 15,
    totalTasks: 15,
    status: "published",
  },
  {
    id: "ep-43",
    podcastId: "podcast-1",
    number: 43,
    title: "Remote Recording Best Practices",
    recordingDate: "2025-05-08",
    releaseDate: "2025-05-15",
    completedTasks: 3,
    totalTasks: 15,
    status: "planning",
  },
  {
    id: "ep-44",
    podcastId: "podcast-1",
    number: 44,
    title: "Monetization Strategies for Podcasters",
    recordingDate: "2025-05-15",
    releaseDate: "2025-05-22",
    completedTasks: 1,
    totalTasks: 15,
    status: "planning",
  },
  {
    id: "ep-28",
    podcastId: "podcast-2",
    number: 28,
    title: "Interview with Award-Winning Designer",
    recordingDate: "2025-05-03",
    releaseDate: "2025-05-10",
    completedTasks: 6,
    totalTasks: 15,
    status: "editing",
  },
  {
    id: "ep-27",
    podcastId: "podcast-2",
    number: 27,
    title: "Creative Process Deep Dive",
    recordingDate: "2025-04-26",
    releaseDate: "2025-05-03",
    completedTasks: 14,
    totalTasks: 15,
    status: "publishing",
  },
  {
    id: "ep-15",
    podcastId: "podcast-3",
    number: 15,
    title: "Startup Funding Strategies",
    recordingDate: "2025-05-05",
    releaseDate: "2025-05-12",
    completedTasks: 5,
    totalTasks: 15,
    status: "editing",
  },
  {
    id: "ep-14",
    podcastId: "podcast-3",
    number: 14,
    title: "Marketing on a Budget",
    recordingDate: "2025-04-28",
    releaseDate: "2025-05-05",
    completedTasks: 13,
    totalTasks: 15,
    status: "publishing",
  },
]

// Template data
const templates = [
  {
    id: "default-template",
    name: "Default Podcast Template",
    description: "Standard workflow for podcast episodes",
    tasks: [
      {
        id: "task-1",
        name: "Schedule recording session",
        description: "Set up a time for recording the episode with the host and any guests.",
        dueDate: "7 days before recording",
        assignee: "Alice Smith",
        dependencies: [],
        isDependent: true,
        type: "planning",
        status: "completed",
      },
      {
        id: "task-2",
        name: "Prepare episode script/outline",
        description:
          "Create a detailed outline or script for the episode, including key talking points and questions for guests.",
        dueDate: "3 days before recording",
        assignee: "John Doe",
        dependencies: ["Schedule recording session"],
        hasDependencyWarning: true,
        type: "planning",
        status: "completed",
      },
      {
        id: "task-3",
        name: "Send prep materials to guest",
        description:
          "Share episode outline, technical requirements, and any other relevant information with the guest.",
        dueDate: "2 days before recording",
        assignee: "Alice Smith",
        dependencies: ["Prepare episode script/outline"],
        type: "planning",
        status: "completed",
      },
      {
        id: "task-4",
        name: "Test recording equipment",
        description: "Ensure all microphones, headphones, and recording software are working properly.",
        dueDate: "1 day before recording",
        assignee: "Bob Johnson",
        dependencies: [],
        type: "generic",
        status: "completed",
      },
      {
        id: "task-5",
        name: "Record episode",
        description: "Conduct the actual recording session with host and guest(s).",
        dueDate: "Recording day",
        assignee: "John Doe",
        dependencies: ["Test recording equipment", "Send prep materials to guest"],
        type: "generic",
        status: "completed",
      },
      {
        id: "task-6",
        name: "Edit audio",
        description: "Clean up audio, remove mistakes, and enhance sound quality.",
        dueDate: "2 days after recording",
        assignee: "Bob Johnson",
        dependencies: ["Record episode"],
        workspaceEnabled: true,
        type: "audio-editing",
        status: "in-progress",
      },
      {
        id: "task-7",
        name: "Generate transcript",
        description: "Create a text transcript of the episode for accessibility and SEO.",
        dueDate: "3 days after recording",
        assignee: "Bob Johnson",
        dependencies: ["Edit audio"],
        workspaceEnabled: true,
        type: "transcription",
        status: "not-started",
      },
      {
        id: "task-8",
        name: "Prepare show notes",
        description: "Write detailed show notes including timestamps, links, and key takeaways.",
        dueDate: "3 days after recording",
        assignee: "Alice Smith",
        dependencies: ["Generate transcript"],
        type: "generic",
        status: "not-started",
      },
      {
        id: "task-9",
        name: "Create promotional graphics",
        description: "Design social media graphics and episode artwork.",
        dueDate: "4 days after recording",
        assignee: "Alice Smith",
        dependencies: ["Edit audio"],
        type: "promotion",
        status: "not-started",
      },
      {
        id: "task-10",
        name: "Upload and schedule episode",
        description: "Upload the episode to podcast hosting platform and schedule for release.",
        dueDate: "5 days after recording",
        assignee: "Alice Smith",
        dependencies: ["Edit audio", "Prepare show notes"],
        type: "generic",
        status: "not-started",
      },
      {
        id: "task-11",
        name: "Publish episode",
        description: "Make the episode live on all podcast platforms.",
        dueDate: "7 days after recording",
        assignee: "Alice Smith",
        dependencies: ["Upload and schedule episode"],
        type: "generic",
        status: "not-started",
      },
      {
        id: "task-12",
        name: "Social media promotion",
        description: "Share the episode across all social media channels.",
        dueDate: "7 days after recording",
        assignee: "Alice Smith",
        dependencies: ["Publish episode", "Create promotional graphics"],
        type: "promotion",
        status: "not-started",
      },
      {
        id: "task-13",
        name: "Send thank you to guest",
        description: "Send a thank you note and the published episode link to the guest.",
        dueDate: "8 days after recording",
        assignee: "John Doe",
        dependencies: ["Publish episode"],
        type: "generic",
        status: "not-started",
      },
      {
        id: "task-14",
        name: "Analyze episode performance",
        description: "Review download statistics and listener feedback.",
        dueDate: "14 days after recording",
        assignee: "John Doe",
        dependencies: ["Publish episode"],
        type: "generic",
        status: "not-started",
      },
      {
        id: "task-15",
        name: "Plan next episode",
        description: "Begin planning the topic and potential guests for the next episode.",
        dueDate: "14 days after recording",
        assignee: "John Doe",
        dependencies: ["Analyze episode performance"],
        type: "planning",
        status: "not-started",
      },
    ],
  },
]
