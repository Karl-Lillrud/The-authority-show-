// teamRequests.js
// New asynchronous methods for team operations calling endpoints in team.py

async function addTeamRequest(payload) {
  const res = await fetch("/add_teams", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return res.json();
}

async function deleteTeamRequest(teamId) {
  const res = await fetch(`/delete_team/${teamId}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" }
  });
  return res.json();
}

async function getTeamsRequest() {
  const res = await fetch("/get_teams", { method: "GET" });
  return res.json();
}

async function editTeamRequest(teamId, payload) {
  const res = await fetch(`/edit_team/${teamId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return res.json();
}

async function updatePodcastTeamRequest(podcastId, payload) {
  const res = await fetch(`/edit_podcasts/${podcastId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return res.json();
}

