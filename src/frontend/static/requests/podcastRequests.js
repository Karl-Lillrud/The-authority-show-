// Function to add a new podcast
export async function addPodcast(data) {
  try {
    const response = await fetch("/add_podcasts", {
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

// Function to get all podcasts
export async function fetchPodcasts() {
  try {
    const response = await fetch("/get_podcasts", {
      method: "GET",
      headers: { "Content-Type": "application/json" }
    });
    return await response.json();
  } catch (error) {
    console.error("Error fetching podcasts:", error);
    throw error;
  }
}

// Function to get a podcast by ID
export async function fetchPodcast(podcastId) {
  try {
    const response = await fetch(`/get_podcasts/${podcastId}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" }
    });
    return await response.json();
  } catch (error) {
    console.error("Error fetching podcast:", error);
    throw error;
  }
}

// Function to update a podcast
export async function updatePodcast(podcastId, podcastData) {
  try {
    const response = await fetch(`/edit_podcasts/${podcastId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(podcastData)
    });
    return await response.json();
  } catch (error) {
    console.error("Error updating podcast:", error);
    throw error;
  }
}

// Function to delete a podcast
export async function deletePodcast(podcastId) {
  try {
    const response = await fetch(`/delete_podcasts/${podcastId}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" }
    });
    return await response.json();
  } catch (error) {
    console.error("Error deleting podcast:", error);
    throw error;
  }
}

// Function to fetch RSS data
export async function fetchRSSData(rssUrl) {
  try {
    const response = await fetch(rssUrl);
    if (!response.ok) {
      throw new Error("Failed to fetch RSS feed.");
    }

    const rssText = await response.text();
    const parser = new DOMParser();
    const rssDoc = parser.parseFromString(rssText, "application/xml");

    const titleElement = rssDoc.querySelector("channel > title");
    if (!titleElement) {
      throw new Error("RSS feed does not contain a title.");
    }

    return titleElement.textContent;
  } catch (error) {
    throw new Error(`Error fetching RSS feed: ${error.message}`);
  }
}
