"use client"

// Helper function to format due date
export function formatDueDate(dueDate) {
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

// Helper function to close any popup with animation
export function closePopup(popup) {
  if (!popup) return

  const popupContent = popup.querySelector(".popup-content")
  if (!popupContent) {
    // If it's a modal with modal-content instead of popup-content
    const modalContent = popup.querySelector(".modal-content")
    if (modalContent) {
      popup.classList.remove("show")

      // Remove popup after animation completes
      setTimeout(() => {
        if (popup && popup.parentNode) {
          popup.parentNode.removeChild(popup)
        }
      }, 300)
      return
    }
  }

  popupContent.classList.remove("show")
  popupContent.classList.add("hide")

  // Remove popup after animation completes
  setTimeout(() => {
    if (popup && popup.parentNode) {
      popup.parentNode.removeChild(popup)
    }
  }, 300)
}

// Add this function to utils.js
export function getDependencyInfo(taskId, tasks) {
  // Find the task
  const task = tasks.find((t) => (t.id || t._id) === taskId)
  if (!task)
    return {
      task: null,
      directDependencies: [],
      dependencyTasks: [],
      allDependenciesCompleted: true,
      dependentTasks: [],
      hasDependencies: false,
      hasDependents: false,
    }

  // Get direct dependencies
  const directDependencies = task.dependencies || []

  // Map dependency IDs to task objects
  const dependencyTasks = directDependencies
    .map((depId) => {
      return tasks.find((t) => (t.id || t._id) === depId)
    })
    .filter(Boolean)

  // Check if all dependencies are completed
  const allDependenciesCompleted =
    dependencyTasks.length > 0 ? dependencyTasks.every((t) => t.status === "completed") : true

  // Find tasks that depend on this task
  const dependentTasks = tasks.filter((t) => t.dependencies && t.dependencies.includes(taskId || task._id || task.id))

  return {
    task,
    directDependencies,
    dependencyTasks,
    allDependenciesCompleted,
    dependentTasks,
    hasDependencies: directDependencies.length > 0,
    hasDependents: dependentTasks.length > 0,
  }
}
