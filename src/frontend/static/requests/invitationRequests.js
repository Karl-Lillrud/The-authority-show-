export async function sendInvitationEmail(podName, podRss, imageUrl) {
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
        imageUrl: imageUrl // Only passing imageUrl from the RSS raw data
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
