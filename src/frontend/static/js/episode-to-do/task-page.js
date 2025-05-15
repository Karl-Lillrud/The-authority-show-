"use client"

import { fetchTasks, fetchTask, saveTask, updateTask, deleteTask } from "/static/requests/podtaskRequest.js"
// Import the getDependencyInfo utility
import { formatDueDate, closePopup, getDependencyInfo } from "/static/js/episode-to-do/utils.js"
import { renderTaskComments, showAddCommentModal } from "/static/js/episode-to-do/comment-utils.js"
import { showImportWorkflowModal, saveWorkflow } from "/static/js/episode-to-do/workflow-page.js"

// Task page functionality
export function renderTaskList(state, updateUI) {
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
          <i class="fas fa-download"></i> Add Task List
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
    addTaskBtn.addEventListener("click", () => showAddTaskModal(state, updateUI))
  }

  const importTasksBtn = document.getElementById("import-default-tasks")
  if (importTasksBtn) {
    importTasksBtn.addEventListener("click", () => showImportTasksModal(state, updateUI))
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

      // Determine if task is assigned to current user - with extra debugging
      let isAssignedToCurrentUser = false

      // Check assignee field (direct ID match)
      if (task.assignee && task.assignee.toString() === state.currentUser.id.toString()) {
        isAssignedToCurrentUser = true
      }
      // Check assigneeName field (contains email)
      else if (task.assigneeName && task.assigneeName.trim() !== "") {
        if (
          task.assigneeName === state.currentUser.email ||
          (state.currentUser.email && task.assigneeName.includes(state.currentUser.email))
        ) {
          isAssignedToCurrentUser = true
        }
      }
      // Check assignedAt field (contains email or name)
      else if (task.assignedAt && task.assignedAt.trim() !== "") {
        if (
          task.assignedAt === state.currentUser.email ||
          (state.currentUser.email && task.assignedAt.includes(state.currentUser.email)) ||
          task.assignedAt === state.currentUser.name ||
          task.assignedAt === state.currentUser.fullName ||
          task.assignedAt === state.currentUser.displayName
        ) {
          isAssignedToCurrentUser = true
        }
      }

      // Add debug logging for assignment checks
      if (task.assignee || task.assigneeName || task.assignedAt) {
        console.log(`Task ${task.name} assignment check:`, {
          taskId: task.id || task._id,
          taskAssignee: task.assignee,
          taskAssigneeName: task.assigneeName,
          taskAssignedAt: task.assignedAt,
          currentUserId: state.currentUser.id,
          currentUserEmail: state.currentUser.email,
          isAssigned: isAssignedToCurrentUser,
        })
      }

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
${isCompleted ? '<i class="fas fa-check" style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); font-size:0.75rem; pointer-events:none;"></i>' : ""}
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
            ${
              task.dependencies && task.dependencies.length > 0
                ? `
                <div class="task-dependencies-badge">
                  <i class="fas fa-link"></i>
                  <span>${task.dependencies.length} ${task.dependencies.length === 1 ? "dependency" : "dependencies"}</span>
                </div>
              `
                : ""
            }
          </div>
          <div class="task-actions">
            ${hasDependencyWarning ? '<i class="fas fa-exclamation-triangle text-warning" title="This task has incomplete dependencies"></i>' : ""}
            ${task.aiTool ? `<button class="task-action-btn workspace-redirect-btn" title="Open in ${task.aiTool} workspace" data-task-id="${task.id || task._id}" data-ai-tool="${task.aiTool}"><i class="fas fa-external-link-alt"></i></button>` : ""}
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
    saveWorkflowBtn.addEventListener("click", () => saveWorkflow(state, updateUI))
  }

  const importWorkflowBtn = document.getElementById("import-workflow")
  if (importWorkflowBtn) {
    importWorkflowBtn.addEventListener("click", () => showImportWorkflowModal(state, updateUI))
  }

  // Add event listeners for task interactions
  setupTaskInteractions(state, updateUI)
}

