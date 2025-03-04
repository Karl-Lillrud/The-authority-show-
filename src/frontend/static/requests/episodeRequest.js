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
