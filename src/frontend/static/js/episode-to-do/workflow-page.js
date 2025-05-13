"use client"

import { deleteWorkflow } from "/static/requests/podtaskRequest.js"
import { formatDueDate, closePopup } from "/static/js/episode-to-do/utils.js"

// Workflow editor functionality
export function renderWorkflowEditor(state, updateUI) {
  const dependencyView = document.getElementById("dependencyView")
  if (!dependencyView) return

  dependencyView.innerHTML = ""

  // Create the workflow editor UI
  const workflowEditorHTML = `
    <div class="workflow-editor">
      
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
        loadWorkflowForEditing(workflowId, state, updateUI)
      }
    })
  }

  if (createWorkflowBtn) {
    createWorkflowBtn.addEventListener("click", () => {
      showCreateWorkflowModal(state, updateUI)
    })
  }

  if (saveChangesBtn) {
    saveChangesBtn.addEventListener("click", () => {
      saveWorkflowChanges(state, updateUI)
    })
  }

  // Add event listener for delete workflow button
  if (deleteWorkflowBtn) {
    deleteWorkflowBtn.addEventListener("click", () => {
      const workflowId = workflowSelect.value
      if (workflowId) {
        confirmDeleteWorkflow(workflowId, state, updateUI)
      }
    })
  }

  // Add event listener for add task button
  const addWorkflowTaskBtn = document.getElementById("add-workflow-task-btn")
  if (addWorkflowTaskBtn) {
    addWorkflowTaskBtn.addEventListener("click", () => {
      const workflowId = workflowSelect.value
      if (workflowId) {
        addTaskToWorkflow(workflowId, state, updateUI)
      }
    })
  }
}

export async function confirmDeleteWorkflow(workflowId, state, updateUI) {
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

export async function loadWorkflowForEditing(workflowId, state, updateUI) {
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
            ${
              task.dependencies && task.dependencies.length > 0
                ? `<div class="task-meta-item">
                <i class="fas fa-link"></i>
                <span>${task.dependencies.length} ${task.dependencies.length === 1 ? "dependency" : "dependencies"}</span>
              </div>`
                : ""
            }
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
          editWorkflowTask(workflowId, taskId, state, updateUI)
        })
      })

      document.querySelectorAll(".remove-workflow-task-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          const taskId = btn.getAttribute("data-task-id")
          removeTaskFromWorkflow(workflowId, taskId, state, updateUI)
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

export function editWorkflowTask(workflowId, taskId, state, updateUI) {
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

            <div class="form-group">
              <label for="edit-workflow-task-dependencies">Dependencies</label>
              <select id="edit-workflow-task-dependencies" class="form-control" multiple>
                ${workflow.tasks
                  .filter((t) => (t._id || t.id) !== taskId)
                  .map(
                    (t) =>
                      `<option value="${t._id || t.id}" ${task.dependencies && task.dependencies.includes(t._id || t.id) ? "selected" : ""}>${t.name}</option>`,
                  )
                  .join("")}
              </select>
              <small class="help-text">Hold Ctrl/Cmd to select multiple tasks. This task will only be available when all selected tasks are completed.</small>
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

    const dependenciesSelect = document.getElementById("edit-workflow-task-dependencies")
    const selectedDependencies = dependenciesSelect
      ? Array.from(dependenciesSelect.selectedOptions).map((option) => option.value)
      : []

    // Update the task in the workflow
    task.name = name
    task.description = description
    task.dueDate = dueDate
    task.assigneeName = assigneeName
    task.dependencies = selectedDependencies

    // Reload the workflow editor
    loadWorkflowForEditing(workflowId, state, updateUI)

    // Close the popup
    closePopup(popup)
  })
}

export function removeTaskFromWorkflow(workflowId, taskId, state, updateUI) {
  // Find the workflow
  const workflow = state.workflows.find((w) => w._id === workflowId)
  if (!workflow) return

  // Confirm removal
  if (confirm("Are you sure you want to remove this task from the workflow?")) {
    // Remove the task from the workflow
    workflow.tasks = workflow.tasks.filter((t) => (t._id || t.id) !== taskId)

    // Reload the workflow editor
    loadWorkflowForEditing(workflowId, state, updateUI)
  }
}

export function addTaskToWorkflow(workflowId, state, updateUI) {
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
    loadWorkflowForEditing(workflowId, state, updateUI)

    // Close the popup
    closePopup(popup)
  })
}

export async function saveWorkflowChanges(state, updateUI) {
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

export function showCreateWorkflowModal(state, updateUI) {
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
          loadWorkflowForEditing(result.workflowId, state, updateUI)
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

export function showImportWorkflowModal(state, updateUI) {
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
              dependencies: task.dependencies || [],
              aiTool: task.aiTool || "",
            }

            // Save the task
            await saveTask(taskData)
            addedCount++
          }

          if (addedCount > 0) {
            // Refresh tasks
            const tasksData = await fetchTasks()
            state.tasks = tasksData ? tasksData.filter((task) => task.episodeId === episodeId) : []

            updateUI()

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

export function saveWorkflow(state, updateUI) {
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