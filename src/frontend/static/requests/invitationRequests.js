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

export async function sendTeamInvite(teamId, email, role) {
  try {
    const response = await fetch("/send_team_invite", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ teamId, email, role })
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Failed to send team invite: ${errorData.error}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error sending team invite:", error);
    throw error;
  }
}
