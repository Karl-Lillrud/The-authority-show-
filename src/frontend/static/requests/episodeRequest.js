export async function fetchAllEpisodes() {
  try {
    const response = await fetch("/get_episodes")
    const data = await response.json()
    if (response.ok) {
      // This function returns an array of episode objects as provided by the backend.
      // Ensure the backend response for this endpoint includes episodes with:
      // title, description, image_url, audio_url, status, and other necessary fields.
      return data.episodes
    } else {
      console.error("Failed to fetch episodes:", data.error)
      throw new Error(data.error || "Failed to fetch episodes")
    }
  } catch (error) {
    console.error("Error fetching episodes:", error)
    throw error
  }
}

export async function fetchEpisode(episodeId) {
  try {
    const response = await fetch(`/get_episodes/${episodeId}`)
    const data = await response.json()
    if (response.ok) {
      // This function returns the episode object as provided by the backend.
      // Ensure the backend response for this endpoint includes:
      // title, description, image_url, audio_url, status, and other necessary fields.
      return data
    } else {
      console.error("Failed to fetch episode:", data.error)
      alert("Failed to fetch episode: " + data.error)
    }
  } catch (error) {
    console.error("Error fetching episode:", error)
    alert("Failed to fetch episode.")
  }
}

export async function fetchEpisodes(guestId) {
  try {
    const response = await fetch(`/episodes/get_episodes_by_guest/${guestId}`)
    const data = await response.json()

    if (response.ok) {
      return data.episodes
    } else {
      console.error("Failed to fetch episodes:", data.error)
      alert("Failed to fetch episodes: " + data.error)
    }
  } catch (error) {
    console.error("Error fetching episodes:", error)
    alert("Failed to fetch episodes.")
  }
}

export async function viewEpisodeTasks(episodeId) {
  try {
    const response = await fetch(`/episodes/view_tasks_by_episode/${episodeId}`)
    const data = await response.json()

    if (response.ok) {
      return data.tasks
    } else {
      console.error("Failed to fetch tasks:", data.error)
      alert("Failed to fetch tasks: " + data.error)
    }
  } catch (error) {
    console.error("Error fetching tasks:", error)
    alert("Failed to fetch tasks.")
  }
}

export async function addTasksToEpisode(episodeId, guestId, tasks) {
  try {
    const response = await fetch("/episodes/add_tasks_to_episode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tasks,
        episode_id: episodeId,
        guest_id: guestId,
      }),
    })

    const result = await response.json()
    if (response.ok) {
      alert("Tasks added to episode successfully!")
      return result
    } else {
      console.error("Error adding tasks to episode:", result.error)
      alert("Error: " + result.error)
    }
  } catch (error) {
    console.error("Error adding tasks to episode:", error)
    alert("Failed to add tasks to episode.")
  }
}

export async function fetchEpisodeCountByGuest(guestId) {
  try {
    const response = await fetch(`/episodes/count_by_guest/${guestId}`)
    const data = await response.json()

    if (response.ok) {
      return data.count
    } else {
      console.error("Failed to fetch episode count:", data.error)
      alert("Failed to fetch episode count: " + data.error)
    }
  } catch (error) {
    console.error("Error fetching episode count:", error)
    alert("Failed to fetch episode count.")
  }
}

export async function registerEpisode(episodeData) {
  console.log("[episodeRequest.js] Received episodeData for registration:", JSON.stringify(episodeData, null, 2))

  if (!episodeData.podcastId || !episodeData.title) {
    console.error(
      "[episodeRequest.js] Validation Error: Missing required fields. podcastId:",
      episodeData.podcastId,
      "title:",
      episodeData.title,
    )
    throw new Error("Missing required fields: podcastId or title")
  }

  try {
    const response = await fetch("/add_episode", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(episodeData),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        error: "Failed to register episode and parse error response.",
      }))
      console.error(
        "[episodeRequest.js] Error registering episode - Server responded with an error:",
        response.status,
        errorData,
      )
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    console.log("[episodeRequest.js] Episode registered successfully via API:", data)
    return data
  } catch (error) {
    console.error("[episodeRequest.js] Error in registerEpisode function:", error.message)
    throw error
  }
}

export async function fetchEpisodesByPodcast(podcastId) {
  try {
    const response = await fetch(`/episodes/by_podcast/${podcastId}`)
    const data = await response.json()
    console.log("Fetched episodes with additional fields:", data.episodes) // Log episodes
    if (response.ok) {
      return data.episodes
    } else {
      console.error("Failed to fetch episodes:", data.error)
      alert("Failed to fetch episodes: " + data.error)
    }
  } catch (error) {
    console.error("Error fetching episodes:", error)
    alert("Failed to fetch episodes.")
  }
}

export async function updateEpisode(episodeId, data) {
  const isFormData = data instanceof FormData // Check if data is FormData

  try {
    const response = await fetch(`/update_episodes/${episodeId}`, {
      method: "PUT",
      headers: {
        // Remove any manual 'Content-Type' setting here if 'isFormData' is true
        // Fetch will automatically set it correctly for FormData
        // Example: DO NOT include the line below if isFormData is true
        // 'Content-Type': isFormData ? undefined : 'application/json', // Let browser set for FormData
        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        // Add other necessary headers like Accept if needed
        Accept: "application/json", // It's good practice to specify what you accept back
      },
      // Send FormData directly, or stringify if it's a plain object
      body: isFormData ? data : JSON.stringify(data),
    })

    // Log request details for debugging
    console.log(`Updating episode ${episodeId}. Is FormData: ${isFormData}`)

    if (!response.ok) {
      let errorData
      try {
        errorData = await response.json() // Try to parse error response
        console.error("Update Episode Error Response:", errorData)
      } catch (e) {
        // If response is not JSON (e.g., plain text or HTML error page)
        errorData = { error: await response.text() }
        console.error("Update Episode Non-JSON Error Response:", errorData.error)
      }
      // Throw a more informative error
      throw new Error(errorData?.error || errorData?.message || `HTTP error! status: ${response.status}`)
    }

    // If response is OK, try to parse JSON, handle potential empty response for 200/204
    if (response.status === 204) {
      // No Content
      return { message: "Episode updated successfully (No Content)" }
    }

    const result = await response.json()
    console.log("Update Episode Success Response:", result)
    return result // Contains { message: "..." } or potentially updated episode data
  } catch (error) {
    console.error("Failed to update episode:", error.message || error)
    // Return an object with an error key for consistent handling in the calling function
    return { error: `Failed to update episode: ${error.message || error}` }
  }
}

export async function deleteEpisode(episodeId) {
  try {
    const response = await fetch(`/delete_episodes/${episodeId}`, {
      method: "DELETE",
    })

    const contentType = response.headers.get("content-type")
    if (contentType && contentType.indexOf("application/json") !== -1) {
      const result = await response.json()
      if (response.ok) {
        return result
      } else {
        console.error("Failed to delete episode:", result.error)
        alert("Failed to delete episode: " + result.error)
      }
    } else {
      console.error("Unexpected response format:", await response.text())
      alert("Failed to delete episode: Unexpected response format")
    }
  } catch (error) {
    console.error("Error deleting episode:", error)
    alert("Failed to delete episode.")
  }
}
