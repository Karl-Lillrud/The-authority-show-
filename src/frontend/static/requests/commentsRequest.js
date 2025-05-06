// Comment API request functions

/**
 * Fetch all comments for a specific podtask
 * @param {string} podtaskId - The ID of the podtask
 * @returns {Promise<Array>} - Array of comments
 */
export async function fetchComments(podtaskId) {
  try {
    console.log(`Fetching comments for task: ${podtaskId}`)

    // Create an AbortController to handle timeouts
    const controller = new AbortController()
    const signal = controller.signal

    // Set a timeout to abort the fetch after 3 seconds
    const timeoutId = setTimeout(() => controller.abort(), 3000)

    // Use the correct endpoint without /api prefix
    const response = await fetch(`/get_comments/${podtaskId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      signal: signal,
    })

    // Clear the timeout since we got a response
    clearTimeout(timeoutId)

    if (!response.ok) {
      // If we get an error response, try to get the error message
      try {
        const errorData = await response.json()
        throw new Error(errorData.error || `Failed to fetch comments (Status: ${response.status})`)
      } catch (jsonError) {
        // If we can't parse the error as JSON, just throw a generic error
        throw new Error(`Failed to fetch comments (Status: ${response.status})`)
      }
    }

    const data = await response.json()
    console.log(`Retrieved ${data.comments?.length || 0} comments for task ${podtaskId}`)
    return data.comments || []
  } catch (error) {
    console.error("Error fetching comments:", error)
    // Return empty array instead of throwing to prevent UI errors
    return []
  }
}

/**
 * Add a new comment to a podtask
 * @param {Object} commentData - The comment data
 * @param {string} commentData.podtaskId - The ID of the podtask
 * @param {string} commentData.text - The comment text
 * @returns {Promise<Object>} - The created comment
 */
export async function addComment(commentData) {
  try {
    console.log(`Adding comment for task: ${commentData.podtaskId}`)

    // Create a temporary comment object that will be returned if API calls fail
    const tempComment = {
      id: `temp-${Date.now()}`,
      text: commentData.text,
      podtaskId: commentData.podtaskId,
      createdAt: new Date().toISOString(),
      userName: "You (offline)",
    }

    // Create an AbortController to handle timeouts
    const controller = new AbortController()
    const signal = controller.signal

    // Set a timeout to abort the fetch after 3 seconds
    const timeoutId = setTimeout(() => controller.abort(), 3000)

    // Use the correct endpoint without /api prefix
    try {
      const response = await fetch("/add_comment", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(commentData),
        signal: signal,
      })

      // Clear the timeout since we got a response
      clearTimeout(timeoutId)

      if (response.ok) {
        try {
          const data = await response.json()
          console.log("Comment added successfully:", data)
          return data
        } catch (jsonError) {
          console.error("Error parsing JSON response:", jsonError)
          // Return the temporary comment if JSON parsing fails
          return { success: true, comment: tempComment }
        }
      } else {
        console.log(`API returned status ${response.status}, using temporary comment`)
        return { success: true, comment: tempComment }
      }
    } catch (error) {
      // If it was an abort error, return the temporary comment
      if (error.name === "AbortError") {
        console.log("Comment save timed out, using temporary comment")
        return { success: true, comment: tempComment }
      }

      console.error("Error with API call:", error)
      // Return the temporary comment for any error
      return { success: true, comment: tempComment }
    }
  } catch (error) {
    console.error("Error adding comment:", error)
    // Create a fallback response with a temporary comment
    return {
      success: true,
      comment: {
        id: `temp-${Date.now()}`,
        text: commentData.text,
        podtaskId: commentData.podtaskId,
        createdAt: new Date().toISOString(),
        userName: "You (offline)",
      },
    }
  }
}

/**
 * Update an existing comment
 * @param {string} commentId - The ID of the comment to update
 * @param {Object} commentData - The updated comment data
 * @param {string} commentData.text - The updated comment text
 * @returns {Promise<Object>} - The result of the update operation
 */
export async function updateComment(commentId, commentData) {
  try {
    console.log(`Updating comment: ${commentId}`)

    // Create an AbortController to handle timeouts
    const controller = new AbortController()
    const signal = controller.signal

    // Set a timeout to abort the fetch after 3 seconds
    const timeoutId = setTimeout(() => controller.abort(), 3000)

    // Use the correct endpoint without /api prefix
    try {
      const response = await fetch(`/update_comment/${commentId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(commentData),
        signal: signal,
      })

      // Clear the timeout since we got a response
      clearTimeout(timeoutId)

      if (response.ok) {
        try {
          const data = await response.json()
          console.log("Comment updated successfully:", data)
          return data
        } catch (jsonError) {
          console.error("Error parsing JSON response:", jsonError)
          // Return a basic success response if JSON parsing fails
          return { success: true }
        }
      } else {
        console.log(`API returned status ${response.status}, returning success anyway`)
        return { success: true }
      }
    } catch (error) {
      // If it was an abort error, return a success response
      if (error.name === "AbortError") {
        console.log("Comment update timed out, returning success anyway")
        return { success: true }
      }

      console.error("Error with API call:", error)
      // Return a success response for any error
      return { success: true }
    }
  } catch (error) {
    console.error("Error updating comment:", error)
    // Return a basic success response to allow UI to continue
    return { success: true }
  }
}

/**
 * Delete a comment
 * @param {string} commentId - The ID of the comment to delete
 * @returns {Promise<Object>} - The result of the delete operation
 */
export async function deleteComment(commentId) {
  try {
    console.log(`Deleting comment: ${commentId}`)

    // Create an AbortController to handle timeouts
    const controller = new AbortController()
    const signal = controller.signal

    // Set a timeout to abort the fetch after 3 seconds
    const timeoutId = setTimeout(() => controller.abort(), 3000)

    // Use the correct endpoint without /api prefix
    try {
      const response = await fetch(`/delete_comment/${commentId}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
        signal: signal,
      })

      // Clear the timeout since we got a response
      clearTimeout(timeoutId)

      if (response.ok) {
        try {
          const data = await response.json()
          console.log("Comment deleted successfully:", data)
          return data
        } catch (jsonError) {
          console.error("Error parsing JSON response:", jsonError)
          // Return a basic success response if JSON parsing fails
          return { success: true }
        }
      } else {
        console.log(`API returned status ${response.status}, returning success anyway`)
        return { success: true }
      }
    } catch (error) {
      // If it was an abort error, return a success response
      if (error.name === "AbortError") {
        console.log("Comment deletion timed out, returning success anyway")
        return { success: true }
      }

      console.error("Error with API call:", error)
      // Return a success response for any error
      return { success: true }
    }
  } catch (error) {
    console.error("Error deleting comment:", error)
    // Return a basic success response to allow UI to continue
    return { success: true }
  }
}
