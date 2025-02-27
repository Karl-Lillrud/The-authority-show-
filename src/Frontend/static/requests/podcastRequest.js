// Example functions for podcast-related requests
export async function addPodcast(data) {
  try {
    const response = await fetch("/add_podcast", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    return await response.json();
  } catch (error) {
    console.error("Error adding podcast:", error);
    throw error;
  }
}

export async function fetchPodcasts() {
  try {
    const response = await fetch("/get_podcasts");
    const data = await response.json();

    if (response.ok) {
      return data.podcasts;
    } else {
      console.error("Failed to fetch podcasts:", data.error);
      alert("Failed to fetch podcasts: " + data.error);
    }
  } catch (error) {
    console.error("Error fetching podcasts:", error);
    alert("Failed to fetch podcasts.");
  }
}

export async function fetchPodcast(podcastId) {
  try {
    const response = await fetch(`/get_podcast/${podcastId}`);
    const data = await response.json();

    if (response.ok) {
      return data;
    } else {
      console.error("Failed to fetch podcast:", data.error);
      alert("Failed to fetch podcast: " + data.error);
    }
  } catch (error) {
    console.error("Error fetching podcast:", error);
    alert("Failed to fetch podcast.");
  }
}

export async function savePodcast(podcastData) {
  try {
    const response = await fetch("/register_podcast", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(podcastData)
    });

    const result = await response.json();
    if (response.ok) {
      alert("Podcast saved successfully!");
      return result;
    } else {
      console.error("Error saving podcast:", result.error);
      alert("Error: " + result.error);
    }
  } catch (error) {
    console.error("Error saving podcast:", error);
    alert("Failed to save podcast.");
  }
}

export async function updatePodcast(podcastId, podcastData) {
  try {
    const response = await fetch(`/update_podcast/${podcastId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(podcastData)
    });

    const result = await response.json();
    if (response.ok) {
      alert("Podcast updated successfully!");
      return result;
    } else {
      console.error("Error updating podcast:", result.error);
      alert("Error: " + result.error);
    }
  } catch (error) {
    console.error("Error updating podcast:", error);
    alert("Failed to update podcast.");
  }
}

export async function deletePodcast(podcastId) {
  try {
    const response = await fetch(`/delete_podcast/${podcastId}`, {
      method: "DELETE"
    });

    const result = await response.json();
    if (response.ok) {
      alert("Podcast deleted successfully!");
      return result;
    } else {
      console.error("Error deleting podcast:", result.error);
      alert("Error: " + result.error);
    }
  } catch (error) {
    console.error("Error deleting podcast:", error);
    alert("Failed to delete podcast.");
  }
}
