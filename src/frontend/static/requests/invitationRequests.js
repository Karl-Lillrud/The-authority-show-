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

export async function sendTeamInviteRequest(teamId, email, role) {
  console.log("Sending request to /send_team_invite"); // Debug log
  const res = await fetch("/send_team_invite", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ teamId, email, role })
  });
  const data = await res.json();
  console.log("Response from /send_team_invite:", data); // Debug log
  return data;
}

export async function createGuestInvitation(episodeId, guestId) {
  try {
    const response = await fetch("/invite-guest", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        episode_id: episodeId,
        guest_id: guestId,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Failed to create invitation: ${errorData.error}`);
    }

    const data = await response.json();
    return {
      message: data.message,
      inviteUrl: data.invite_url,
    };
  } catch (error) {
    console.error("Error creating guest invitation:", error);
    throw error;
  }
}

export async function acceptGuestInvitation(token) {
  try {
    const response = await fetch(`/accept-invite/${token}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Failed to accept invitation: ${errorData.error}`);
    }

    const data = await response.json();
    return {
      message: data.message,
    };
  } catch (error) {
    console.error("Error accepting guest invitation:", error);
    throw error;
  }
}