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
    const response = await fetch(`/episodes/view_tasks_by_episode/${episodeId}`);
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

export async function registerEpisode(data) {
  try {
    if (!data.podcastId || !data.title) {
      console.error("Missing required fields: podcastId or title", data); // Added log
      throw new Error("Missing required fields: podcastId or title");
    }
    console.log("Sending data to /add_episode:", data); // Added log
    const response = await fetch("/add_episode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    const responseData = await response.json();
    console.log("Received response from /add_episode:", responseData); // Added log
    if (!response.ok) {
      console.error("Error response from /add_episode:", responseData); // Added log
      throw new Error(responseData.error || "Failed to register episode");
    }
    return responseData;
  } catch (error) {
    console.error("Error registering episode:", error); // Added log
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
    if (!response.ok) {
      throw new Error(`Failed to fetch episode: ${response.statusText}`);
    }
    const episode = await response.json();
    // Ensure binary data is correctly handled
    if (episode.episodeFiles) {
      episode.episodeFiles = episode.episodeFiles.map(file => {
        if (file.data) {
          file.data = atob(file.data); // Decode base64 to binary string
        }
        return file;
      });
    }
    return episode;
  } catch (error) {
    console.error(`Failed to fetch episode: ${error.message}`);
    throw error;
  }
}

export async function updateEpisode(episodeId, updatedData) {
  try {
    const response = await fetch(`/update_episodes/${episodeId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updatedData)
    });
    const result = await response.json();
    if (response.ok) {
      return result;
    } else {
      console.error("Failed to update episode:", result.error);
      alert("Failed to update episode: " + result.error);
    }
  } catch (error) {
    console.error("Error updating episode:", error);
    alert("Failed to update episode.");
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

