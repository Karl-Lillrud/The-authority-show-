export async function publishEpisode(episodeId, platforms, notes) {
  try {
    const response = await fetch(`/publish/api/publish_episode/${episodeId}`, { // Added /publish prefix
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // Add Authorization header if needed:
        // 'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
      },
      body: JSON.stringify({ platforms, notes }),
    });

    const result = await response.json();

    if (!response.ok) {
      console.error("Publishing error response:", result);
      // Check if result.error exists, otherwise use a generic message or response.statusText
      const errorMessage = result.error || result.message || `HTTP error! status: ${response.status}`;
      throw new Error(errorMessage);
    }
    return result; // Should contain { success: true, message: "...", data: ... }
  } catch (error) {
    console.error("Error in publishEpisode request:", error);
    // Return a structured error for the UI to handle
    // Ensure error.message is a string.
    const errorMessageString = (typeof error.message === 'string') ? error.message : "Failed to connect to the server.";
    return { success: false, error: errorMessageString };
  }
}

export async function getSasUrl(filename, contentType) {
  try {
    const res = await fetch("/publish/get_sas_url", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename, contentType }),
    });

    if (!res.ok) throw new Error("Failed to get SAS URL");
    return res.json();
  } catch (error) {
    console.error("Error getting SAS URL:", error);
    throw error;
  }
}
