export async function addUserToTeamRequest(payload) {
  const res = await fetch("/add_users_to_teams", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return res.json();
}

export async function removeUserFromTeamRequest(payload) {
  const res = await fetch("/remove_users_from_teams", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return res.json();
}

export async function editTeamMemberRequest(teamId, userId, role) {
  console.log("Sending payload to /edit_team_member:", {
    teamId,
    userId,
    role
  }); // Debug log
  const res = await fetch("/edit_team_member", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ teamId, userId, role })
  });

  if (!res.ok) {
    const errorData = await res.json();
    console.error("Error response from /edit_team_member:", errorData); // Logga backend-felet
  }

  return res.json();
}

export async function deleteTeamMemberRequest(
  teamId,
  userId = null,
  email = null
) {
  console.log("Payload for deleteTeamMemberRequest:", {
    teamId,
    userId,
    email
  }); // Debugging log
  const res = await fetch("/delete_team_member", {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ teamId, userId, email })
  });
  return res.json();
}

export async function getTeamMembersRequest(teamId) {
  const res = await fetch(`/get_teams_members/${teamId}`, { method: "GET" });
  return res.json();
}

export async function getAllTeamMembersRequest() {
  const res = await fetch("/get_team_members", { method: "GET" });
  return res.json();
}
