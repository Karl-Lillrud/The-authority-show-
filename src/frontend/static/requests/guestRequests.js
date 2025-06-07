export async function addGuestRequest(payload) {
  try {
    const res = await fetch("/add_guest", {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${localStorage.getItem('access_token') || ""}` 
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errorData = await res.json();
      console.error("Error adding guest:", errorData.error);

      // If Google Calendar is not connected, show a specific error
      if (errorData.error.includes("connect your Google Calendar")) {
        throw new Error(errorData.error || "Google Calendar is not connected");
      }

      throw new Error(errorData.error || "Failed to add guest.");
    }

    const data = await res.json();
    
    // Check if invitation was sent and include that in the response
    if (payload.sendInvitation && data.invitationSent) {
      console.log("Guest invitation email was sent successfully");
    }
    
    return data;
  } catch (error) {
    console.error("Error in addGuestRequest:", error);
    throw error;
  }
}

export async function editGuestRequest(guestId, payload) {
  const res = await fetch(`/edit_guests/${guestId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const json = await res.json();

  if (!res.ok) {
    throw new Error(json.error || "Failed to edit guest");
  }

  return json;
}


export async function deleteGuestRequest(guestId) {
  if (!guestId) {
    console.error("deleteGuestRequest: guestId is undefined");
    throw new Error("Missing guestId when trying to delete guest.");
  }

  const res = await fetch(`/delete_guests/${guestId}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    const errorText = await res.text();
    console.error("Failed to delete guest:", errorText);
    throw new Error("Failed to delete guest");
  }

  return res.json();
}


export async function fetchGuestsRequest() {
  const res = await fetch("/get_guests");
  if (!res.ok) {
    throw new Error("Failed to fetch guests");
  }
  const data = await res.json();
  return data.guests || [];
}

export async function fetchGuestsByEpisode(episodeId, token) {
  if (!episodeId || episodeId === "undefined") {
    console.warn(" Invalid episodeId passed to fetchGuestsByEpisode:", episodeId);
    return [];
  }

  const res = await fetch(`/get_guests_by_episode/${episodeId}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

  if (res.status === 404) {
    return [];
  }
  if (!res.ok) {
    throw new Error("Failed to fetch guests by episode");
  }

  const data = await res.json();
  return data.guests || [];
}