export function setupTaskInteractions(state, updateUI) {
  // Task checkbox toggle
  document.querySelectorAll(".task-checkbox").forEach((checkbox) => {
    checkbox.addEventListener("click", () => {
      const taskId = checkbox.getAttribute("data-task-id")
      toggleTaskCompletion(taskId, state, updateUI)
    })
  })

  // Task expand/collapse
  document.querySelectorAll(".task-expand").forEach((button) => {
    button.addEventListener("click", () => {
      const taskId = button.getAttribute("data-task-id")
      toggleTaskExpansion(taskId, state, updateUI)
    })
  })

  // Task name click to show details
  document.querySelectorAll(".task-name").forEach((taskName) => {
    taskName.addEventListener("click", () => {
      const taskItem = taskName.closest(".task-item")
      if (taskItem) {
        const taskId = taskItem.dataset.taskId
        showTaskDetailsModal(taskId, state, updateUI)
      }
    })
  })

  // Edit task buttons
  document.querySelectorAll(".edit-task-btn").forEach((button) => {
    if (!button.classList.contains("edit-task-listener")) {
      button.classList.add("edit-task-listener")
      button.addEventListener("click", (e) => {
        e.stopPropagation() // Prevent event bubbling
        const taskId = button.getAttribute("data-task-id")
        // Close the details modal if it's open
        const existingModal = document.getElementById("task-details-modal")
        if (existingModal) {
          existingModal.remove()
        }
        showEditTaskPopup(taskId, state, updateUI)
      })
    }
  })

  // Delete task buttons
  document.querySelectorAll(".delete-task-btn").forEach((button) => {
    button.addEventListener("click", () => {
      const taskId = button.getAttribute("data-task-id")
      confirmDeleteTask(taskId, state, updateUI)
    })
  })

  // Assign task buttons
  document.querySelectorAll(".assign-task-btn").forEach((button) => {
    button.addEventListener("click", () => {
      const taskId = button.getAttribute("data-task-id")
      toggleTaskAssignment(taskId, state, updateUI)
    })
  })

  // Add comment buttons
  document.querySelectorAll(".add-comment-btn").forEach((button) => {
    button.addEventListener("click", () => {
      const taskId = button.getAttribute("data-task-id")
      showAddCommentModal(taskId, state, updateUI)
    })
  })

  // Workspace redirect buttons
  document.querySelectorAll(".workspace-redirect-btn").forEach((button) => {
    button.addEventListener("click", (e) => {
      e.stopPropagation() // Prevent task details from opening
      const taskId = button.getAttribute("data-task-id")
      const aiTool = button.getAttribute("data-ai-tool")
      redirectToWorkspace(taskId, aiTool, state, updateUI)
    })
  })
}

export async function toggleTaskCompletion(taskId, state, updateUI) {
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
  updateUI()
}

// Modify the toggleTaskExpansion function to handle comment loading properly
export function toggleTaskExpansion(taskId, state, updateUI) {
  // First toggle the state
  state.expandedTasks[taskId] = !state.expandedTasks[taskId]

  // Update UI immediately to show the expansion
  updateUI()

  // If the task is now expanded, load comments after the UI has updated
  if (state.expandedTasks[taskId]) {
    const task = state.tasks.find((t) => t.id === taskId || t._id === taskId)
    if (task) {
      // Add a loading indicator to the comments section
      const commentsSection = document.querySelector(`.task-item[data-task-id="${taskId}"] .task-comments`)
      if (commentsSection) {
        commentsSection.innerHTML = `
          <h4 class="comments-title">Comments</h4>
          <div class="comments-loading">
            <i class="fas fa-spinner fa-spin"></i> Loading comments...
          </div>
        `
      }

      // Load comments asynchronously with a slight delay to ensure UI responsiveness
      setTimeout(() => {
        import("/static/js/episode-to-do/comment-utils.js")
          .then((module) => {
            module.loadTaskComments(taskId, state, updateUI)
          })
          .catch((error) => {
            console.error("Error loading comment utils:", error)
            // Update UI to show error state
            if (commentsSection) {
              commentsSection.innerHTML = `
              <h4 class="comments-title">Comments</h4>
              <p class="comments-error">Failed to load comments. Please try again.</p>
            `
            }
          })
      }, 300)
    }
  }
}

