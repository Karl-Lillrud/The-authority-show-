// Task Management functionality for podcast dashboard
import {
  fetchTasks,
  fetchTask,
  saveTask,
  updateTask,
  deleteTask,
  fetchLocalDefaultTasks,
  addDefaultTasksToEpisode
} from "/static/requests/podtaskRequest.js";

// Initialize task management for all episode cards
export function initEpisodeToDo() {
  const toggleButtons = document.querySelectorAll(".toggle-tasks");
  toggleButtons.forEach((button) => {
    button.addEventListener("click", handleToggleTasks);
  });
}

function handleToggleTasks(event) {
  const button = event.currentTarget;
  const card = button.closest(".episode-card");
  const tasksContainer = card.querySelector(".tasks-container");
  const episodeId = card.dataset.episodeId;

  if (tasksContainer.style.display === "none") {
    tasksContainer.style.display = "block";
    button.textContent = "-";
    loadTasksForEpisode(episodeId, tasksContainer);
  } else {
    tasksContainer.style.display = "none";
    button.textContent = "+";
  }
}

async function loadTasksForEpisode(episodeId, container) {
  try {
    if (!container) {
      console.error("Tasks container not found for episode:", episodeId);
      return;
    }

    container.innerHTML = "<p>Loading tasks...</p>";
    const tasks = await fetchTasks();

    const episodeTasks = tasks
      ? tasks.filter((task) => task.episodeId === episodeId)
      : [];
    renderTasksUI(episodeId, episodeTasks, container);
  } catch (error) {
    console.error("Error loading tasks:", error);
    if (container) {
      container.innerHTML =
        '<p class="error-message">Error loading tasks. Please try again.</p>';
    }
  }
}

// Render tasks UI
function renderTasksUI(episodeId, tasks, container) {
  const taskManagementHTML = `
    <div class="task-management">
      <div class="task-header">
        <h3>Tasks</h3>
        <div class="task-header-actions">
          <button class="btn import-tasks-btn" data-episode-id="${episodeId}">
            <i class="fas fa-upload"></i> Import
          </button>
          <button class="btn add-task-btn" data-episode-id="${episodeId}">
            <i class="fas fa-plus"></i> Add Task
          </button>
        </div>
      </div>
      <div class="task-list">
        ${
          tasks.length > 0
            ? renderTaskList(tasks)
            : '<p class="no-tasks">No tasks yet. Add a task or import default tasks.</p>'
        }
      </div>
      <!-- New Buttons for Save and Import Workflow -->
      <div class="workflow-actions">
        <button class="btn save-workflow-btn" data-episode-id="${episodeId}">
          <i class="fas fa-save"></i> Save Workflow
        </button>
        <button class="btn import-workflow-btn" data-episode-id="${episodeId}">
          <i class="fas fa-download"></i> Import Workflow
        </button>
      </div>
    </div>
  `;

  container.innerHTML = taskManagementHTML;

  // Add event listeners for save and import workflow
  const saveWorkflowBtn = container.querySelector(".save-workflow-btn");
  const importWorkflowBtn = container.querySelector(".import-workflow-btn");

  saveWorkflowBtn.addEventListener("click", () => saveWorkflow(episodeId));
  importWorkflowBtn.addEventListener("click", () => importWorkflow(episodeId));

  // Existing task actions (add, edit, delete tasks)
  const addTaskBtn = container.querySelector(".add-task-btn");
  addTaskBtn.addEventListener("click", () => showAddTaskPopup(episodeId));

  const importTasksBtn = container.querySelector(".import-tasks-btn");
  importTasksBtn.addEventListener("click", () =>
    showImportTasksPopup(episodeId)
  );

  // Add event listeners to task actions
  const taskItems = container.querySelectorAll(".task-item");
  taskItems.forEach((item) => {
    const taskId = item.dataset.taskId;
    if (taskId) {
      const checkbox = item.querySelector(".task-checkbox");
      checkbox.addEventListener("change", () =>
        toggleTaskCompletion(taskId, checkbox.checked)
      );

      const editBtn = item.querySelector(".edit-task-btn");
      editBtn.addEventListener("click", () => showEditTaskPopup(taskId));

      const deleteBtn = item.querySelector(".delete-task-btn");
      deleteBtn.addEventListener("click", () => confirmDeleteTask(taskId));
    }
  });
}

