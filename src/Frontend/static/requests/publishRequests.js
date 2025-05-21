export async function publishEpisode(episodeId, platforms, notes) {
  try {
    const response = await fetch(`/api/publish_episode/${episodeId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // Add Authorization header if needed:
        // 'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
      },
      body: JSON.stringify({ platforms, notes }),
    })

    const result = await response.json()

    if (!response.ok) {
      console.error("Publishing error response:", result)
      throw new Error(result.error || `HTTP error! status: ${response.status}`)
    }
    return result // Should contain { success: true, message: "...", data: ... }
  } catch (error) {
    console.error("Error in publishEpisode request:", error)
    // Return a structured error for the UI to handle
    return { success: false, error: error.message || "Failed to connect to the server." }
  }
}

export async function getSasUrl(filename, contentType) {
  try {
    const res = await fetch("/api/publish/get_sas_url", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename, contentType }),
    })

    if (!res.ok) throw new Error("Failed to get SAS URL")
    return res.json()
  } catch (error) {
    console.error("Error getting SAS URL:", error)
    throw error
  }
}
