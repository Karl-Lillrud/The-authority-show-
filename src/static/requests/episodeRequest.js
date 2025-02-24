export async function fetchEpisodes(guestId) {
  try {
    const response = await fetch(`/episodes/get_episodes_by_guest/${guestId}`);
    if (response.status === 404) {
      console.error("Endpoint not found:", response.url);
      alert("Failed to fetch episodes: Endpoint not found.");
      return [];
    }

    const text = await response.text();
    let data;

    try {
      data = JSON.parse(text);
    } catch (error) {
      console.error("Failed to parse JSON:", text);
      alert("Failed to fetch episodes: Invalid JSON response.");
      return [];
    }

    if (response.ok) {
      return data.episodes;
    } else if (data.error) {
      console.error("Failed to fetch episodes:", data.error);
      alert("Failed to fetch episodes: " + data.error);
      return [];
    } else {
      console.error("Unexpected response:", data);
      alert("Unexpected response while fetching episodes.");
      return [];
    }
  } catch (error) {
    console.error("Error fetching episodes:", error);
    alert("Failed to fetch episodes.");
    return [];
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
    } else if (data.error) {
      console.error("Failed to fetch tasks:", data.error);
      alert("Failed to fetch tasks: " + data.error);
    } else {
      console.error("Unexpected response:", data);
      alert("Unexpected response while fetching tasks.");
    }
  } catch (error) {
    console.error("Error fetching tasks:", error);
    alert("Failed to fetch tasks.");
  }
}

export async function addTasksToEpisode(episodeId, guestId, tasks) {
  try {
    const response = await fetch("/add_tasks_to_episode", {
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
    } else if (result.error) {
      console.error("Error adding tasks to episode:", result.error);
      alert("Error: " + result.error);
    } else {
      console.error("Unexpected response:", result);
      alert("Unexpected response while adding tasks to episode.");
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
    } else if (data.error) {
      console.error("Failed to fetch episode count:", data.error);
      alert("Failed to fetch episode count: " + data.error);
    } else {
      console.error("Unexpected response:", data);
      alert("Unexpected response while fetching episode count.");
    }
  } catch (error) {
    console.error("Error fetching episode count:", error);
    alert("Failed to fetch episode count.");
  }
}