// Save workflow function
async function saveWorkflow(episodeId) {
  try {
    const response = await fetch("/get_podtasks", {
      method: "GET",
      headers: { "Content-Type": "application/json" }
    });
    const data = await response.json();

    const tasks = data.podtasks.filter((task) => task.episodeId === episodeId);

    if (tasks.length === 0) {
      return alert("No tasks found for this episode.");
    }

    const saveResponse = await fetch("/save_workflow", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ episode_id: episodeId, tasks: tasks })
    });

    const saveData = await saveResponse.json();
    if (saveResponse.ok) {
      alert("Workflow saved successfully!");
    } else {
      alert("Failed to save workflow: " + saveData.error);
    }
  } catch (error) {
    console.error("Error saving workflow:", error);
    alert("Failed to save workflow.");
  }
}

// Import workflow function with dropdown
async function importWorkflow(episodeId) {
  try {
    const response = await fetch(`/get_workflows`, {
      method: "GET",
      headers: { "Content-Type": "application/json" }
    });

    const data = await response.json();
    if (response.ok && data.workflows.length > 0) {
      // Show a modal with a dropdown list of workflows
      showImportWorkflowModal(episodeId, data.workflows);
    } else {
      alert("No workflows available to import.");
    }
  } catch (error) {
    console.error("Error fetching workflows:", error);
    alert("Failed to fetch workflows.");
  }
}

function showImportWorkflowModal(episodeId, workflows) {
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
              .map(
                (workflow) =>
                  `<option value="${workflow._id}">${
                    workflow.name || "Unnamed Workflow"
                  }</option>`
              )
              .join("")}
          </select>
        </div>
        <div class="modal-footer">
          <button type="button" id="cancel-import-btn" class="btn cancel-btn">Cancel</button>
          <button type="button" id="import-selected-btn" class="btn save-btn" disabled>Import Workflow</button>
        </div>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML("beforeend", modalHTML);

  // Force modal to display
  const modal = document.getElementById("import-workflow-modal");
  modal.style.display = "flex"; // Make sure it's visible

  const importBtn = document.getElementById("import-selected-btn");
  const workflowSelect = document.getElementById("workflow-select");

  workflowSelect.addEventListener("change", () => {
    importBtn.disabled = !workflowSelect.value;
  });

  const closeBtn = modal.querySelector(".close-btn");
  closeBtn.addEventListener("click", () => closeModal(modal));

  const cancelBtn = document.getElementById("cancel-import-btn");
  cancelBtn.addEventListener("click", () => closeModal(modal));

  importBtn.addEventListener("click", async () => {
    const workflowId = workflowSelect.value;
    if (!workflowId) return;

    try {
      // First, get the specific workflow by ID
      const workflowResponse = await fetch(`/get_workflows`, {
        method: "GET",
        headers: { "Content-Type": "application/json" }
      });

      const workflowData = await workflowResponse.json();

      if (!workflowResponse.ok) {
        alert("Failed to fetch workflows: " + workflowData.error);
        return;
      }

      // Find the selected workflow in the response
      const selectedWorkflow = workflowData.workflows.find(
        (w) => w._id === workflowId
      );

      if (!selectedWorkflow) {
        alert("Selected workflow not found");
        return;
      }

      // Extract tasks from the selected workflow
      const tasks = selectedWorkflow.tasks;

      if (!tasks || tasks.length === 0) {
        alert("No tasks found in this workflow");
        return;
      }

      // Debug: Log the tasks to see their structure
      console.log("Tasks to import:", tasks);

      // Instead of using add_tasks_to_episode, let's add tasks one by one using saveTask
      let addedCount = 0;
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
          priority: task.priority || "medium"
        };

        // Save the task
        await saveTask(taskData);
        addedCount++;
      }

      if (addedCount > 0) {
        // Reload the tasks after successful import
        const tasksContainer = document.querySelector(
          `.episode-card[data-episode-id="${episodeId}"] .tasks-container`
        );
        loadTasksForEpisode(episodeId, tasksContainer);

        alert(`Successfully imported ${addedCount} tasks from the workflow!`);
        closeModal(modal);
      } else {
        alert("No tasks were imported");
      }
    } catch (error) {
      console.error("Error importing workflow:", error);
      alert("Failed to import workflow: " + error.message);
    }
  });
} // Added missing closing brace here

