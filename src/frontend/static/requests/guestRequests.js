export function addGuestRequest(payload) {
  return fetch("/add_guests", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  }).then((res) => res.json());
}

export function editGuestRequest(guestId, payload) {
  return fetch("/edit_guests/" + guestId, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  }).then((res) => res.json());
}

export function deleteGuestRequest(guestId) {
  return fetch("/delete_guests/" + guestId, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" }
  }).then((res) => res.json());
}

export function fetchGuestsRequest() {
  return fetch("/get_guests", { method: "GET" })
    .then((res) => {
      if (!res.ok) {
        throw new Error("Failed to fetch guests");
      }
      return res.json();
    })
    .then((data) => data.guests || []);
}
