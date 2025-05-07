/**
 * Utility functions for handling comments in the task page
 */

import { addComment, fetchComments, updateComment, deleteComment } from "/static/requests/commentsRequest.js"

/**
 * Renders the comments section for a task
 * @param {Object} task - The task object
 * @returns {string} HTML string for the comments section
 */
export function renderTaskComments(task) {
  // If the task has no comments array or it's empty
  if (!task || !task.comments || task.comments.length === 0) {
    return `
      <div class="task-comments">
        <h4 class="comments-title">Comments</h4>
        <p class="no-comments">No comments yet</p>
      </div>
    `
  }

  // Sort comments by creation date (newest first)
  const sortedComments = [...task.comments].sort((a, b) => {
    return new Date(b.createdAt) - new Date(a.createdAt)
  })

  const commentsHTML = sortedComments
    .map(
      (comment) => `
    <div class="comment-item" data-comment-id="${comment.id || comment._id}">
      <div class="comment-header">
        <span class="comment-author">${comment.userName || "Anonymous"}</span>
        <span class="comment-date">${new Date(comment.createdAt).toLocaleString()}</span>
        <div class="comment-actions">
          <button class="comment-edit-btn" title="Edit Comment">
            <i class="fas fa-edit"></i>
          </button>
          <button class="comment-delete-btn" title="Delete Comment">
            <i class="fas fa-trash"></i>
          </button>
        </div>
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

/**
 * Shows a modal for adding a comment to a task
 * @param {string} taskId - The ID of the task
 * @param {Object} state - The application state
 * @param {Function} updateUI - Function to update the UI
 */
export async function showAddCommentModal(taskId, state, updateUI) {
  // Find the task
  const task = state.tasks.find((t) => t.id === taskId || t._id === taskId)
  if (!task) return

  // First, remove any existing comment modals to prevent duplicates
  const existingModal = document.getElementById("add-comment-modal")
  if (existingModal) {
    existingModal.parentNode.removeChild(existingModal)
  }

  const modalHTML = `
    <div id="add-comment-modal" class="modal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Add Comment</h2>
          <button class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
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

  // Append the modal directly to the body
  document.body.insertAdjacentHTML("beforeend", modalHTML)

  // Get the modal element
  const modal = document.getElementById("add-comment-modal")

  // Show the modal
  setTimeout(() => {
    modal.classList.add("show")

    // Focus on the textarea
    const textarea = document.getElementById("comment-text")
    if (textarea) textarea.focus()
  }, 10)

  // Close button event
  const closeBtn = modal.querySelector(".close-btn")
  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      closeCommentModal(modal)
    })
  }

  // Cancel button event
  const cancelBtn = document.getElementById("cancel-comment-btn")
  if (cancelBtn) {
    cancelBtn.addEventListener("click", () => {
      closeCommentModal(modal)
    })
  }

  // Close when clicking outside the modal content
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      closeCommentModal(modal)
    }
  })

  // Save comment event
  const saveBtn = document.getElementById("save-comment-btn")
  if (saveBtn) {
    saveBtn.addEventListener("click", async () => {
      const commentText = document.getElementById("comment-text")?.value.trim()
      if (!commentText) return

      try {
        const originalText = saveBtn.innerHTML // Store original text
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...'
        saveBtn.disabled = true

        // Create comment data
        const commentData = {
          podtaskId: taskId,
          text: commentText,
        }

        try {
          // Create a timeout promise to prevent hanging
          const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error("Comment saving timed out")), 5000),
          )

          // Send to server with timeout
          const savePromise = addComment(commentData)
          const result = await Promise.race([savePromise, timeoutPromise])

          // If successful, update the task's comments
          if (result && result.comment) {
            // Initialize comments array if it doesn't exist
            task.comments = task.comments || []

            // Add the new comment to the task
            task.comments.push(result.comment)
          } else {
            // If the server API isn't working yet, create a temporary comment
            console.log("Server API not responding correctly, creating temporary comment")
            const tempComment = {
              id: Date.now().toString(),
              text: commentText,
              ownerId: state.currentUser.id,
              userName: state.currentUser.name,
              createdAt: new Date().toISOString(),
            }

            // Initialize comments array if it doesn't exist
            task.comments = task.comments || []

            // Add the temporary comment
            task.comments.push(tempComment)
          }
        } catch (error) {
          console.error("Error with server API, creating temporary comment:", error)

          // Create a temporary comment
          const tempComment = {
            id: Date.now().toString(),
            text: commentText,
            ownerId: state.currentUser.id,
            userName: state.currentUser.name,
            createdAt: new Date().toISOString(),
          }

          // Initialize comments array if it doesn't exist
          task.comments = task.comments || []

          // Add the temporary comment
          task.comments.push(tempComment)
        } finally {
          closeCommentModal(modal)
          updateUI()
        }
      } catch (error) {
        console.error("Error adding comment:", error)
        alert("Failed to add comment. Please try again.")

        if (saveBtn) {
          saveBtn.disabled = false
          saveBtn.innerHTML = "Add Comment"
        }
      }
    })
  }
}

