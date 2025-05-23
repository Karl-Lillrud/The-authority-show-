"use client"

import { updateTask } from "/static/requests/podtaskRequest.js"
import { formatDueDate } from "/static/js/episode-to-do/utils.js"

// Kanban board functionality
export function renderKanbanBoard(state, updateUI) {
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
                          ${
                            task.dependencies && task.dependencies.length > 0
                              ? `<div class="task-meta-item task-dependencies">
        <i class="fas fa-link"></i>
        <span>${task.dependencies.length} ${task.dependencies.length === 1 ? "dependency" : "dependencies"}</span>
      </div>`
                              : ""
                          }
                        </div>
                        <div class="kanban-task-footer">
                          <div class="kanban-task-assignee ${task.assignee ? "assigned" : ""}">
                            ${task.assignedAt || task.assigneeName || "Unassigned"}
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
  setupKanbanDragDrop(state, updateUI)
}

export function setupKanbanDragDrop(state, updateUI) {
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
        updateTaskStatus(taskId, columnId, state, updateUI)
      }
    })
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
