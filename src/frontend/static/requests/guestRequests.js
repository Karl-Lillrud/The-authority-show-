export async function addGuestRequest(payload) {
  try {
    const res = await fetch("/add_guest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errorData = await res.json();
      console.error("Backend error:", errorData.error);

      // If Google Calendar is not connected, show a specific error
      if (errorData.error.includes("connect your Google Calendar")) {
        alert(errorData.error);  // Show specific alert message
        window.location.href = "/podprofile";  // Redirect to the page where the user can connect their calendar
        return;
      }

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

// Ensure the endpoint is correctly calling the backend route
export function fetchGuestsByEpisode(episodeId) {
  return fetch(`/get_guests_by_episode/${episodeId}`, { method: "GET" })
    .then((res) => {
      if (!res.ok) {
        throw new Error("Failed to fetch guests");
      }
      return res.json();
    })
    .then((data) => {
      if (!data || !data.guests) {
        return []; // Return an empty array if no guests data exists. The previous function was throwing errors when no guest was in the episode.
      }
      return data.guests;
    })
    .catch(() => []); // Ensure that an empty array is returned in case of any error
}
