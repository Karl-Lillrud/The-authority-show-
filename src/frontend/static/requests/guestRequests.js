export async function addGuestRequest(payload) {
  try {
    const res = await fetch("/add_guest", { // Correct endpoint
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errorData = await res.json();
      console.error("Backend error:", errorData.error);
      throw new Error(errorData.error || "Failed to add guest.");
    }

    return await res.json();
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
  return res.json();
}

export async function deleteGuestRequest(guestId) {
  const res = await fetch(`/delete_guests/${guestId}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" }
  });
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

export async function fetchGuestsByEpisode(episodeId) {
  if (!episodeId || episodeId === "undefined") {
    console.warn(
      "⚠️ Invalid episodeId passed to fetchGuestsByEpisode:",
      episodeId
    );
    return [];
  }

  const res = await fetch(`/get_guests_by_episode/${episodeId}`);
  if (res.status === 404) {
    return [];
  }
  if (!res.ok) {
    throw new Error("Failed to fetch guests by episode");
  }

  const data = await res.json();
  return data.guests || [];
}