function closeModal(modal) {
  modal.style.display = "none"; // Make sure to hide it
  setTimeout(() => modal.remove(), 300); // Remove after animation
}

// Render task list
function renderTaskList(tasks) {
  return tasks
    .map(
      (task) => `
      <div class="task-item ${
        task.completed ? "task-completed" : ""
      }" data-task-id="${task._id || task.id}">
        <input type="checkbox" class="task-checkbox" ${
          task.completed ? "checked" : ""
        }>
        <div class="task-content">
          <div class="task-title">${task.name}</div>
          ${
            task.description
              ? `<div class="task-description">${task.description}</div>`
              : ""
          }
        </div>
        <div class="task-actions">
          <button class="task-action-btn edit-task-btn" title="Edit Task"><i class="fas fa-edit"></i> Edit</button>
          <button class="task-action-btn delete-task-btn" title="Delete Task"><i class="fas fa-trash"></i> Delete</button>
        </div>
      </div>
    `
    )
    .join("");
}

// Additional task management functions like addTask, editTask, etc., stay the same...

// Show add task popup
function showAddTaskPopup(episodeId) {
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
  `;

  document.body.insertAdjacentHTML("beforeend", popupHTML);
  const popup = document.getElementById("task-popup");

  // Show the popup
  popup.style.display = "flex";

  // Add class to animate in
  setTimeout(() => {
    popup.querySelector(".popup-content").classList.add("show");
  }, 10);

  // Close button event
  const closeBtn = popup.querySelector(".close-btn");
  closeBtn.addEventListener("click", () => {
    closePopup(popup);
  });

  // Cancel button event
  const cancelBtn = document.getElementById("cancel-add-btn");
  cancelBtn.addEventListener("click", () => {
    closePopup(popup);
  });

  // Close when clicking outside
  popup.addEventListener("click", (e) => {
    if (e.target === popup) {
      closePopup(popup);
    }
  });

  // Form submission
  const form = document.getElementById("task-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("task-title").value;
    const description = document.getElementById("task-description").value;

    const taskData = {
      name: title,
      description,
      episodeId: episodeId
    };

    try {
      // Show loading state
      const saveBtn = form.querySelector(".save-btn");
      const originalText = saveBtn.innerHTML;
      saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
      saveBtn.disabled = true;

      await saveTask(taskData);
      closePopup(popup);
      const tasksContainer = document.querySelector(
        `.episode-card[data-episode-id="${episodeId}"] .tasks-container`
      );
      loadTasksForEpisode(episodeId, tasksContainer);
    } catch (error) {
      console.error("Error saving task:", error);
      // Reset button state
      const saveBtn = form.querySelector(".save-btn");
      saveBtn.innerHTML = originalText;
      saveBtn.disabled = false;
    }
  });
}

// FIXED: Show edit task popup with proper animation and visibility
// Show edit task popup with proper animation and visibility
async function showEditTaskPopup(taskId) {
  const response = await fetchTask(taskId); // Ensure this fetches the full task object

  if (!response || !response[0].podtask) {
    console.error("Task not found:", taskId);
    return;
  }

  const task = response[0].podtask; // Access the podtask data

  // Log the fetched task to inspect its structure
  console.log("Fetched task data:", task);

  const { name, description, guestId, status } = task; // Destructure the required fields directly from the task

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
              <input type="text" id="edit-task-title" class="form-control" value="${
                name || ""
              }" required>
            </div>
            <div class="form-group">
              <label for="edit-task-description">Description</label>
              <textarea id="edit-task-description" class="form-control">${
                description || ""
              }</textarea>
            </div>
            <div class="form-group">
              <label for="edit-task-status">Status</label>
              <select id="edit-task-status" class="form-control">
                <option value="incomplete" ${
                  status === "incomplete" ? "selected" : ""
                }>Incomplete</option>
                <option value="completed" ${
                  status === "completed" ? "selected" : ""
                }>Completed</option>
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
  `;

  document.body.insertAdjacentHTML("beforeend", modalHTML);

  const modal = document.getElementById("edit-task-modal");
  modal.style.display = "flex";

  setTimeout(() => {
    modal.querySelector(".popup-content").classList.add("show");
  }, 10);

  const closeBtn = modal.querySelector(".close-btn");
  closeBtn.addEventListener("click", () => closeEditModal(modal));

  const cancelBtn = document.getElementById("cancel-edit-btn");
  cancelBtn.addEventListener("click", () => closeEditModal(modal));

  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      closeEditModal(modal);
    }
  });

  const form = document.getElementById("edit-task-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const title = document.getElementById("edit-task-title").value;
    const description = document.getElementById("edit-task-description").value;
    const status = document.getElementById("edit-task-status").value;

    const taskData = {
      name: title,
      description,
      status: status
    };

    try {
      const saveBtn = form.querySelector(".save-btn");
      const originalText = saveBtn.innerHTML;
      saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
      saveBtn.disabled = true;

      await updateTask(taskId, taskData);

      closeEditModal(modal);

      // Refresh task list after update
      const taskItem = document.querySelector(
        `.task-item[data-task-id="${taskId}"]`
      );
      const tasksContainer = taskItem.closest(".tasks-container");
      const episodeCard = tasksContainer.closest(".episode-card");
      const episodeId = episodeCard.dataset.episodeId;
      loadTasksForEpisode(episodeId, tasksContainer);
    } catch (error) {
      console.error("Error updating task:", error);
      const saveBtn = form.querySelector(".save-btn");
      saveBtn.innerHTML = originalText;
      saveBtn.disabled = false;
    }
  });
}