// Find the toggleTaskAssignment function and replace it with this improved version
export async function toggleTaskAssignment(taskId, state, updateUI) {
  // Find the task
  const task = state.tasks.find((t) => t.id === taskId || t._id === taskId)
  if (!task) return

  // Get the button that was clicked
  const button = document.querySelector(`.assign-task-btn[data-task-id="${taskId}"]`)
  if (!button) return

  try {
    // Show loading state on the button
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>'
    button.disabled = true

    // Check current assignment state
    const isCurrentlyAssigned =
      (task.assignee && task.assignee.toString() === state.currentUser.id.toString()) ||
      (task.assigneeName && task.assigneeName.trim() !== "") ||
      (task.assignedAt && task.assignedAt.trim() !== "")

    console.log("Current assignment state:", {
      taskId,
      isCurrentlyAssigned,
      assignee: task.assignee,
      assigneeName: task.assigneeName,
      assignedAt: task.assignedAt,
      currentUserId: state.currentUser.id,
    })

    let updateData = {}

    if (isCurrentlyAssigned) {
      // UNASSIGN: Set all assignment fields to empty strings
      updateData = {
        assignee: "",
        assigneeName: "",
        assignedAt: "",
      }
      console.log("Unassigning task:", taskId)
    } else {
      // ASSIGN: Get user info for assignment
      let userId = state.currentUser.id
      let displayName = state.currentUser.email || "Unknown User"

      try {
        const accountRequests = await import("/static/requests/accountRequests.js")
        if (accountRequests.fetchAccount && typeof accountRequests.fetchAccount === "function") {
          const accountData = await accountRequests.fetchAccount()
          const userData = accountData.account || accountData
          userId = userData._id || userData.id || state.currentUser.id
          displayName =
            userData.fullName ||
            userData.full_name ||
            userData.name ||
            userData.displayName ||
            userData.display_name ||
            userData.email ||
            state.currentUser.email ||
            "Unknown User"
        }
      } catch (error) {
        console.warn("Error fetching account data, using fallback data:", error)
      }

      updateData = {
        assignee: userId,
        assigneeName: displayName,
        assignedAt: displayName,
      }
      console.log("Assigning task to:", displayName)
    }

    // Update task in the database
    await updateTask(taskId, updateData)

    // Update local task object with the new data
    Object.assign(task, updateData)

    // Update button state based on new assignment status
    button.innerHTML = isCurrentlyAssigned ? '<i class="fas fa-user-plus"></i>' : '<i class="fas fa-user-minus"></i>'
    button.title = isCurrentlyAssigned ? "Assign to me" : "Unassign Task"
    button.disabled = false

    // Update UI to reflect changes
    updateUI()

    console.log("Task assignment updated successfully:", {
      taskId,
      newState: !isCurrentlyAssigned,
      task,
    })
  } catch (error) {
    console.error("Error updating task assignment:", error)
    alert("Failed to update task assignment. Please try again.")

    // Reset button state in case of error
    button.innerHTML =
      task.assignedAt && task.assignedAt.trim() !== ""
        ? '<i class="fas fa-user-minus"></i>'
        : '<i class="fas fa-user-plus"></i>'
    button.disabled = false
  }
}

export async function confirmDeleteTask(taskId, state, updateUI) {
  if (confirm("Are you sure you want to delete this task?")) {
    try {
      await deleteTask(taskId)
      // Refresh tasks
      const episodeId = state.selectedEpisode._id || state.selectedEpisode.id
      const tasksData = await fetchTasks()
      state.tasks = tasksData ? tasksData.filter((task) => task.episodeId === episodeId) : []

      updateUI()
    } catch (error) {
      console.error("Error deleting task:", error)
      alert("Failed to delete task. Please try again.")
    }
  }
}

