import {
  addTeamRequest,
  getTeamsRequest, // Keep this import
  editTeamRequest,
  deleteTeamRequest,
  fetchPodcasts,
  updatePodcastTeamRequest,
  getTeamMembersRequest
} from "/static/requests/teamRequests.js";
import { sendTeamInvite } from "/static/requests/invitationRequests.js"; // Import sendTeamInvite
import { initSidebar } from "./teamSidebar.js";

// Update the UI with retrieved teams
export function updateTeamsUI(teams) {
  const container = document.querySelector(".main-content");
  if (!container) {
    console.error("Error: '.main-content' container not found.");
    return;
  }
  container.innerHTML = ""; // Clear existing content
  container.innerHTML = `
    <div class="card-container">
      ${teams
        .map(
          (team) => `
        <div class="team-card" data-id="${team._id}">
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
              ${team.members
                .map((m) => `<span class="member-chip">${m.email}</span>`)
                .join("")}
            </div>
          </div>
          <div class="team-card-footer">
            <button class="btn edit-team-btn">Edit</button>
            <button class="btn delete-team-btn">Delete</button>
          </div>
        </div>
      `
        )
        .join("")}
    </div>
  `;

  // Attach event listeners for Edit and Delete buttons
  container.querySelectorAll(".edit-team-btn").forEach((button) => {
    button.addEventListener("click", (event) => {
      const teamId = event.target.closest(".team-card").dataset.id;
      const team = teams.find((t) => t._id === teamId);
      if (team) {
        showTeamDetailModal(team); // Call the function to show the edit modal
      }
    });
  });

  container.querySelectorAll(".delete-team-btn").forEach((button) => {
    button.addEventListener("click", async (event) => {
      const teamId = event.target.closest(".team-card").dataset.id;
      try {
        const result = await deleteTeamRequest(teamId); // Call the delete API
        alert(result.message || "Team deleted successfully!");
        const updatedTeams = await getTeamsRequest(); // Fetch updated teams
        updateTeamsUI(updatedTeams); // Re-render the team cards
      } catch (error) {
        console.error("Error deleting team:", error);
      }
    });
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
  // Ensure the modal exists in the DOM
  const modal = document.getElementById("teamDetailModal");
  if (!modal) {
    console.error("Error: 'teamDetailModal' not found in the DOM.");
    return;
  }

  // Populate modal fields with team data
  document.getElementById("detailName").value = team.name || "";
  document.getElementById("detailEmail").value = team.email || "";
  document.getElementById("detailDescription").value = team.description || "";
  const membersContainer = document.getElementById("members-container-edit");
  membersContainer.innerHTML = ""; // Clear existing members
  team.members.forEach((member) => {
    const memberRow = document.createElement("div");
    memberRow.className = "member-row";
    memberRow.innerHTML = `
      <input type="email" name="memberEmail" value="${
        member.email
      }" class="form-control" required>
      <select name="memberRole" class="form-control" required>
        <option value="admin" ${
          member.role === "admin" ? "selected" : ""
        }>Admin</option>
        <option value="member" ${
          member.role === "member" ? "selected" : ""
        }>Member</option>
      </select>
      <button type="button" class="removeMemberBtn btn">Remove</button>
    `;
    membersContainer.appendChild(memberRow);

    // Add event listener to remove button
    memberRow
      .querySelector(".removeMemberBtn")
      .addEventListener("click", () => {
        membersContainer.removeChild(memberRow);
      });
  });

  // Show the modal
  modal.classList.add("show");
  modal.setAttribute("aria-hidden", "false");

  // Add event listener to close the modal
  document
    .getElementById("teamDetailCloseBtn")
    .addEventListener("click", () => {
      modal.classList.remove("show");
      modal.setAttribute("aria-hidden", "true");
    });
}

// Add a function to render members view
export function renderMembersView(members) {
  const container = document.querySelector(".main-content");
  if (!container) {
    console.error("Error: '.main-content' container not found.");
    return;
  }
  container.innerHTML = ""; // Clear existing content
  container.innerHTML = `
    <div class="members-view">
      ${members
        .map(
          (member) => `
        <div class="member-card">
          <h3>${member.fullName || member.name}</h3>
          <p><strong>Email:</strong> ${member.email}</p>
          <p><strong>Role:</strong> ${member.role || "member"}</p>
        </div>
      `
        )
        .join("")}
    </div>
  `;
}

// Export the view-switching functions
export async function switchToTeamsView() {
  const mainContent = document.querySelector(".main-content");
  if (mainContent) mainContent.innerHTML = ""; // Clear existing content

  try {
    const teams = await getTeamsRequest();
    updateTeamsUI(teams);
  } catch (error) {
    console.error("Error fetching teams:", error);
  }
}

export async function switchToMembersView() {
  const mainContent = document.querySelector(".main-content");
  if (mainContent) mainContent.innerHTML = ""; // Clear existing content

  try {
    const response = await getTeamMembersRequest();
    renderMembersView(response.members || []);
  } catch (error) {
    console.error("Error fetching members:", error);
  }
}

// Initialize the page
document.addEventListener("DOMContentLoaded", async () => {
  initSidebar(); // Initialize the sidebar
  // Initialize sidebar using the imported component

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
        description: formData.get("description"), // Ensure description is included
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

        // Trigger sendTeamInvite for each member
        for (const member of members) {
          try {
            await sendTeamInvite(teamId, member.email);
            console.log(`Invitation sent to ${member.email}`);
          } catch (error) {
            console.error(
              `Failed to send invitation to ${member.email}:`,
              error
            );
          }
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

  // Attach event listener for "Members" button
  const membersBtn = document.getElementById("sidebar-members");
  if (membersBtn) {
    membersBtn.addEventListener("click", async (event) => {
      event.preventDefault(); // Prevent default navigation behavior
      console.log("Members button pressed");
      try {
        const response = await getTeamMembersRequest();
        console.log("Fetched members:", response);
        renderMembersView(response.members || []);
      } catch (error) {
        console.error("Error fetching members:", error);
      }
    });
  } else {
    console.error("Members button not found");
  }
});