/**
 * Close the comment modal with animation
 * @param {HTMLElement} modal - The modal element to close
 */
function closeCommentModal(modal) {
  if (!modal) return

  modal.classList.remove("show")

  // Remove the modal after animation completes
  setTimeout(() => {
    if (modal && modal.parentNode) {
      modal.parentNode.removeChild(modal)
    }
  }, 300)
}

/**
 * Shows a modal for editing a comment
 * @param {string} taskId - The ID of the task
 * @param {string} commentId - The ID of the comment
 * @param {Object} state - The application state
 * @param {Function} updateUI - Function to update the UI
 */
export async function showEditCommentModal(taskId, commentId, state, updateUI) {
  // Find the task and comment
  const task = state.tasks.find((t) => t.id === taskId || t._id === taskId)
  if (!task || !task.comments) return

  const comment = task.comments.find((c) => c.id === commentId || c._id === commentId)
  if (!comment) return

  // First, remove any existing edit comment modals
  const existingModal = document.getElementById("edit-comment-modal")
  if (existingModal) {
    existingModal.parentNode.removeChild(existingModal)
  }

  const modalHTML = `
    <div id="edit-comment-modal" class="modal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Edit Comment</h2>
          <button class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <form id="edit-comment-form">
            <input type="hidden" id="edit-comment-id" value="${commentId}">
            <input type="hidden" id="edit-comment-task-id" value="${taskId}">
            <div class="form-group">
              <label for="edit-comment-text">Comment</label>
              <textarea id="edit-comment-text" class="form-control" required>${comment.text}</textarea>
            </div>
          </form>
        </div>
        <div class="modal-footer">
          <button type="button" id="cancel-edit-comment-btn" class="btn cancel-btn">Cancel</button>
          <button type="button" id="update-comment-btn" class="btn save-btn">Update Comment</button>
        </div>
      </div>
    </div>
  `

  document.body.insertAdjacentHTML("beforeend", modalHTML)
  const modal = document.getElementById("edit-comment-modal")

  // Show the modal
  setTimeout(() => {
    modal.classList.add("show")

    // Focus on the textarea
    const textarea = document.getElementById("edit-comment-text")
    if (textarea) textarea.focus()
  }, 10)

  // Close button event
  const closeBtn = modal.querySelector(".close-btn")
  closeBtn.addEventListener("click", () => {
    closeCommentModal(modal)
  })

  // Cancel button event
  const cancelBtn = document.getElementById("cancel-edit-comment-btn")
  cancelBtn.addEventListener("click", () => {
    closeCommentModal(modal)
  })

  // Close when clicking outside
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      closeCommentModal(modal)
    }
  })

  // Update comment event
  document.getElementById("update-comment-btn").addEventListener("click", async () => {
    const commentText = document.getElementById("edit-comment-text").value.trim()
    if (!commentText) return

    try {
      const updateBtn = document.getElementById("update-comment-btn")
      const originalText = updateBtn.innerHTML // Store original text
      updateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...'
      updateBtn.disabled = true

      // Update comment data
      const commentData = {
        text: commentText,
      }

      try {
        // Send to server
        await updateComment(commentId, commentData)

        // Update the comment in the task
        comment.text = commentText
        comment.updatedAt = new Date().toISOString()

        closeCommentModal(modal)
        updateUI()
      } catch (error) {
        console.error("Error with server API, updating comment locally:", error)

        // Update the comment locally
        comment.text = commentText
        comment.updatedAt = new Date().toISOString()

        closeCommentModal(modal)
        updateUI()
      }
    } catch (error) {
      console.error("Error updating comment:", error)
      alert("Failed to update comment. Please try again.")

      const updateBtn = document.getElementById("update-comment-btn")
      if (updateBtn) {
        updateBtn.disabled = false
        updateBtn.innerHTML = "Update Comment"
      }
    }
  })
}