export async function showEditTaskPopup(taskId, state, updateUI) {
  try {
    const response = await fetchTask(taskId)

    if (!response || !response[0] || !response[0].podtask) {
      console.error("Task not found:", taskId)
      return
    }

    const task = response[0].podtask
    console.log("Fetched task data:", task)

    const {
      name,
      description,
      status,
      dependencies = [],
      dueDate = "",
      assignee = null,
      assigneeName = "",
      aiTool = "",
    } = task

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
                <label for="edit-task-ai-tools">AI Tools</label>
                <select id="edit-task-ai-tools" class="form-control">
                  <option value="" ${!aiTool ? "selected" : ""}>None</option>
                  <option value="transcription" ${aiTool === "transcription" ? "selected" : ""}>Transcription</option>
                  <option value="audio-editing" ${aiTool === "audio-editing" ? "selected" : ""}>Audio Editing</option>
                  <option value="video-editing" ${aiTool === "video-editing" ? "selected" : ""}>Video Editing</option>
                </select>
                <small class="help-text">Select an AI tool to assist with this task</small>
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

      const dependenciesSelect = document.getElementById("edit-task-dependencies")
      const dependencyPreview = document.createElement("div")
      dependencyPreview.id = "edit-dependency-preview"
      dependencyPreview.className = "dependency-preview"
      document.querySelector(".dependencies-container").appendChild(dependencyPreview)

      if (dependenciesSelect && dependencyPreview) {
        dependenciesSelect.addEventListener("change", () => {
          updateDependencyPreview(dependenciesSelect, dependencyPreview, allTasks)
        })
        // Initialize preview
        updateDependencyPreview(dependenciesSelect, dependencyPreview, allTasks)
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
    let originalText
    saveBtn.addEventListener("click", async () => {
      const title = document.getElementById("edit-task-title").value
      const description = document.getElementById("edit-task-description").value
      const status = document.getElementById("edit-task-status").value
      const dueDate = document.getElementById("edit-task-due-date").value
      const aiTool = document.getElementById("edit-task-ai-tools").value

      // Get selected dependencies
      const dependenciesSelect = document.getElementById("edit-task-dependencies")
      const selectedDependencies = Array.from(dependenciesSelect.selectedOptions).map((option) => option.value)

      const taskData = {
        name: title,
        description,
        status,
        dueDate,
        dependencies: selectedDependencies,
        aiTool: aiTool,
      }

      try {
        originalText = saveBtn.innerHTML
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...'
        saveBtn.disabled = true

        await updateTask(taskId, taskData)
        closePopup(popup)

        // Refresh tasks
        const episodeId = state.selectedEpisode._id || state.selectedEpisode.id
        const tasksData = await fetchTasks()
        state.tasks = tasksData ? tasksData.filter((task) => task.episodeId === episodeId) : []

        updateUI()
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

export function showAddTaskModal(state, updateUI) {
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
              <label for="task-ai-tools">AI Tools</label>
              <select id="task-ai-tools" class="form-control">
                <option value="">None</option>
                <option value="transcription">Transcription</option>
                <option value="audio-editing">Audio Editing</option>
                <option value="video-editing">Video Editing</option>
              </select>
              <small class="help-text">Select an AI tool to assist with this task</small>
                <option value="audio-editing">Audio Editing</option>
                <option value="video-editing">Video Editing</option>
              </select>
              <small class="help-text">Select an AI tool to assist with this task</small>
            </div>
            <div class="form-group">
              <label for="task-dependencies">Dependencies</label>
              <div class="dependencies-container">
                <select id="task-dependencies" class="form-control" multiple ${allTasks.length === 0 ? "disabled" : ""}>
                  ${
                    allTasks.length > 0
                      ? allTasks.map((task) => `<option value="${task.id || task._id}">${task.name}</option>`).join("")
                      : "<option disabled>No tasks available for dependencies</option>"
                  }
                </select>
                <p class="help-text">Hold Ctrl/Cmd to select multiple tasks. This task will only be available when all selected tasks are completed.</p>
                <div class="dependency-preview" id="dependency-preview"></div>
                  }
                </select>
                <p class="help-text">Hold Ctrl/Cmd to select multiple tasks. This task will only be available when all selected tasks are completed.</p>
                <div class="dependency-preview" id="dependency-preview"></div>
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

    const dependenciesSelect = document.getElementById("task-dependencies")
    const dependencyPreview = document.getElementById("dependency-preview")
    if (dependenciesSelect && dependencyPreview) {
      dependenciesSelect.addEventListener("change", () => {
        updateDependencyPreview(dependenciesSelect, dependencyPreview, allTasks)
      })
      // Initialize preview
      updateDependencyPreview(dependenciesSelect, dependencyPreview, allTasks)
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
    const aiTool = document.getElementById("task-ai-tools").value

    // Get selected dependencies
    const dependenciesSelect = document.getElementById("task-dependencies")
    const selectedDependencies =
      dependenciesSelect && !dependenciesSelect.disabled
        ? Array.from(dependenciesSelect.selectedOptions).map((option) => option.value)
        : []

    // Check if this task has dependencies
    const hasDependencies = selectedDependencies && selectedDependencies.length > 0

    const taskData = {
      name: title,
      description,
      episodeId: episodeId,
      dueDate,
      dependencies: selectedDependencies,
      status: "not-started", // Default to not-started
      aiTool: aiTool, // Add the AI tool to the task data
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

      updateUI()
    } catch (error) {
      console.error("Error saving task:", error)
      // Reset button state
      saveBtn.innerHTML = originalText
      saveBtn.disabled = false
      alert("Failed to save task: " + (error.message || "Unknown error"))
    }
  })
}

export async function showImportTasksModal(state, updateUI) {
  if (!state.selectedEpisode) {
    alert("Please select an episode first")
    return
  }

  const episodeId = state.selectedEpisode._id || state.selectedEpisode.id

  try {
    // Fetch default tasks from your JSON file
    const { fetchLocalDefaultTasks } = await import("/static/requests/podtaskRequest.js")
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

        updateUI()
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

function updateDependencyPreview(selectElement, previewElement, tasks) {
  if (!selectElement || !previewElement) return

  const selectedOptions = Array.from(selectElement.selectedOptions)
  previewElement.innerHTML = ""

  if (selectedOptions.length === 0) {
    previewElement.innerHTML = '<p class="text-muted">No dependencies selected</p>'
    return
  }

  const ul = document.createElement("ul")
  ul.className = "dependency-preview-list"

  selectedOptions.forEach((option) => {
    const task = tasks.find((t) => (t.id || t._id) === option.value)
    if (!task) return

    const li = document.createElement("li")
    li.className = `dependency-preview-item ${task.status === "completed" ? "completed" : "pending"}`
    li.innerHTML = `
      <span class="dependency-status ${task.status === "completed" ? "completed" : "pending"}"></span>
      ${task.name}
      <span class="dependency-status-text">(${task.status === "completed" ? "Completed" : "Pending"})</span>
    `
    ul.appendChild(li)
  })

  previewElement.appendChild(ul)
}

export function showTaskDetailsModal(taskId, state, updateUI) {
  // Find the task
  const task = state.tasks.find((t) => t.id === taskId || t._id === taskId)
  if (!task) return

  // Get dependency information
  const dependencyInfo = getDependencyInfo(taskId, state.tasks)
  const { dependencyTasks, dependentTasks } = dependencyInfo

  const modalHTML = `
    <div id="task-details-modal" class="popup">
      <div class="popup-content">
        <div class="modal-header">
          <h2>${task.name}</h2>
          <button class="close-btn">&times;</button>
        </div>
        <div class="popup-body">
          <div class="task-details-section">
            <p class="task-description">${task.description || "No description available"}</p>
            
            <div class="task-meta-section">
              <div class="task-meta-item">
                <i class="fas fa-clock"></i>
                <span>Due: ${formatDueDate(task.dueDate) || "No due date"}</span>
              </div>
              <div class="task-meta-item">
                <i class="fas fa-user"></i>
                <span>Assigned to: ${task.assignedAt || task.assigneeName || "Unassigned"}</span>
              </div>
              <div class="task-meta-item">
                <i class="fas fa-tasks"></i>
                <span>Status: ${task.status || "Not started"}</span>
              </div>
              ${
                task.aiTool
                  ? `
              <div class="task-meta-item">
                <i class="fas fa-robot"></i>
                <span>AI Tool: ${task.aiTool.replace("-", " ").replace(/\b\w/g, (l) => l.toUpperCase())}</span>
              </div>
              `
                  : ""
              }
            </div>
            
            ${
              dependencyTasks.length > 0
                ? `
                <div class="task-dependencies-section">
                  <h4>Dependencies:</h4>
                  <ul class="task-dependency-list">
                    ${dependencyTasks
                      .map(
                        (depTask) => `
                      <li class="task-dependency-item">
                        <span class="dependency-status ${depTask.status === "completed" ? "completed" : "pending"}"></span>
                        ${depTask.name} <span class="dependency-status-text">(${
                          depTask.status === "completed" ? "Completed" : "Pending"
                        })</span>
                      </li>
                    `,
                      )
                      .join("")}
                  </ul>
                </div>
              `
                : ""
            }
            
            ${
              dependentTasks.length > 0
                ? `
                <div class="task-dependents-section">
                  <h4>Tasks that depend on this:</h4>
                  <ul class="task-dependency-list">
                    ${dependentTasks
                      .map(
                        (depTask) => `
                      <li class="task-dependency-item">
                        <span class="dependency-status ${depTask.status === "completed" ? "completed" : "pending"}"></span>
                        ${depTask.name} <span class="dependency-status-text">(${
                          depTask.status === "completed" ? "Completed" : "Pending"
                        })</span>
                      </li>
                    `,
                      )
                      .join("")}
                  </ul>
                </div>
              `
                : ""
            }
            
            ${
              task.comments && task.comments.length > 0
                ? `
                <div class="task-comments-section">
                  <h4>Comments (${task.comments.length}):</h4>
                  <div class="comments-list">
                    ${task.comments
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
                      .join("")}
                  </div>
                </div>
              `
                : `<div class="task-comments-section"><p>No comments yet</p></div>`
            }
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" id="edit-task-details-btn" class="btn btn-primary" data-task-id="${taskId}">
            <i class="fas fa-edit"></i> Edit Task
          </button>
          ${
            task.aiTool
              ? `
          <button type="button" id="open-workspace-btn" class="btn btn-primary" data-task-id="${taskId}" data-ai-tool="${task.aiTool}">
            <i class="fas fa-laptop"></i> Open in Workspace
          </button>
          `
              : ""
          }
          <button type="button" id="close-task-details-btn" class="btn cancel-btn">Close</button>
        </div>
      </div>
    </div>
  `

  document.body.insertAdjacentHTML("beforeend", modalHTML)
  const popup = document.getElementById("task-details-modal")

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

  // Close button in footer
  const closeDetailsBtn = document.getElementById("close-task-details-btn")
  closeDetailsBtn.addEventListener("click", () => {
    closePopup(popup)
  })

  // Workspace button event
  if (task.aiTool) {
    const workspaceBtn = document.getElementById("open-workspace-btn")
    workspaceBtn.addEventListener("click", () => {
      closePopup(popup)
      redirectToWorkspace(taskId, task.aiTool, state, updateUI)
    })
  }

  // Close when clicking outside
  popup.addEventListener("click", (e) => {
    if (e.target === popup) {
      closePopup(popup)
    }
  })
}

export async function updateTaskStatus(taskId, columnId, state, updateUI) {
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
      // Update with both status and dependencies to ensure dependencies are saved
      await updateTask(taskId, {
        status: newStatus,
        dependencies: task.dependencies || [],
      })
      console.log(`Task ${taskId} status updated to ${newStatus}`)

      // If task is completed, check if any other tasks depend on this one
      if (newStatus === "completed") {
        // Find tasks that depend on this task
        const dependentTasks = state.tasks.filter((t) => t.dependencies && t.dependencies.includes(taskId))

        if (dependentTasks.length > 0) {
          console.log(`${dependentTasks.length} tasks depend on the completed task`)
        }
      }
    } catch (error) {
      console.error("Error updating task status:", error)
    }
  }

  // Update UI
  updateUI()
}

export function redirectToWorkspace(taskId, aiTool, state, updateUI) {
  // First, switch to the workspace tab
  const workspaceTab = document.querySelector('.tab-btn[data-tab="workspace"]')
  if (workspaceTab) {
    workspaceTab.click()
  }

  // Then, select the appropriate AI tool tab based on the aiTool value
  setTimeout(() => {
    let tabName = "transcription" // default

    if (aiTool === "audio-editing") {
      tabName = "audio"
    } else if (aiTool === "video-editing") {
      tabName = "video"
    } else if (aiTool === "transcription") {
      tabName = "transcription"
    } else if (aiTool === "summary" || aiTool === "seo") {
      tabName = "transcription" // These likely work with the transcript
    }

    // Call the showTab function from layout.js
    if (window.showTab) {
      window.showTab(tabName)
    } else {
      // Fallback if the function isn't globally available
      const tabButton = document.querySelector(`.tab-btn[onclick="showTab('${tabName}')"]`)
      if (tabButton) {
        tabButton.click()
      }
    }

    // Optionally, you could also pass the task context to the workspace
    // This would require additional implementation in the workspace code
    if (window.setCurrentTask) {
      window.setCurrentTask(taskId)
    }
  }, 100) // Small delay to ensure the tab switch happens first
}
