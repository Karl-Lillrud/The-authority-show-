import {
  addTeamRequest,
  getTeamsRequest,
  editTeamRequest,
  deleteTeamRequest,
  fetchPodcasts,
  updatePodcastTeamRequest,
  getTeamMembers
} from "/static/requests/teamRequests.js";
import { sendTeamInvite } from "/static/requests/invitationRequests.js";
import { initSidebar } from "../components/sidebar.js";
import { sidebarIcons } from "../components/sidebar-icons.js";

// Update the UI with retrieved teams
function updateTeamsUI(teams) {
  let container = document.querySelector(".card-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "card-container";
    (document.querySelector("main") || document.body).appendChild(container);
  }
  container.innerHTML = "";
  if (teams.length === 0) {
    container.innerHTML = "<p>No teams available.</p>";
    return;
  }
  teams.forEach((team) => {
    const card = document.createElement("div");
    card.className = "team-card";
    card.setAttribute("data-id", team._id);
    card.innerHTML = `
      <div class="team-card-header">
        <h2>${team.name}</h2>
        <p><strong>Email:</strong> ${team.email}</p>
      </div>
      <div class="team-card-body">
        <p><strong>Description:</strong> ${
          team.description || "No description available"
        }</p>
        <p><strong>Podcasts:</strong> ${team.podNames || "N/A"}</p>
        <p><strong>Members:</strong></p>
        <div class="member-chips">
          ${(() => {
            // Sort so creator comes first
            const sortedMembers = team.members.sort((a, b) => {
              if (a.role === "creator" && b.role !== "creator") return -1;
              if (a.role !== "creator" && b.role === "creator") return 1;
              return 0;
            });
            return sortedMembers
              .map(
                (m) => `
            <span class="member-chip">
              <span>${m.email}</span>
              ${
                m.role === "creator"
                  ? '<span class="creator-badge">Creator</span>'
                  : m.verified === true
                  ? '<span class="verified-badge">Verified</span>'
                  : '<span class="not-verified-badge">Not Verified</span>'
              }
            </span>
          `
              )
              .join("");
          })()}
        </div>
      </div>
      <div class="team-card-footer">
        <button class="btn edit-team-btn">Edit</button>
        <button class="btn delete-team-btn">Delete</button>
      </div>
    `;
    card
      .querySelector(".edit-team-btn")
      .addEventListener("click", () => showTeamDetailModal(team));
    card
      .querySelector(".delete-team-btn")
      .addEventListener("click", async () => {
        try {
          const result = await deleteTeamRequest(team._id);
          alert(result.message || "Team deleted successfully!");
          card.remove();
          const teams = await getTeamsRequest();
          updateTeamsUI(teams);
        } catch (error) {
          console.error("Error deleting team:", error);
        }
      });
    container.appendChild(card);
  });
}

// Helper to render assigned podcasts based on original assignments and pending changes.
function renderAssignedPodcasts(
  teamId,
  originalAssignedPodcasts,
  pendingPodcastChanges
) {
  const container = document.getElementById("assignedPodcasts");
  container.innerHTML = "";
  const finalAssignments = {};
  originalAssignedPodcasts.forEach((p) => {
    finalAssignments[p._id] = p;
  });
  for (const [podcastId, newTeam] of Object.entries(pendingPodcastChanges)) {
    if (newTeam === teamId) {
      if (!finalAssignments[podcastId]) {
        finalAssignments[podcastId] = {
          _id: podcastId,
          podName: "Pending: " + podcastId
        };
      }
    } else if (newTeam === "REMOVE") {
      delete finalAssignments[podcastId];
    }
  }
  Object.values(finalAssignments).forEach((podcast) => {
    const chip = document.createElement("div");
    chip.className = "podcast-chip";
    chip.innerHTML = `${podcast.podName} <span class="remove-chip" data-id="${podcast._id}">&times;</span>`;
    container.appendChild(chip);
  });
}

