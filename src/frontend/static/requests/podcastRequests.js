// Remove: import feedparser from "feedparser-promised";

// Function to add a new podcast
export async function addPodcast(podcastData) {
  try {
    const response = await fetch("/api/podcasts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(podcastData),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: "Failed to add podcast and parse error response" }));
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
    console.log("[podcastRequests.js] Attempting to fetch /get_podcasts");
    const response = await fetch("/get_podcasts", {
      method: "GET",
      headers: { "Content-Type": "application/json" }
    });
    console.log(`[podcastRequests.js] /get_podcasts response status: ${response.status}`);
    if (!response.ok) {
      // Try to parse error json, but prepare for non-json errors too
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        errorData = { error: `HTTP error! status: ${response.status}, non-JSON response` };
      }
      console.error("[podcastRequests.js] Error fetching podcasts, server returned error:", errorData);
      // Return the error structure so loadPodcasts can inspect podcastData.error
      return errorData; 
    }
    const jsonData = await response.json();
    console.log("[podcastRequests.js] Successfully fetched and parsed podcasts:", jsonData);
    return jsonData;
  } catch (error) {
    console.error("[podcastRequests.js] Network or other error in fetchPodcasts:", error);
    // Ensure a structure with an .error field is returned or thrown for consistency
    // Throwing will make it go to loadPodcasts's catch block
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

// All fetches use /get_podcasts and /get_podcasts/<id> which are now correct in backend
