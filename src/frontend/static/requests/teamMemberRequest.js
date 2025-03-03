async function addUserToTeam(userId, teamId, role) {
    try {
      const response = await fetch('/add_users_to_teams', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId: userId,
          teamId: teamId,
          role: role,
        }),
      });
  
      if (response.ok) {
        const data = await response.json();
        console.log(data.message); // Success message
      } else {
        const errorData = await response.json();
        console.error(errorData.error); // Error message
      }
    } catch (error) {
      console.error('Error:', error);
    }
  }

  async function removeUserFromTeam(userId, teamId) {
    try {
      const response = await fetch('/remove_users_from_teams', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId: userId,
          teamId: teamId,
        }),
      });
  
      if (response.ok) {
        const data = await response.json();
        console.log(data.message); // Success message
      } else {
        const errorData = await response.json();
        console.error(errorData.error); // Error message
      }
    } catch (error) {
      console.error('Error:', error);
    }
  }

  async function getTeamMembers(teamId) {
    try {
      const response = await fetch(`/get_teams_members/${teamId}`);
  
      if (response.ok) {
        const data = await response.json();
        console.log('Team Members:', data.members);
      } else {
        const errorData = await response.json();
        console.error(errorData.error); // Error message
      }
    } catch (error) {
      console.error('Error:', error);
    }
  }

  async function inviteUserToTeam(userId, teamId, role) {
    try {
      const response = await fetch('/invite_user_to_team', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId: userId,
          teamId: teamId,
          role: role,
        }),
      });
  
      if (response.ok) {
        const data = await response.json();
        console.log(data.message); // Success message
      } else {
        const errorData = await response.json();
        console.error(errorData.error); // Error message
      }
    } catch (error) {
      console.error('Error:', error);
    }
  }

  async function respondToInvite(teamId, response) {
    try {
      const response = await fetch('/respond_invite', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          teamId: teamId,
          response: response, // 'accepted' or 'declined'
        }),
      });
  
      if (response.ok) {
        const data = await response.json();
        console.log(data.message); // Success message
      } else {
        const errorData = await response.json();
        console.error(errorData.error); // Error message
      }
    } catch (error) {
      console.error('Error:', error);
    }
  }
  

  
  
  