// Helper to populate the podcast dropdown for assignment based on pending changes.
async function populatePodcastDropdownForTeam(teamId, pendingPodcastChanges) {
  const dropdown = document.getElementById("podcastAssignmentDropdown");
  dropdown.innerHTML = '<option value="">Select Podcast to Add</option>';
  const podcasts = await fetchPodcasts();
  podcasts.forEach((podcast) => {
    let isAssigned = false;
    if (podcast.teamId === teamId) {
      isAssigned = true;
    }
    if (pendingPodcastChanges[podcast._id] === teamId) {
      isAssigned = true;
    }
    if (pendingPodcastChanges[podcast._id] === "REMOVE") {
      isAssigned = false;
    }
    if (!isAssigned) {
      const option = document.createElement("option");
      option.value = podcast._id;
      option.textContent = podcast.podName;
      dropdown.appendChild(option);
    }
  });
}

// Helper to close modals
function closeModal(modal) {
  modal.classList.remove("show");
  modal.setAttribute("aria-hidden", "true");
}

// Function to add a new member input row
function addMemberRow(containerId) {
  const membersContainer = document.getElementById(containerId);
  const memberRow = document.createElement("div");
  memberRow.className = "member-row";
  memberRow.innerHTML = `
    <input type="email" name="memberEmail" placeholder="Email" class="form-control" required>
    <select name="memberRole" class="form-control" required>
      <option value="admin">Admin</option>
      <option value="member">Member</option>
    </select>
    <button type="button" class="removeMemberBtn btn">Remove</button>
  `;
  membersContainer.appendChild(memberRow);

  // Add event listener to the remove button
  memberRow.querySelector(".removeMemberBtn").addEventListener("click", () => {
    membersContainer.removeChild(memberRow);
  });
}

