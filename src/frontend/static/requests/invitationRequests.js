/**
 * Sends an invitation email to the current user
 * @returns {Promise<Object>} Response from the server
 */
export async function sendInvitationEmail() {
  try {
    console.log("Sending invitation email request...");
    const response = await fetch("/send_invitation", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": `Bearer ${localStorage.getItem("access_token") || ""}`,
      },
      body: JSON.stringify({}) // Empty body since user info is taken from auth token
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: `HTTP Error: ${response.status} ${response.statusText}` }));
      console.error("Failed to send invitation email:", errorData);
      throw new Error(`Failed to send invitation email: ${errorData.error || "Unknown error"}`);
    }

    const data = await response.json();
    console.log("Invitation email sent successfully:", data);
    return data;
  } catch (error) {
    console.error("Error sending invitation email:", error);
    throw error;
  }
}

/**
 * Sends a team invite request
 * @param {string} teamId - ID of the team
 * @param {string} email - Email of the user to invite
 * @param {string} role - Role of the user in the team
 * @returns {Promise<Object>} Response from the server
 */
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

/**
 * Creates a guest invitation email
 * @param {string} episodeId - ID of the episode
 * @param {string} guestId - ID of the guest
 * @returns {Promise<Object>} Response from the server
 */
export async function createGuestInvitation(episodeId, guestId) {
  try {
    console.log(`Creating guest invitation for episode ${episodeId}, guest ${guestId}`);
    const response = await fetch("/create_guest_invitation", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": `Bearer ${localStorage.getItem("access_token") || ""}`,
      },
      body: JSON.stringify({
        episodeId,
        guestId
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: `HTTP Error: ${response.status} ${response.statusText}` }));
      throw new Error(`Failed to create guest invitation: ${errorData.error || "Unknown error"}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error creating guest invitation:", error);
    throw error;
  }
}

/**
 * Accepts a guest invitation
 * @param {string} token - Token from the invitation link
 * @returns {Promise<Object>} Response from the server
 */
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