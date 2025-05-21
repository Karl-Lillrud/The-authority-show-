export async function fetchEpisodes(guestId) {
  try {
    const response = await fetch(`/episodes/get_episodes_by_guest/${guestId}`);
    const data = await response.json();

    if (response.ok) {
      return data.episodes;
    } else {
      console.error("Failed to fetch episodes:", data.error);
      alert("Failed to fetch episodes: " + data.error);
    }
  } catch (error) {
    console.error("Error fetching episodes:", error);
    alert("Failed to fetch episodes.");
  }
}

export async function viewEpisodeTasks(episodeId) {
  try {
    const response = await fetch(
      `/episodes/view_tasks_by_episode/${episodeId}`
    );
    const data = await response.json();

    if (response.ok) {
      return data.tasks;
    } else {
      console.error("Failed to fetch tasks:", data.error);
      alert("Failed to fetch tasks: " + data.error);
    }
  } catch (error) {
    console.error("Error fetching tasks:", error);
    alert("Failed to fetch tasks.");
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
        guest_id: guestId
      })
    });

    const result = await response.json();
    if (response.ok) {
      alert("Tasks added to episode successfully!");
      return result;
    } else {
      console.error("Error adding tasks to episode:", result.error);
      alert("Error: " + result.error);
    }
  } catch (error) {
    console.error("Error adding tasks to episode:", error);
    alert("Failed to add tasks to episode.");
  }
}

export async function fetchEpisodeCountByGuest(guestId) {
  try {
    const response = await fetch(`/episodes/count_by_guest/${guestId}`);
    const data = await response.json();

    if (response.ok) {
      return data.count;
    } else {
      console.error("Failed to fetch episode count:", data.error);
      alert("Failed to fetch episode count: " + data.error);
    }
  } catch (error) {
    console.error("Error fetching episode count:", error);
    alert("Failed to fetch episode count.");
  }
}

export async function registerEpisode(episodeData) {
  console.log("[episodeRequest.js] Received episodeData for registration:", JSON.stringify(episodeData, null, 2));
  
  if (!episodeData.podcastId || !episodeData.title) {
    console.error(
      "[episodeRequest.js] Validation Error: Missing required fields. podcastId:", 
      episodeData.podcastId, "title:", episodeData.title
    );
    throw new Error("Missing required fields: podcastId or title"); 
  }

  try {
    const response = await fetch("/add_episode", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(episodeData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        error: "Failed to register episode and parse error response.",
      }));
      console.error(
        "[episodeRequest.js] Error registering episode - Server responded with an error:",
        response.status,
        errorData,
      );
      throw new Error(
        errorData.error || `HTTP error! status: ${response.status}`,
      );
    }

    const data = await response.json();
    console.log("[episodeRequest.js] Episode registered successfully via API:", data);
    return data;
  } catch (error) {
    console.error("[episodeRequest.js] Error in registerEpisode function:", error.message);
    throw error;
  }
}

export async function fetchEpisodesByPodcast(podcastId) {
  try {
    const response = await fetch(`/episodes/by_podcast/${podcastId}`);
    const data = await response.json();
    console.log("Fetched episodes with additional fields:", data.episodes); // Log episodes
    if (response.ok) {
      return data.episodes;
    } else {
      console.error("Failed to fetch episodes:", data.error);
      alert("Failed to fetch episodes: " + data.error);
    }
  } catch (error) {
    console.error("Error fetching episodes:", error);
    alert("Failed to fetch episodes.");
  }
}

export async function fetchEpisode(episodeId) {
  try {
    const response = await fetch(`/get_episodes/${episodeId}`);
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

export async function updateEpisode(episodeId, formData) {
  if (!(formData instanceof FormData)) {
    throw new Error("Expected FormData for episode update");
  }

  try {
    const response = await fetch(`/episodes/${episodeId}`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        Accept: "application/json"
        // Do not set Content-Type; let the browser handle it for FormData
      },
      body: formData
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || `Failed to update episode (status: ${response.status})`);
    }

    console.log(`Updated episode ${episodeId} successfully`);

    return result;
  } catch (error) {
    console.error(`Error updating episode ${episodeId}:`, error);
    throw error;
  }
}

export async function deleteEpisode(episodeId) {
  try {
    const response = await fetch(`/delete_episodes/${episodeId}`, {
      method: "DELETE"
    });

    const contentType = response.headers.get("content-type");
    if (contentType && contentType.indexOf("application/json") !== -1) {
      const result = await response.json();
      if (response.ok) {
        return result;
      } else {
        console.error("Failed to delete episode:", result.error);
        alert("Failed to delete episode: " + result.error);
      }
    } else {
      console.error("Unexpected response format:", await response.text());
      alert("Failed to delete episode: Unexpected response format");
    }
  } catch (error) {
    console.error("Error deleting episode:", error);
    alert("Failed to delete episode.");
  }
}

// In episodeRequest.js
export async function fetchAllEpisodes() {
  try {
    const response = await fetch("/get_episodes");
    const data = await response.json();
    if (response.ok) {
      return data.episodes;
    } else {
      console.error("Failed to fetch episodes:", data.error);
      throw new Error(data.error || "Failed to fetch episodes");
    }
  } catch (error) {
    console.error("Error fetching episodes:", error);
    throw error;
  }
}