// The team detail modal logic
function showTeamDetailModal(team) {
  // Local state for pending podcast assignment changes
  const pendingPodcastChanges = {};
  let originalAssignedPodcasts = [];

  async function initAssignments() {
    const podcasts = await fetchPodcasts();
    originalAssignedPodcasts = podcasts.filter((p) => p.teamId === team._id);
    renderAssignedPodcasts(
      team._id,
      originalAssignedPodcasts,
      pendingPodcastChanges
    );
    populatePodcastDropdownForTeam(team._id, pendingPodcastChanges);
  }
  initAssignments();

  // Pre-populate team detail modal fields.
  document.getElementById("detailName").value = team.name;
  document.getElementById("detailEmail").value = team.email;
  document.getElementById("detailDescription").value = team.description;
  document.getElementById("members-container-edit").innerHTML = "";
  team.members.forEach((member) => {
    addMemberRow("members-container-edit");
    const memberRows = document.querySelectorAll(
      "#members-container-edit .member-row"
    );
    const lastRow = memberRows[memberRows.length - 1];
    lastRow.querySelector("input[name='memberEmail']").value = member.email;
    lastRow.querySelector("select[name='memberRole']").value = member.role;
  });

  const modal = document.getElementById("teamDetailModal");
  modal.classList.add("show");
  modal.setAttribute("aria-hidden", "false");

  // Handle podcast addition via dropdown.
  const dropdown = document.getElementById("podcastAssignmentDropdown");
  dropdown.onchange = () => {
    const podcastId = dropdown.value;
    if (podcastId) {
      pendingPodcastChanges[podcastId] = team._id;
      renderAssignedPodcasts(
        team._id,
        originalAssignedPodcasts,
        pendingPodcastChanges
      );
      populatePodcastDropdownForTeam(team._id, pendingPodcastChanges);
      dropdown.value = "";
      alert("Podcast addition pending. Press Save to finalize.");
    }
  };

  // Handle removal of a podcast chip.
  const assignedContainer = document.getElementById("assignedPodcasts");
  assignedContainer.onclick = (event) => {
    if (event.target.classList.contains("remove-chip")) {
      const podcastId = event.target.getAttribute("data-id");
      pendingPodcastChanges[podcastId] = "REMOVE";
      renderAssignedPodcasts(
        team._id,
        originalAssignedPodcasts,
        pendingPodcastChanges
      );
      populatePodcastDropdownForTeam(team._id, pendingPodcastChanges);
      alert("Podcast removal pending. Press Save to finalize.");
    }
  };

  // Delete button immediately deletes the team.
  const deleteBtn = document.getElementById("deleteTeamBtn");
  deleteBtn.onclick = async () => {
    try {
      const result = await deleteTeamRequest(team._id);
      alert(result.message || "Team deleted successfully!");
      const card = document.querySelector(`.team-card[data-id="${team._id}"]`);
      if (card) card.remove();
      closeModal(modal);
      const teams = await getTeamsRequest();
      updateTeamsUI(teams);
    } catch (error) {
      console.error("Error deleting team:", error);
    }
  };

  // Save button finalizes pending podcast assignment changes and updates team details.
  const saveBtn = document.getElementById("saveTeamBtn");
  saveBtn.onclick = async () => {
    // First update all pending podcast assignments with a PUT request.
    try {
      for (const [podcastId, newTeam] of Object.entries(
        pendingPodcastChanges
      )) {
        if (newTeam === team._id) {
          // Podcast selected: update podcast with the teamId
          const updateResponse = await updatePodcastTeamRequest(podcastId, {
            teamId: team._id
          });
          console.log("Update podcast response:", updateResponse);
        } else if (newTeam === "REMOVE") {
          // Podcast removal: set teamId to empty
          const updateResponse = await updatePodcastTeamRequest(podcastId, {
            teamId: ""
          });
          console.log("Update podcast response:", updateResponse);
        }
      }
    } catch (err) {
      console.error("Error updating podcast assignments:", err);
      alert("Error updating podcast assignments.");
      return;
    }

    const payload = {
      name: document.getElementById("detailName").value,
      email: document.getElementById("detailEmail").value,
      description: document.getElementById("detailDescription").value,
      members: []
    };

    document
      .querySelectorAll("#members-container-edit .member-row")
      .forEach((row) => {
        payload.members.push({
          email: row.querySelector("input[name='memberEmail']").value,
          role: row.querySelector("select[name='memberRole']").value
        });
      });

    try {
      const result = await editTeamRequest(team._id, payload);
      console.log("Edit team response:", result);
      alert(result.message || "Team updated successfully!");
      closeModal(modal);
      const teams = await getTeamsRequest();
      updateTeamsUI(teams);
    } catch (error) {
      console.error("Error editing team:", error);
    }
  };

  // Modal close handler.
  document.getElementById("teamDetailCloseBtn").onclick = () =>
    closeModal(modal);
  window.addEventListener("click", (event) => {
    if (event.target === modal) {
      closeModal(modal);
    }
  });
}