// Helper function to close the edit modal with animation
function closeEditModal(modal) {
  const modalContent = modal.querySelector(".popup-content");
  modalContent.classList.remove("show");
  modalContent.classList.add("hide");

  // Remove modal after animation completes
  setTimeout(() => {
    modal.remove();
  }, 300);
}

// Helper function to close any popup with animation
function closePopup(popup) {
  const popupContent = popup.querySelector(".popup-content");
  popupContent.classList.remove("show");
  popupContent.classList.add("hide");

  // Remove popup after animation completes
  setTimeout(() => {
    popup.remove();
  }, 300);
}

// Show import tasks popup
async function showImportTasksPopup(episodeId) {
  try {
    // Fetch default tasks from your JSON file
    const defaultTasks = await fetchLocalDefaultTasks();

    const popupHTML = `
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
                </div>
              `
                )
                .join("")}
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
      </div>
    `;

    document.body.insertAdjacentHTML("beforeend", popupHTML);

    const popup = document.getElementById("import-tasks-popup");
    popup.style.display = "flex";

    // Add animation
    setTimeout(() => {
      popup.querySelector(".popup-content").classList.add("show");
    }, 10);

    // Close button event
    const closeBtn = popup.querySelector(".close-btn");
    closeBtn.addEventListener("click", () => {
      closePopup(popup);
    });

    // Cancel button event
    const cancelBtn = document.getElementById("cancel-import-btn");
    cancelBtn.addEventListener("click", () => {
      closePopup(popup);
    });

    // Close when clicking outside
    popup.addEventListener("click", (e) => {
      if (e.target === popup) {
        closePopup(popup);
      }
    });

    const checkboxes = popup.querySelectorAll(".import-task-checkbox");
    const selectedCountEl = popup.querySelector(".selected-count");
    const importBtn = document.getElementById("import-selected-btn");

    checkboxes.forEach((checkbox) => {
      checkbox.addEventListener("change", () => {
        const selectedCount = [...checkboxes].filter((cb) => cb.checked).length;
        selectedCountEl.textContent = `${selectedCount} selected`;
        importBtn.disabled = selectedCount === 0;
      });
    });

    importBtn.addEventListener("click", async () => {
      // Get selected tasks as an array of strings
      const selectedTasks = [...checkboxes]
        .filter((cb) => cb.checked)
        .map((cb) => cb.value);

      try {
        // Show loading state
        const originalText = importBtn.innerHTML;
        importBtn.innerHTML =
          '<i class="fas fa-spinner fa-spin"></i> Importing...';
        importBtn.disabled = true;

        await addDefaultTasksToEpisode(episodeId, selectedTasks);
        closePopup(popup);
        const tasksContainer = document.querySelector(
          `.episode-card[data-episode-id="${episodeId}"] .tasks-container`
        );
        loadTasksForEpisode(episodeId, tasksContainer);
      } catch (error) {
        console.error("Error importing default tasks:", error);
        // Reset button state
        importBtn.innerHTML = originalText;
        importBtn.disabled = false;
      }
    });
  } catch (error) {
    console.error("Error fetching default tasks:", error);
  }
}

// Toggle task completion
// Toggle task completion
async function toggleTaskCompletion(taskId, completed) {
  try {
    // Update task completion status on the server
    const updatedTask = await updateTask(taskId, {
      status: completed ? "completed" : "incomplete"
    });

    // Update the UI to reflect the new completion status
    const taskItem = document.querySelector(
      `.task-item[data-task-id="${taskId}"]`
    );
    const checkbox = taskItem.querySelector(".task-checkbox");

    // Update the class and checkbox state based on completion status
    if (completed) {
      taskItem.classList.add("task-completed");
      checkbox.checked = true;
    } else {
      taskItem.classList.remove("task-completed");
      checkbox.checked = false;
    }
  } catch (error) {
    console.error("Error updating task completion:", error);
  }
}

// Confirm delete task
function confirmDeleteTask(taskId) {
  if (!taskId) {
    console.error("Cannot delete task: Task ID is undefined");
    alert("Error: Cannot delete this task. Task ID is missing.");
    return;
  }

  const confirmPopupHTML = `
    <div id="confirm-delete-popup" class="popup">
      <div class="popup-content" style="max-width: 400px;">
        <div class="modal-header">
          <h2>Delete Task</h2>
          <button class="close-btn">&times;</button>
        </div>
        <div class="popup-body">
          <p>Are you sure you want to delete this task?</p>
          <p style="font-size: 0.9rem; color: #999;">This action cannot be undone.</p>
          <div class="modal-footer">
            <button id="cancel-delete-btn" class="btn cancel-btn">Cancel</button>
            <button id="confirm-delete-btn" class="btn save-btn" style="background-color: #ff3b30;">Delete</button>
          </div>
        </div>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML("beforeend", confirmPopupHTML);
  const popup = document.getElementById("confirm-delete-popup");
  popup.style.display = "flex";

  // Add animation
  setTimeout(() => {
    popup.querySelector(".popup-content").classList.add("show");
  }, 10);

  // Close button event
  const closeBtn = popup.querySelector(".close-btn");
  closeBtn.addEventListener("click", () => {
    closePopup(popup);
  });

  // Cancel button event
  const cancelBtn = document.getElementById("cancel-delete-btn");
  cancelBtn.addEventListener("click", () => {
    closePopup(popup);
  });

  // Close when clicking outside
  popup.addEventListener("click", (e) => {
    if (e.target === popup) {
      closePopup(popup);
    }
  });

  // Confirm button event
  const confirmBtn = document.getElementById("confirm-delete-btn");
  confirmBtn.addEventListener("click", async () => {
    try {
      // Show loading state
      const originalText = confirmBtn.innerHTML;
      confirmBtn.innerHTML =
        '<i class="fas fa-spinner fa-spin"></i> Deleting...';
      confirmBtn.disabled = true;

      // Get episode ID before deleting
      const taskItem = document.querySelector(
        `.task-item[data-task-id="${taskId}"]`
      );
      const tasksContainer = taskItem.closest(".tasks-container");
      const episodeCard = tasksContainer.closest(".episode-card");
      const episodeId = episodeCard.dataset.episodeId;

      // Delete task
      await deleteTask(taskId);
      closePopup(popup);

      // Reload tasks
      loadTasksForEpisode(episodeId, tasksContainer);
    } catch (error) {
      console.error("Error deleting task:", error);
      // Reset button state if there's an error
      confirmBtn.innerHTML = originalText;
      confirmBtn.disabled = false;
    }
  });
}
