import {
  addTeamRequest,
  getTeamsRequest,
  editTeamRequest,
  deleteTeamRequest,
  fetchPodcasts,
  updatePodcastTeamRequest
} from "/static/requests/teamRequests.js";
import { sendTeamInvite } from "/static/requests/invitationRequests.js";
import { initSidebar } from "../components/sidebar.js";
import { sidebarIcons } from "../components/sidebar-icons.js";
import { deleteTeamMemberRequest } from "/static/requests/userToTeamRequests.js";
import { successSvg, errorSvg, infoSvg, closeSvg } from "./teamSvg.js";

// Notification system for team.js
function showNotification(title, message, type = "info") {
  // Remove any existing notification
  const existingNotification = document.querySelector(".notification");
  if (existingNotification) {
    existingNotification.remove();
  }

  // Create notification elements
  const notification = document.createElement("div");
  notification.className = `notification ${type}`;

  // Icon based on type
  let iconSvg = "";
  if (type === "success") {
    iconSvg = successSvg;
  } else if (type === "error") {
    iconSvg = errorSvg;
  } else {
    iconSvg = infoSvg;
  }

  notification.innerHTML = `
    <div class="notification-icon">${iconSvg}</div>
    <div class="notification-content">
      <div class="notification-title">${title}</div>
      <div class="notification-message">${message}</div>
    </div>
    <div class="notification-close">
      ${closeSvg}
    </div>
  `;

  // Add to DOM
  document.body.appendChild(notification);

  // Add event listener to close button
  notification
    .querySelector(".notification-close")
    .addEventListener("click", () => {
      notification.classList.remove("show");
      setTimeout(() => {
        notification.remove();
      }, 500);
    });

  // Show notification with animation
  setTimeout(() => {
    notification.classList.add("show");
  }, 10);

  // Auto hide after 5 seconds
  setTimeout(() => {
    if (document.body.contains(notification)) {
      notification.classList.remove("show");
      setTimeout(() => {
        if (document.body.contains(notification)) {
          notification.remove();
        }
      }, 500);
    }
  }, 5000);
}

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
        <p><strong>Team Email:</strong> ${team.email}</p>
      </div>
      <div class="team-card-body">
        <p><strong>Description:</strong> ${
          team.description || "No description available"
        }</p>
        <p><strong>Podcasts:</strong> ${team.podNames || "N/A"}</p>
        <div class="members-section">
          <strong>Members:</strong>
          <div>
            ${
              team.members.length > 0
                ? team.members
                    .map(
                      (m) => `
                      <span class="member-chip">
                        ${m.email}
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
                    .join("")
                : "No members available"
            }
          </div>
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
    card.querySelector(".delete-team-btn").addEventListener("click", () => {
      // New confirmation popup for deleting a team which will remove all members as well
      showConfirmationPopup(
        "Delete Team",
        "Deleting this team will also remove all associated members. Are you sure you want to proceed?",
        async () => {
          try {
            const result = await deleteTeamRequest(team._id);
            showNotification(
              "Success",
              result.message || "Team deleted successfully!",
              "success"
            );
            card.remove();
            const teams = await getTeamsRequest();
            updateTeamsUI(teams);
          } catch (error) {
            console.error("Error deleting team:", error);
            showNotification(
              "Error",
              "An error occurred while deleting the team.",
              "error"
            );
          }
        },
        () => {
          showNotification("Info", "Team deletion cancelled.", "info");
        }
      );
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
      showNotification(
        "Success",
        "Podcast addition pending. Press Save to finalize.",
        "success"
      );
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
      showNotification(
        "Success",
        "Podcast removal pending. Press Save to finalize.",
        "success"
      );
    }
  };

  // Delete button immediately deletes the team.
  const deleteBtn = document.getElementById("deleteTeamBtn");
  deleteBtn.onclick = async () => {
    try {
      const result = await deleteTeamRequest(team._id);
      showNotification(
        "Success",
        result.message || "Team deleted successfully!",
        "success"
      );
      const card = document.querySelector(`.team-card[data-id="${team._id}"]`);
      if (card) card.remove();
      closeModal(modal);
      const teams = await getTeamsRequest();
      updateTeamsUI(teams);
    } catch (error) {
      console.error("Error deleting team:", error);
      showNotification(
        "Error",
        "An error occurred while deleting the team.",
        "error"
      );
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
      showNotification("Error", "Error updating podcast assignments.", "error");
      return;
    }

    const payload = {
      name: document.getElementById("detailName").value,
      email: document.getElementById("detailEmail").value,
      description: document.getElementById("detailDescription").value,
      members: [] // Members är tomt eftersom det inte längre används här
    };

    try {
      const result = await editTeamRequest(team._id, payload);
      console.log("Edit team response:", result);
      showNotification(
        "Success",
        result.message || "Team updated successfully!",
        "success"
      );
      closeModal(modal);
      const teams = await getTeamsRequest();
      updateTeamsUI(teams);
    } catch (error) {
      console.error("Error editing team:", error);
      showNotification(
        "Error",
        "An error occurred while updating the team.",
        "error"
      );
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

      // Extract the selected podcast ID from the form
      const podcastId = formData.get("podcastId");
      const payload = {
        name: formData.get("name"),
        email: formData.get("email"),
        description: formData.get("description"),
        members: [] // Members är tomt eftersom det inte längre används här
      };

      try {
        const response = await addTeamRequest(payload);
        console.log("Add team response:", response);
        const teamId = response.team_id;
        showNotification("Success", "Team successfully created!", "success");

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
        showNotification("Error", "Failed to create team.", "error");
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

  // New Member Modal functionality remains unchanged
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
    // Ta bort eventuella tidigare registrerade eventhanterare
    addMemberForm.removeEventListener("submit", handleAddMemberFormSubmission);

    // Lägg till eventhanteraren
    addMemberForm.addEventListener("submit", handleAddMemberFormSubmission);
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
  const addTeamIcon = document.querySelector("#openModalBtn .sidebar-icon");
  const addMemberIcon = document.querySelector(
    "#addNewMemberBtn .sidebar-icon"
  );

  if (backToDashboardIcon)
    backToDashboardIcon.innerHTML = sidebarIcons.backToDashboard;
  if (teamsIcon) teamsIcon.innerHTML = sidebarIcons.teams;
  if (membersIcon) membersIcon.innerHTML = sidebarIcons.members;
  if (addTeamIcon) addTeamIcon.innerHTML = sidebarIcons.add;
  if (addMemberIcon) addMemberIcon.innerHTML = sidebarIcons.add;
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
  `;

  try {
    const teams = await getTeamsRequest();
    const membersView = document.getElementById("members-view-container");

    for (const team of teams) {
      console.log(`Team: ${team.name}`, team.members); // Debugging: Log team members
      if (team.members && Array.isArray(team.members)) {
        team.members.forEach((member) => {
          console.log(`Member: ${member.email}`, member); // Debugging: Log each member
          const card = document.createElement("div");
          card.className = "member-card";
          card.innerHTML = `
            <div class="member-card-header">
              <h3>${member.fullName || member.email}</h3>
              <span class="member-chip">
                ${
                  member.role === "creator"
                    ? '<span class="creator-badge">Creator</span>'
                    : member.role === "admin"
                    ? '<span class="admin-badge">Admin</span>'
                    : '<span class="member-badge">Member</span>'
                }
                ${
                  member.role !== "creator" && !member.verified
                    ? '<span class="not-verified-badge">Not Verified</span>'
                    : member.role !== "creator" && member.verified
                    ? '<span class="verified-badge">Verified</span>'
                    : ""
                }
              </span>
            </div>
            <div class="member-card-body">
              ${
                member.verified
                  ? `<p><strong>Email:</strong> ${member.email}</p>`
                  : ""
              }
              ${
                member.phone
                  ? `<p><strong>Phone:</strong> ${member.phone}</p>`
                  : ""
              }
              <p><strong>Role:</strong> ${member.role}</p>
              <p><strong>Team:</strong> ${team.name}</p>
              <div class="member-card-footer"> <!-- Ensure this class is applied -->
                <button class="btn edit-member-btn">Edit</button>
                <button class="btn delete-member-btn">Delete</button>
              </div>
            </div>
          `;
          card
            .querySelector(".edit-member-btn")
            .addEventListener("click", () =>
              showEditMemberModal(team._id, member)
            );
          card
            .querySelector(".delete-member-btn")
            .addEventListener("click", () =>
              deleteMember(team._id, member.userId, member.email, member.role)
            );
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

function showConfirmationPopup(title, message, onConfirm, onCancel) {
  console.log("showConfirmationPopup called with:", title, message); // Debugging log

  // Remove any existing popup
  const existingPopup = document.querySelector(".confirmation-popup");
  if (existingPopup) {
    existingPopup.remove();
  }

  // Create popup elements
  const popup = document.createElement("div");
  popup.className = "popup confirmation-popup show";

  popup.innerHTML = `
    <div class="form-box">
      <h2 class="form-title">${title}</h2>
      <p>${message}</p>
      <div class="form-actions">
        <button class="cancel-btn" id="cancelPopupBtn">Cancel</button>
        <button class="save-btn" id="confirmPopupBtn">Confirm</button>
      </div>
    </div>
  `;

  // Add to DOM
  document.body.appendChild(popup);

  // Add event listeners for buttons
  document.getElementById("confirmPopupBtn").addEventListener("click", () => {
    console.log("Confirm button clicked"); // Debugging log
    onConfirm();
    popup.remove();
  });

  document.getElementById("cancelPopupBtn").addEventListener("click", () => {
    console.log("Cancel button clicked"); // Debugging log
    if (onCancel) onCancel();
    popup.remove();
  });
}

// Update deleteMember function to ensure popup is triggered
async function deleteMember(teamId, userId = null, email = null, role = null) {
  console.log("deleteMember called with:", { teamId, userId, email, role }); // Debug log

  try {
    // Modified condition to ensure case-insensitive check for 'creator'
    if (role && role.toLowerCase() === "creator") {
      showConfirmationPopup(
        "Delete Creator",
        "This member is the creator of the team. Deleting the creator will delete the entire team. Are you sure you want to proceed?",
        async () => {
          try {
            await deleteTeam(teamId); // Proceed to delete the entire team
            showNotification(
              "Success",
              "Team and creator deleted successfully!",
              "success"
            );
            renderMembersView(); // Refresh the members view
          } catch (error) {
            console.error("Error deleting team:", error);
            showNotification(
              "Error",
              "An error occurred while deleting the team.",
              "error"
            );
          }
        },
        () => {
          showNotification("Info", "Deletion canceled.", "info");
        }
      );
      return;
    }

    // Proceed to delete the member
    const result = await deleteTeamMemberRequest(teamId, userId, email);
    if (result.message) {
      showNotification(
        "Success",
        result.message || "Member deleted successfully!",
        "success"
      );
      renderMembersView(); // Refresh the members view
    } else {
      showNotification(
        "Error",
        result.error || "Failed to delete member.",
        "error"
      );
    }
  } catch (error) {
    console.error("Error deleting member:", error);
    showNotification(
      "Error",
      "An error occurred while deleting the member.",
      "error"
    );
  }
}

// Example usage for unverified members
function handleDeleteUnverifiedMember(teamId, email, role) {
  deleteMember(teamId, null, email, role);
}

function showEditMemberModal(teamId, member) {
  const modal = document.getElementById("editMemberModal");
  document.getElementById("editMemberEmail").value = member.email;
  document.getElementById("editMemberRole").value = member.role;
  modal.classList.add("show");
  modal.setAttribute("aria-hidden", "false");

  document.getElementById("saveEditMemberBtn").onclick = async () => {
    const updatedEmail = document.getElementById("editMemberEmail").value;
    const updatedRole = document.getElementById("editMemberRole").value;

    if (!teamId || !updatedEmail || !updatedRole) {
      showNotification(
        "Error",
        "Missing teamId, email, or role. Please check your input.",
        "error"
      );
      return;
    }

    try {
      // Step 1: Delete the old member
      const deleteResult = await deleteTeamMemberRequest(
        teamId,
        member.userId,
        member.email
      );
      if (deleteResult.error) {
        showNotification(
          "Error",
          deleteResult.error || "Failed to delete old member.",
          "error"
        );
        return;
      }

      // Step 2: Add the new member
      const addMemberPayload = {
        teamId,
        email: updatedEmail,
        role: updatedRole
      };
      console.log("Payload for adding new member:", addMemberPayload); // Debugging log
      const addMemberResponse = await fetch("/add_team_member", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(addMemberPayload)
      });
      const addMemberResult = await addMemberResponse.json();

      if (addMemberResult.error) {
        showNotification(
          "Error",
          addMemberResult.error || "Failed to add new member.",
          "error"
        );
        return;
      }

      // Step 3: Send invitation email to the new member
      try {
        const inviteResult = await sendTeamInvite(teamId, updatedEmail);
        if (inviteResult.error) {
          showNotification(
            "Error",
            inviteResult.error || "Failed to send invitation email.",
            "error"
          );
        } else {
          showNotification(
            "Success",
            "Member updated and invitation email sent successfully!",
            "success"
          );
        }
      } catch (inviteError) {
        console.error("Error sending invitation email:", inviteError);
        showNotification(
          "Error",
          "Failed to send invitation email to the new member.",
          "error"
        );
      }

      modal.classList.remove("show");
      renderMembersView(); // Refresh the members view
    } catch (error) {
      console.error("Error updating member:", error);
      showNotification(
        "Error",
        "An error occurred while updating the member.",
        "error"
      );
    }
  };

  document.getElementById("cancelEditMemberBtn").onclick = () => {
    modal.classList.remove("show");
  };
}

async function addTeam(payload) {
  try {
    const response = await addTeamRequest(payload);
    showNotification("Success", "Team successfully created!", "success");
    const teams = await getTeamsRequest();
    updateTeamsUI(teams);
  } catch (error) {
    console.error("Error adding team:", error);
    showNotification("Error", "Failed to create team.", "error");
  }
}

async function deleteTeam(teamId) {
  try {
    const result = await deleteTeamRequest(teamId);
    if (result.message) {
      showNotification(
        "Success",
        result.message || "Team deleted successfully!",
        "success"
      );
      const teams = await getTeamsRequest();
      updateTeamsUI(teams);
    } else {
      showNotification(
        "Error",
        result.error || "Failed to delete team.",
        "error"
      );
    }
  } catch (error) {
    console.error("Error deleting team:", error);
    showNotification(
      "Error",
      "An error occurred while deleting the team.",
      "error"
    );
  }
}

async function saveTeamDetails(teamId, payload) {
  try {
    const result = await editTeamRequest(teamId, payload);
    if (result.message) {
      showNotification(
        "Success",
        result.message || "Team updated successfully!",
        "success"
      );
      const teams = await getTeamsRequest();
      updateTeamsUI(teams);
    } else {
      showNotification(
        "Error",
        result.error || "Failed to update team.",
        "error"
      );
    }
  } catch (error) {
    console.error("Error updating team:", error);
    showNotification(
      "Error",
      "An error occurred while updating the team.",
      "error"
    );
  }
}

async function handleAddMemberFormSubmission(e) {
  e.preventDefault();
  const email = document.getElementById("memberEmail").value;
  const role = document.getElementById("memberRole").value;
  const teamId = document.getElementById("teamSelect").value;

  if (!email || !teamId || !role) {
    showNotification(
      "Error",
      "Please provide member email, role, and select a team.",
      "error"
    );
    return;
  }

  try {
    const inviteResult = await sendTeamInvite(teamId, email);
    console.log(`Invitation sent: `, inviteResult);

    const res = await fetch("/add_team_member", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ teamId, email, role })
    });
    const updateResult = await res.json();

    if (updateResult.error && updateResult.error.includes("creator")) {
      showNotification(
        "The provided email is already used by the team creator.",
        "error"
      );
    } else if (updateResult.message) {
      showNotification(
        "Success",
        "Invitation mail sent successfully!",
        "success"
      );
      document.getElementById("addMemberModal").classList.remove("show");
    } else {
      showNotification(
        "Error",
        updateResult.error || "Failed to add member.",
        "error"
      );
    }
  } catch (error) {
    if (error.message.includes("User is already a member of this team")) {
      showNotification(
        "Error",
        "The provided email is already used by the team creator.",
        "error"
      );
    } else {
      console.error("Error sending team invite or adding member:", error);
      showNotification("Error", "Failed to add member.", "error");
    }
  }
}

// Update existing event listeners to use showNotification
document
  .getElementById("addMemberForm")
  .addEventListener("submit", handleAddMemberFormSubmission);
