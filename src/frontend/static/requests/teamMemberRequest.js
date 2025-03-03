async function handleRequest(url, method, body = null) {
  try {
    const options = {
      method: method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);

    if (response.ok) {
      const data = await response.json();
      console.log(data.message || 'Request was successful');
      return data; // Returning data if needed for further processing
    } else {
      const errorData = await response.json();
      console.error('Error:', errorData.error || 'Unknown error');
      return null;
    }
  } catch (error) {
    console.error('Request failed:', error);
    return null;
  }
}

// Add User to Team
async function addUserToTeam(userId, teamId, role) {
  const body = { userId, teamId, role };
  await handleRequest('/add_users_to_teams', 'POST', body);
}

// Remove User from Team
async function removeUserFromTeam(userId, teamId) {
  const body = { userId, teamId };
  await handleRequest('/remove_users_from_teams', 'POST', body);
}

// Get Team Members
async function getTeamMembers(teamId) {
  const data = await handleRequest(`/get_teams_members/${teamId}`, 'GET');
  if (data && data.members) {
    console.log('Team Members:', data.members);
  }
}

// Invite User to Team
async function inviteUserToTeam(userId, teamId, role) {
  const body = { userId, teamId, role };
  await handleRequest('/invite_user_to_team', 'POST', body);
}

// Respond to Invite
async function respondToInvite(teamId, response) {
  const body = { teamId, response }; // 'accepted' or 'declined'
  await handleRequest('/respond_invite', 'POST', body);
}
