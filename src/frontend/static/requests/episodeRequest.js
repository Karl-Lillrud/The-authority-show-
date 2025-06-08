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
    const urlParams = new URLSearchParams(window.location.search);
    const tokenFromUrl = urlParams.get("token");
    const accessToken = localStorage.getItem("access_token");

    const headers = {
      "Content-Type": "application/json",
    };

    if (tokenFromUrl) {
      headers["Authorization"] = `Bearer ${tokenFromUrl}`;
    } else if (accessToken) {
      headers["Authorization"] = `Bearer ${accessToken}`;
    }

    const response = await fetch(`/get_episodes/${episodeId}`, {
      headers
    });

    const data = await response.json();

    if (response.ok) {
      return data;
    } else {
      console.error("Failed to fetch episode:", data.error);
      alert("Failed to fetch episode: " + data.error);
    }
  } catch (error) {
    console.error("Error fetching episode:", error);
    alert("Failed to fetch episode.");
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
    console.log("Fetched episodes with additional fields:", data.episodes)
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

/**
 * Fetches episodes by podcast ID, excluding episodes with "published" status
 * This function is specifically used by the episode-to-do page
 * @param {string} podcastId - The podcast ID to fetch episodes for
 * @returns {Array} - Array of unpublished episodes
 */
export async function fetchUnpublishedEpisodesByPodcast(podcastId) {
  try {
    const response = await fetch(`/episodes/by_podcast/${podcastId}?exclude_statuses=published`)
    const data = await response.json()
    console.log("Fetched unpublished episodes:", data.episodes)
    if (response.ok) {
      return data.episodes || []
    } else {
      console.error("Failed to fetch unpublished episodes:", data.error)
      alert("Failed to fetch episodes: " + data.error)
      return []
    }
  } catch (error) {
    console.error("Error fetching unpublished episodes:", error)
    alert("Failed to fetch episodes.")
    return []
  }
}

export async function updateEpisode(episodeId, data) {
  const isFormData = data instanceof FormData;

  console.log("Episode ID type and value:", typeof episodeId, episodeId);

  try {
    const headers = {
      Accept: "application/json",
    };

    if (!isFormData) {
      headers["Content-Type"] = "application/json";
    }

    const response = await fetch(`/episodes/${episodeId}`, {
      method: "PUT",
      headers,
      body: isFormData ? data : JSON.stringify(data),
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
        console.error("Update Episode Error Response:", errorData);
      } catch (e) {
        errorData = { error: await response.text() };
        console.error("Update Episode Non-JSON Error Response:", errorData.error);
      }
      throw new Error(errorData?.error || errorData?.message || `HTTP error! status: ${response.status}`);
    }

    if (response.status === 204) {
      return { message: "Episode updated successfully (No Content)" };
    }

    const result = await response.json();
    console.log("Update Episode Success Response:", result);
    return result;
  } catch (error) {
    console.error("Failed to update episode:", error.message || error);
    return { error: `Failed to update episode: ${error.message || error}` };
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
