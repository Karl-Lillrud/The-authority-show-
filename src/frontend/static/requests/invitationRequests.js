export async function sendInvitationEmail() {
  try {
    const response = await fetch("/send_invitation", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      }
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