// Initialize the page
document.addEventListener("DOMContentLoaded", async () => {
  // Initialize sidebar from teamSidebar.js
  initSidebar();
  initSidebarIcons(); // Flyttad funktion initieras här

  // Fetch teams data
  const teams = await getTeamsRequest();
  updateTeamsUI(teams);

  // Add event listeners to the Add Member buttons
  document.getElementById("addMemberBtn").addEventListener("click", () => {
    addMemberRow("members-container");
  });

  document.getElementById("addMemberBtnEdit").addEventListener("click", () => {
    addMemberRow("members-container-edit");
  });

  // Initialize podcast dropdown
  async function populatePodcastDropdown() {
    const podcastDropdown = document.getElementById("podcastDropdown");
    if (podcastDropdown) {
      try {
        const podcasts = await fetchPodcasts();
        podcasts.forEach((podcast) => {
          const option = document.createElement("option");
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

  // Setup Add Team Modal
  const addTeamModal = document.getElementById("addTeamModal");
  const addTeamForm = addTeamModal
    ? addTeamModal.querySelector("form")
    : document.querySelector("form");

  if (addTeamForm) {
    addTeamForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(addTeamForm);
      const members = [];
      document.querySelectorAll(".member-row").forEach((row) => {
        members.push({
          email: row.querySelector("input[name='memberEmail']").value,
          role: row.querySelector("select[name='memberRole']").value
        });
      });
      // Extract the selected podcast ID from the form
      const podcastId = formData.get("podcastId");
      const payload = {
        name: formData.get("name"),
        email: formData.get("email"),
        description: formData.get("description"),
        members: members
      };

      try {
        const response = await addTeamRequest(payload);
        console.log("Add team response:", response);
        const teamId = response.team_id;
        alert("Team successfully created!");

        // If a podcast was selected, update it with the new team ID using a PUT request.
        if (podcastId) {
          const updateResponse = await updatePodcastTeamRequest(podcastId, {
            teamId: teamId
          });
          console.log("Podcast updated with teamId:", updateResponse);
        }
        closeModal(addTeamModal);
        const teams = await getTeamsRequest();
        updateTeamsUI(teams);
      } catch (error) {
        console.error("Error adding team:", error);
      }
    });
  }

  if (addTeamModal) {
    const openModalBtn = document.getElementById("openModalBtn");
    const closeButtons = document.querySelectorAll(
      "#modalCloseBtn, #modalCloseBtn2"
    );

    if (openModalBtn) {
      openModalBtn.addEventListener("click", () => {
        addTeamModal.classList.add("show");
        addTeamModal.setAttribute("aria-hidden", "false");
      });
    }

    closeButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        closeModal(addTeamModal);
      });
    });

    window.addEventListener("click", (event) => {
      if (event.target === addTeamModal) {
        closeModal(addTeamModal);
      }
    });

    window.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && addTeamModal.classList.contains("show")) {
        closeModal(addTeamModal);
      }
    });
  }

  // New Member Modal functionality
  const addMemberBtnSidebar = document.getElementById("addNewMemberBtn");
  const addMemberModal = document.getElementById("addMemberModal");
  const closeAddMemberModal = document.getElementById("closeAddMemberModal");
  const cancelAddMember = document.getElementById("cancelAddMember");
  const addMemberForm = document.getElementById("addMemberForm");
  const teamSelect = document.getElementById("teamSelect");

  // Function to fetch teams and populate dropdown
  async function populateTeamDropdown() {
    try {
      const teams = await getTeamsRequest();
      teamSelect.innerHTML = '<option value="">Select a Team</option>';
      teams.forEach((team) => {
        const option = document.createElement("option");
        option.value = team._id;
        option.textContent = team.name;
        teamSelect.appendChild(option);
      });
    } catch (err) {
      console.error("Error fetching teams for dropdown:", err);
    }
  }

  // Open modal on Add New Member button click
  if (addMemberBtnSidebar && addMemberModal) {
    addMemberBtnSidebar.addEventListener("click", () => {
      populateTeamDropdown();
      addMemberModal.classList.add("show");
      addMemberModal.setAttribute("aria-hidden", "false");
    });
  }

  // Modal close handlers
  if (closeAddMemberModal) {
    closeAddMemberModal.addEventListener("click", () => {
      addMemberModal.classList.remove("show");
      addMemberModal.setAttribute("aria-hidden", "true");
    });
  }
  if (cancelAddMember) {
    cancelAddMember.addEventListener("click", () => {
      addMemberModal.classList.remove("show");
      addMemberModal.setAttribute("aria-hidden", "true");
    });
  }

  // Handle Add Member form submission in the new member modal
  if (addMemberForm) {
    addMemberForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("memberEmail").value;
      const role = document.getElementById("memberRole").value;
      const teamId = teamSelect.value;
      if (!email || !teamId || !role) {
        alert("Please provide member email, role and select a team.");
        return;
      }
      try {
        // First, trigger sending the invitation email
        const inviteResult = await sendTeamInvite(teamId, email);
        console.log(`Invitation sent: `, inviteResult);
        // Then, update the team's member array via new endpoint
        const res = await fetch("/add_team_member", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ teamId, email, role })
        });
        const updateResult = await res.json();
        alert(
          updateResult.message || `Member added and invitation sent to ${email}`
        );
        addMemberModal.classList.remove("show");
        addMemberModal.setAttribute("aria-hidden", "true");
      } catch (error) {
        console.error("Error sending team invite or adding member:", error);
        alert("Failed to add member.");
      }
    });
  }

  // Initialize menu item event listeners
  const teamsMenuItem = document.getElementById("sidebar-teams");
  const membersMenuItem = document.getElementById("sidebar-members");

  if (teamsMenuItem && membersMenuItem) {
    teamsMenuItem.addEventListener("click", (event) => {
      event.preventDefault();
      membersMenuItem.classList.remove("active");
      teamsMenuItem.classList.add("active");
      switchToTeamsView();
    });

    membersMenuItem.addEventListener("click", (event) => {
      event.preventDefault();
      teamsMenuItem.classList.remove("active");
      membersMenuItem.classList.add("active");
      switchToMembersView();
    });
  }
});

