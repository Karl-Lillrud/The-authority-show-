// Remove: import feedparser from "feedparser-promised";

// Function to add a new podcast
export async function addPodcast(data) {
  try {
    console.log("Sending podcast data to /add_podcasts:", data); // Added log
    const response = await fetch("/add_podcasts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data) // Correctly pass the entire data object
    });
    const responseData = await response.json();
    if (!response.ok) {
      console.error("Error response from /add_podcasts:", responseData); // Added log
      throw new Error(responseData.error || "Failed to add podcast");
    }
    console.log("Received response from /add_podcasts:", responseData); // Added log
    return responseData;
  } catch (error) {
    console.error("Error adding podcast:", error); // Added log
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
    const response = await fetch(`/get_podcasts/${podcastId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch podcast: ${response.statusText}`);
    }
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
