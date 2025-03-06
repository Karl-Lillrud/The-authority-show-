export async function sendInvitationEmail(email, podName, podRss) {
  try {
    const response = await fetch("/send_invitation", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: email,
        subject: "Welcome to PodManager.ai!",
        podName: podName,
        podRss: podRss,
      }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Failed to send invitation email: ${errorData.error}`);
    }
  } catch (error) {
    console.error("Error sending invitation email:", error);
  }
}