function initSidebarIcons() {
  const backToDashboardIcon = document.getElementById("back-to-dashboard-icon");
  const teamsIcon = document.getElementById("teams-icon");
  const membersIcon = document.getElementById("members-icon");

  if (backToDashboardIcon)
    backToDashboardIcon.innerHTML = sidebarIcons.backToDashboard;
  if (teamsIcon) teamsIcon.innerHTML = sidebarIcons.teams;
  if (membersIcon) membersIcon.innerHTML = sidebarIcons.members;
}

export function switchToTeamsView() {
  console.log("Switching to Teams view");
  const mainContent = document.querySelector(".main-content");
  mainContent.innerHTML = `
    <div class="main-header">
      <h1>Teams</h1>
    </div>
    <div class="card-container">
      <!-- Team cards will be dynamically inserted here -->
    </div>
  `;
  getTeamsRequest()
    .then((teams) => updateTeamsUI(teams))
    .catch((error) => console.error("Error rendering teams view:", error));
}

async function renderMembersView() {
  const mainContent = document.querySelector(".main-content");
  mainContent.innerHTML = `
    <div class="main-header">
      <h1>Members</h1>
    </div>
    <div id="members-view-container" class="card-container"></div>
      <!-- Member cards will be dynamically inserted here -->
    </div>
  `;

  try {
    const teams = await getTeamsRequest();
    const membersView = document.getElementById("members-view-container");

    for (const team of teams) {
      // Iterera över alla medlemmar i teamet
      if (team.members && Array.isArray(team.members)) {
        team.members.forEach((member) => {
          const card = document.createElement("div");
          card.className = "member-card";
          card.innerHTML = `
            <div class="member-card-header">
              <h3>${member.fullName || member.email}</h3>
              ${
                member.role === "creator"
                  ? '<span class="creator-badge">Creator</span>'
                  : member.verified
                  ? '<span class="verified-badge">Verified</span>'
                  : '<span class="not-verified-badge">Not Verified</span>'
              }
            </div>
            <div class="member-card-body">
              <p><strong>Email:</strong> ${member.email}</p>
              <p><strong>Role:</strong> ${member.role}</p>
              <p><strong>Team:</strong> ${team.name}</p>
            </div>
          `;
          membersView.appendChild(card);
        });
      } else {
        console.warn(`No members found for team: ${team.name}`);
      }
    }
  } catch (error) {
    console.error("Error fetching members:", error);
    const membersView = document.getElementById("members-view-container");
    membersView.innerHTML = `<p>Error loading members. Please try again later.</p>`;
  }
}

export function switchToMembersView() {
  console.log("Switching to Members view");
  renderMembersView();
}
