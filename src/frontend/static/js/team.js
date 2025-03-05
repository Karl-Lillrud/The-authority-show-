// team.js
document.addEventListener('DOMContentLoaded', function() {
  // Function to update the UI with the retrieved teams
  function updateTeamsUI(teams) {
    let container = document.querySelector('.card-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'card-container';
      (document.querySelector('main') || document.body).appendChild(container);
    }
    container.innerHTML = '';
    if (teams.length === 0) {
      container.innerHTML = '<p>No teams available.</p>';
      return;
    }
    teams.forEach(team => {
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `
        <p><strong>Podcast:</strong> ${team.podName || 'N/A'}</p>
        <h4>${team.name}</h4>
        <p><strong>Email:</strong> ${team.email}</p>
        <p><strong>Description:</strong> ${team.description}</p>
        <p><strong>Members:</strong> ${team.members.map(m => m.userId).join(", ")}</p>
      `;
      // Open detail modal on click
      card.addEventListener('click', () => showTeamDetailModal(team));
      container.appendChild(card);
    });
  }

  function showTeamDetailModal(team) {
    // Pre-populate modal input fields with team data
    document.getElementById('detailName').value = team.name;
    document.getElementById('detailEmail').value = team.email;
    document.getElementById('detailDescription').value = team.description;
    document.getElementById('detailMembers').textContent = team.members.map(m => m.userId).join(", ");
    document.getElementById('detailPodcast').value = team.podName || "N/A";

    const modal = document.getElementById('teamDetailModal');
    modal.classList.add('show');
    modal.setAttribute('aria-hidden', 'false');

    // Set delete action
    const deleteBtn = document.getElementById('deleteTeamBtn');
    deleteBtn.onclick = async () => {
      try {
          // Now delete the team
          const result = await deleteTeamRequest(team._id);
          alert(result.message || "Team deleted successfully!");
      
          modal.classList.remove('show');
          modal.setAttribute('aria-hidden', 'true');
          const teams = await getTeamsRequest();
          updateTeamsUI(teams);
      } catch (error) {
          console.error("Error deleting team:", error);
      }
  };
    

    // Set save action to update team data based on current input values
    const saveBtn = document.getElementById('saveTeamBtn');
    saveBtn.onclick = async () => {
      const payload = {
        name: document.getElementById('detailName').value,
        email: document.getElementById('detailEmail').value,
        description: document.getElementById('detailDescription').value
      };
      try {
        const result = await editTeamRequest(team._id, payload);
        alert(result.message || "Team updated successfully!");
        modal.classList.remove('show');
        modal.setAttribute('aria-hidden', 'true');
        const teams = await getTeamsRequest();
        updateTeamsUI(teams);
      } catch (error) {
        console.error("Error editing team:", error);
      }
    };

    // Close modal on clicking the close button
    document.getElementById('teamDetailCloseBtn').onclick = () => {
      modal.classList.remove('show');
      modal.setAttribute('aria-hidden', 'true');
    };
  }

  // Optional: Close modal if clicking outside modal content
  window.addEventListener('click', (event) => {
    const modal = document.getElementById('teamDetailModal');
    if (event.target === modal) {
      modal.classList.remove('show');
      modal.setAttribute('aria-hidden', 'true');
    }
  });

  // Retrieve teams and update UI on page load
  getTeamsRequest().then(data => {
    updateTeamsUI(data);
  });

  async function populatePodcastDropdown() {
    const podcastDropdown = document.getElementById('podcastDropdown');
    if (podcastDropdown) {
      try {
        // Fetch podcasts using the /get_podcasts endpoint
        const res = await fetch("/get_podcasts", { method: "GET" });
        const data = await res.json();
        // Assuming the returned data structure is { podcast: [...] }
        const podcasts = data.podcast || [];
        podcasts.forEach(podcast => {
          const option = document.createElement('option');
          option.value = podcast._id;
          option.textContent = podcast.podName;
          podcastDropdown.appendChild(option);
        });
      } catch (err) {
        console.error("Error fetching podcasts:", err);
      }
    }
  }
  populatePodcastDropdown();

  // New function to check if a podcast already has a team
  async function checkPodcastHasTeam(podcastId) {
    const res = await fetch(`/get_podcasts/${podcastId}`, { method: "GET" });
    const data = await res.json();
    return data.podcast && data.podcast.teamId; // Returns true if podcast already has a teamId
  }

  // Add team modal and form handling
  const addTeamModal = document.getElementById('addTeamModal');
  const addTeamForm = addTeamModal ? addTeamModal.querySelector('form') : document.querySelector('form');

  if (addTeamForm) {
    addTeamForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      const formData = new FormData(addTeamForm);
      const payload = {
        name: formData.get('name'),
        email: formData.get('email'),
        description: formData.get('description')
      };
      // Get the selected podcast ID from the dropdown
      const podcastId = formData.get('podcastId');
      
      // Check if the selected podcast already has a team
      const hasTeam = await checkPodcastHasTeam(podcastId);
      if (hasTeam) {
        alert("This podcast already has a team. You cannot create a new team for it.");
        return; // Stop the form submission
      }

      try {
        // Create the team
        const response = await addTeamRequest(payload);
        const teamId = response.team_id;
        alert("Team successfully created!");
        // If a podcast is selected, update it with the new teamId
        if (podcastId && teamId) {
          const updatePayload = { teamId: teamId };
          const updateResponse = await updatePodcastTeamRequest(podcastId, updatePayload);
          console.log("Podcast updated:", updateResponse);
        }
        // Close the Add Team modal after adding a team
        addTeamModal.classList.remove('show');
        addTeamModal.setAttribute('aria-hidden', 'true');
        const teams = await getTeamsRequest();
        updateTeamsUI(teams);
      } catch (error) {
        console.error("Error adding team or updating podcast:", error);
      }
    });
  }

  // Modal open/close handling for Add Team Modal
  if (addTeamModal) {
    const openModalBtn = document.getElementById('openModalBtn');
    const closeButtons = document.querySelectorAll('#modalCloseBtn, #modalCloseBtn2');

    if (openModalBtn) {
      openModalBtn.addEventListener('click', () => {
        addTeamModal.classList.add('show');
        addTeamModal.setAttribute('aria-hidden', 'false');
      });
    }

    closeButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        addTeamModal.classList.remove('show');
        addTeamModal.setAttribute('aria-hidden', 'true');
      });
    });

    window.addEventListener('click', (event) => {
      if (event.target === addTeamModal) {
        addTeamModal.classList.remove('show');
        addTeamModal.setAttribute('aria-hidden', 'true');
      }
    });

    window.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && addTeamModal.classList.contains('show')) {
        addTeamModal.classList.remove('show');
        addTeamModal.setAttribute('aria-hidden', 'true');
      }
    });
  }
});
