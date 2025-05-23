// Remove: import feedparser from "feedparser-promised";

// Function to add a new podcast
export async function addPodcast(podcastData) {
  try {
    // Ensure required fields are present
    if (!podcastData.podName) {
      throw new Error("Missing required field: podName");
    }

    const response = await fetch("/api/podcasts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(podcastData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: "Failed to parse error response" }));
      console.error("Server error from addPodcast:", errorData);
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error in addPodcast:", error);
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
    const response = await fetch(`/api/podcasts/${podcastId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(podcastData),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: "Failed to update podcast and parse error response" }));
      console.error("Server error from updatePodcast:", errorData);
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error in updatePodcast:", error);
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

export async function fetchRSSData(rssUrl) {
  try {
    console.log("Fetching RSS data from URL:", rssUrl); // Added log
    const response = await fetch("/fetch_rss", {
      method: "POST", // Changed from GET to POST
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rssUrl }) // Send rssUrl in the request body
    });
    if (!response.ok) {
      throw new Error("Failed to fetch RSS feed.");
    }
    const rssData = await response.json();
    console.log("Fetched RSS data:", rssData); // Added log
    return rssData;
  } catch (error) {
    console.error("Error in fetchRSSData:", error); // Added log
    throw new Error(`Error fetching RSS feed: ${error.message}`);
  }
}

// Helper function to extract iTunes ID from feed URL
function extractItunesId(url) {
  // Try to extract from iTunes URL format
  const itunesMatch = url.match(/\/id(\d+)/);
  if (itunesMatch && itunesMatch[1]) {
    return itunesMatch[1];
  }
  return null;
}

// Helper function to extract social media links from text (existing code)
function extractSocialMediaLinks(description, link) {
  // Your existing implementation
  // ...
}
