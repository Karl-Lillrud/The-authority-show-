// teamRequests.js
// New asynchronous methods for team operations calling endpoints in team.py

export async function addTeamRequest(payload) {
  console.log("Sending payload to add team:", payload); // Debugging line
  const res = await fetch("/add_teams", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  console.log("Response from add team:", data); // Debugging line
  return data;
}

export async function deleteTeamRequest(teamId) {
  const res = await fetch(`/delete_team/${teamId}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" }
  });
  return res.json();
}

export async function getTeamsRequest() {
  const res = await fetch("/get_teams", { method: "GET" });
  return res.json();
}

export async function editTeamRequest(teamId, payload) {
  console.log("Sending payload to edit team:", payload); // Debugging line
  const res = await fetch(`/edit_team/${teamId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  console.log("Response from edit team:", data); // Debugging line
  return data;
}

export async function updatePodcastTeamRequest(podcastId, payload) {
  console.log("Sending payload to update podcast:", payload); // Debugging line
  const res = await fetch(`/edit_podcasts/${podcastId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  console.log("Response from update podcast:", data); // Debugging line
  return data;
}

export async function fetchPodcasts() {
  try {
    const res = await fetch("/get_podcasts", { method: "GET" });
    const data = await res.json();
    return data.podcast || [];
  } catch (err) {
    console.error("Error fetching podcasts:", err);
    return [];
  }
}
