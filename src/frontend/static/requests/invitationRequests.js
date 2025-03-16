export async function sendInvitationEmail(
  podName,
  podRss,
  imageUrl,
  additionalData = {}
) {
  try {
    const response = await fetch("/send_invitation", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        subject: "Welcome to PodManager.ai!",
        podName: podName,
        podRss: podRss,
        imageUrl: imageUrl,
        description: additionalData.description || "",
        socialMedia: additionalData.socialMedia || [],
        category: additionalData.category || "",
        author: additionalData.author || "",
        // New fields to capture more podcast information
        language: additionalData.language || "",
        copyright: additionalData.copyright || "",
        explicit: additionalData.explicit || false,
        podcastType: additionalData.podcastType || "episodic",
        ownerEmail: additionalData.ownerEmail || "",
        ownerName: additionalData.ownerName || "",
        keywords: additionalData.keywords || [],
        itunesId: additionalData.itunesId || "",
        guid: additionalData.guid || "",
        pubDate: additionalData.pubDate || "",
        lastBuildDate: additionalData.lastBuildDate || "",
        fundingUrl: additionalData.fundingUrl || "",
        fundingText: additionalData.fundingText || "",
        complete: additionalData.complete || false, // Indicates if podcast is complete/no longer publishing
        episodes: additionalData.episodes || [] // Include episodes data
      })
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Failed to send invitation email: ${errorData.error}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error sending invitation email:", error);
    throw error;
  }
}