/**
 * Confirms and deletes a comment
 * @param {string} taskId - The ID of the task
 * @param {string} commentId - The ID of the comment
 * @param {Object} state - The application state
 * @param {Function} updateUI - Function to update the UI
 */
export async function confirmDeleteComment(taskId, commentId, state, updateUI) {
  if (confirm("Are you sure you want to delete this comment?")) {
    try {
      // Find the task
      const task = state.tasks.find((t) => t.id === taskId || t._id === taskId)
      if (!task || !task.comments) return

      try {
        // Delete from server
        await deleteComment(commentId)

        // Remove from task's comments array
        task.comments = task.comments.filter((c) => c.id !== commentId && c._id !== commentId)

        updateUI()
      } catch (error) {
        console.error("Error with server API, deleting comment locally:", error)

        // Remove from task's comments array locally
        task.comments = task.comments.filter((c) => c.id !== commentId && c._id !== commentId)

        updateUI()
      }
    } catch (error) {
      console.error("Error deleting comment:", error)
      alert("Failed to delete comment. Please try again.")
    }
  }
}

/**
 * Sets up event listeners for comment interactions
 * @param {Object} state - The application state
 * @param {Function} updateUI - Function to update the UI
 */
export function setupCommentInteractions(state, updateUI) {
  // Edit comment buttons
  document.querySelectorAll(".comment-edit-btn").forEach((button) => {
    button.addEventListener("click", (e) => {
      e.stopPropagation() // Prevent task details from opening
      const commentItem = button.closest(".comment-item")
      const taskItem = button.closest(".task-item")
      if (commentItem && taskItem) {
        const commentId = commentItem.dataset.commentId
        const taskId = taskItem.dataset.taskId
        showEditCommentModal(taskId, commentId, state, updateUI)
      }
    })
  })

  // Delete comment buttons
  document.querySelectorAll(".comment-delete-btn").forEach((button) => {
    button.addEventListener("click", (e) => {
      e.stopPropagation() // Prevent task details from opening
      const commentItem = button.closest(".comment-item")
      const taskItem = button.closest(".task-item")
      if (commentItem && taskItem) {
        const commentId = commentItem.dataset.commentId
        const taskId = taskItem.dataset.taskId
        confirmDeleteComment(taskId, commentId, state, updateUI)
      }
    })
  })
}

/**
 * Loads comments for a task from the server
 * @param {string} taskId - The ID of the task
 * @param {Object} state - The application state
 * @param {Function} updateUI - Function to update the UI
 */
export async function loadTaskComments(taskId, state, updateUI) {
  try {
    // Find the task
    const task = state.tasks.find((t) => t.id === taskId || t._id === taskId)
    if (!task) return

    // Initialize comments array if it doesn't exist
    if (!task.comments) {
      task.comments = []
    }

    // Set a timeout to prevent hanging
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error("Comment loading timed out")), 5000),
    )

    try {
      // Fetch comments from server with a timeout
      const fetchPromise = fetchComments(taskId)
      const comments = await Promise.race([fetchPromise, timeoutPromise])

      // If we got comments from the server, update the task
      if (comments && comments.length > 0) {
        task.comments = comments
      }
    } catch (error) {
      console.error("Error loading comments from server:", error)
      // We'll continue with the existing comments (empty or local)
    } finally {
      // Always update the UI, whether we got new comments or not
      updateUI()
    }
  } catch (error) {
    console.error("Error loading comments:", error)
    // Ensure UI is updated even on error
    updateUI()
  }
}
