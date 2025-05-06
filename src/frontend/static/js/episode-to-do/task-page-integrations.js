/**
 * Integration file to connect the task page with the comment functionality
 */

import { renderTaskList, setupTaskInteractions } from "/static/js/episode-to-do/task-page.js"
import {
  renderTaskComments,
  showAddCommentModal,
  setupCommentInteractions,
} from "/static/js/episode-to-do/comment-utils.js"

/**
 * Enhanced version of renderTaskList that integrates comments
 * @param {Object} state - The application state
 * @param {Function} updateUI - Function to update the UI
 */
export function renderEnhancedTaskList(state, updateUI) {
  // Call the original renderTaskList function
  renderTaskList(state, updateUI)

  // Set up comment interactions
  setupCommentInteractions(state, updateUI)

  // Add event listeners for the "Add Comment" buttons
  document.querySelectorAll(".add-comment-btn").forEach((button) => {
    button.addEventListener("click", (e) => {
      e.stopPropagation() // Prevent task details from opening
      const taskId = button.getAttribute("data-task-id")
      showAddCommentModal(taskId, state, updateUI)
    })
  })

  // We'll handle comment loading in the toggleTaskExpansion function instead
  // This ensures the UI is responsive first before loading comments
}

/**
 * Initialize the task page with comment functionality
 * @param {Object} state - The application state
 * @param {Function} updateUI - Function to update the UI
 */
export function initTaskPageWithComments(state, updateUI) {
  // Override the original renderTaskComments function
  window.renderTaskComments = renderTaskComments

  // Use the enhanced task list renderer
  renderEnhancedTaskList(state, updateUI)

  // Set up task interactions (from the original file)
  setupTaskInteractions(state, updateUI)
}
