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
