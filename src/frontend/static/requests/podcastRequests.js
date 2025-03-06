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
  if (!rssUrl) return;
  try {
    const response = await fetch(
      `https://api.rss2json.com/v1/api.json?rss_url=${encodeURIComponent(
        rssUrl
      )}`
    );
    const data = await response.json();
    if (data.status === "ok") {
      return data.feed; // Return feed data for further processing
    } else {
      console.error("Error fetching RSS feed:", data);
      throw new Error("Error fetching RSS feed");
    }
  } catch (error) {
    console.error("Error fetching RSS feed:", error);
    throw error;
  }
}

export async function schedulePodcastRecording(podcastId, guestData) {
  try {
      const response = await fetch('/schedule_podcast_recording', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json'
          },
          body: JSON.stringify({
              podcast_id: podcastId,
              guest_email: guestData.email,
              recording_date: guestData.date,
              recording_time: guestData.time,
              platform: guestData.platform
          })
      });

      const data = await response.json();
      if (!response.ok) {
          throw new Error(data.error);
      }
      return data;
  } catch (error) {
      console.error('Error scheduling podcast:', error);
      throw error;
  }
}