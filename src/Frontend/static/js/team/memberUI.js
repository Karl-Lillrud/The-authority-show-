import { showNotification, showConfirmationPopup } from "./notifications.js";
import { edit } from "./teamSvg.js";
import { closeModal } from "./modals.js";
import { getTeamsRequest } from "/static/requests/teamRequests.js";
import {
  deleteTeamMemberRequest,
  editTeamMemberRequest
} from "/static/requests/userToTeamRequests.js";
import {
  editTeamMemberByEmailRequest,
  addTeamMemberRequest
} from "/static/requests/teamRequests.js";
import { sendTeamInviteRequest } from "/static/requests/invitationRequests.js";
import { updateTeamsUI } from "./teamUI.js";

export async function renderMembersView() {
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
      if (team.members && Array.isArray(team.members)) {
        team.members.forEach((member) => {
          const card = document.createElement("div");
          card.className = "member-card";
          card.innerHTML = `
  <div class="member-card-header" style="position: relative;">
    <h3 class="text-truncate">${member.email}</h3>
    <button class="edit-icon-btn" style="position: absolute; top: 8px; right: 8px;">${edit}</button>
  </div>
  <div class="member-card-body">
    ${
      member.fullName
        ? `<p><strong>Full Name:</strong> <span class="text-truncate">${member.fullName}</span></p>`
        : ""
    }
    ${
      member.phone
        ? `<p><strong>Phone:</strong> <span class="text-truncate">${member.phone}</span></p>`
        : ""
    }
    <p><strong>Role:</strong> ${member.role}</p>
    <p><strong>Team:</strong> <span class="text-truncate">${
      team.name
    }</span></p>
    <div class="member-card-footer">
      <span class="member-badge">
        ${
          member.role === "creator"
            ? '<span class="creator-badge">Creator</span>'
            : (member.verified
                ? '<span class="verified-badge">Verified</span>'
                : '<span class="not-verified-badge">Not Verified</span>') +
              '<span class="role-badge ' +
              member.role.toLowerCase() +
              '">' +
              member.role +
              "</span>"
        }
      </span>
    </div>
  </div>
`;
          if (member.role !== "creator") {
            card
              .querySelector(".edit-icon-btn")
              .addEventListener("click", () =>
                showTeamCardEditMemberModal(team._id, member)
              );
          } else {
            card.querySelector(".edit-icon-btn").style.display = "none";
          }
          membersView.appendChild(card);
        });
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

export async function deleteMember(
  teamId,
  userId = null,
  email = null,
  role = null,
  skipConfirmation = false
) {
  try {
    // Skip confirmation if requested
    if (skipConfirmation) {
      const result = await deleteTeamMemberRequest(teamId, userId, email);
      if (result.message) {
        showNotification(
          "Success",
          result.message || "Member deleted successfully!",
          "success"
        );
        renderMembersView();
      } else {
        showNotification(
          "Error",
          result.error || "Failed to delete member.",
          "error"
        );
      }
      return;
    }

    // Show popup for creator deletion
    if (role && role.toLowerCase() === "creator") {
      showConfirmationPopup(
        "Delete Creator",
        "This member is the creator of the team. Deleting the creator will delete the entire team. Are you sure you want to proceed?",
        async () => {
          try {
            import("./teamOperations.js").then(async ({ deleteTeam }) => {
              await deleteTeam(teamId);
              showNotification(
                "Success",
                "Team and creator deleted successfully!",
                "success"
              );
              renderMembersView();
            });
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

    // Show popup for regular member deletion
    showConfirmationPopup(
      "Delete Member",
      "Are you sure you want to delete this member? This action cannot be undone.",
      async () => {
        try {
          const result = await deleteTeamMemberRequest(teamId, userId, email);
          if (result.message) {
            showNotification(
              "Success",
              result.message || "Member deleted successfully!",
              "success"
            );
            renderMembersView();
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
      },
      () => {
        showNotification("Info", "Member deletion canceled.", "info");
      }
    );
  } catch (error) {
    console.error("Error deleting member:", error);
    showNotification(
      "Error",
      "An error occurred while deleting the member.",
      "error"
    );
  }
}

export function showTeamCardEditMemberModal(teamId, member) {
  const modal = document.getElementById("teamCardEditMemberModal");
  const emailInput = document.getElementById("teamCardEditMemberEmail");
  const roleSelect = document.getElementById("teamCardEditMemberRole");
  const fullNameInput = document.getElementById("teamCardEditMemberFullName");
  const phoneInput = document.getElementById("teamCardEditMemberPhone");
  const editBtn = document.getElementById("teamCardEditMemberEditBtn");
  const saveBtn = document.getElementById("teamCardEditMemberSaveBtn");
  const closeBtn = document.getElementById("teamCardEditMemberCloseBtn");

  // Store original values
  const originalEmail = member.email;
  emailInput.value = member.email;
  fullNameInput.value = member.fullName || "";
  phoneInput.value = member.phone || "";

  // Show/hide fields based on data availability
  fullNameInput.parentElement.style.display = member.fullName ? "" : "none";
  phoneInput.parentElement.style.display = member.phone ? "" : "none";

  // Set up role options
  const roles = [
    "CoHost",
    "Guest",
    "Scriptwriter",
    "Producer",
    "AudioEngineer",
    "SoundDesigner",
    "Researcher",
    "GuestCoordinator",
    "Showrunner",
    "SocialMediaManager",
    "GraphicDesigner",
    "Copywriter",
    "Publicist",
    "SponsorshipManager",
    "MarketingStrategist",
    "AnalyticsSpecialist",
    "ShowCoordinator",
    "Webmaster"
  ];
  roleSelect.innerHTML = roles
    .map(
      (role) =>
        `<option value="${role}" ${
          member.role === role ? "selected" : ""
        }>${role}</option>`
    )
    .join("");

  // Set up help text and initial states
  let roleHelp = document.getElementById("teamCardEditMemberRoleHelpText");
  if (!roleHelp) {
    roleHelp = document.createElement("div");
    roleHelp.id = "teamCardEditMemberRoleHelpText";
    roleHelp.style.fontSize = "0.8em";
    roleHelp.style.color = "red";
    roleHelp.style.marginLeft = "0.5cm";
    roleSelect.parentElement.appendChild(roleHelp);
  }

  // Handle creator role differently
  if (member.role === "creator") {
    roleHelp.textContent = "";
    roleSelect.disabled = true;
    editBtn.style.display = "none";
  } else {
    roleHelp.textContent = !member.verified
      ? "The user must be verified before you can change roles."
      : "";
    roleSelect.disabled = true;
    editBtn.style.display = "inline-block";
  }

  // Initial state - all fields readonly
  emailInput.readOnly = true;
  fullNameInput.readOnly = true;
  phoneInput.readOnly = true;
  saveBtn.disabled = true;

  // Show modal
  modal.classList.add("show");
  modal.setAttribute("aria-hidden", "false");

  // Global edit button enables all fields
  editBtn.onclick = () => {
    emailInput.readOnly = false;
    fullNameInput.readOnly = false;
    phoneInput.readOnly = false;

    // Only enable role select if user is verified
    if (member.verified && member.role !== "creator") {
      roleSelect.disabled = false;
    }

    // Enable save button
    saveBtn.disabled = false;

    // Add visual indication that fields are editable
    emailInput.style.backgroundColor = "rgba(255, 111, 97, 0.05)";
    fullNameInput.style.backgroundColor = "rgba(255, 111, 97, 0.05)";
    phoneInput.style.backgroundColor = "rgba(255, 111, 97, 0.05)";

    emailInput.style.borderColor = "var(--highlight-color)";
    fullNameInput.style.borderColor = "var(--highlight-color)";
    phoneInput.style.borderColor = "var(--highlight-color)";

    // Focus on the first field
    emailInput.focus();
  };

  // Save changes
  saveBtn.onclick = async () => {
    const newEmail = emailInput.value;
    const newRole = roleSelect.value;
    const newFullName = fullNameInput.value;
    const newPhone = phoneInput.value;

    if (!teamId || !newEmail || !newRole) {
      showNotification("Error", "Missing teamId, email, or role.", "error");
      return;
    }
    modal.classList.remove("show");
    modal.setAttribute("aria-hidden", "true");

    // Handle email change
    if (newEmail !== originalEmail) {
      showConfirmationPopup(
        "Change Email",
        "Are you sure you want to change the email? The previous member will be removed, and a new verification email will be sent.",
        async () => {
          try {
            await deleteMember(
              teamId,
              member.userId,
              originalEmail,
              member.role,
              true
            );
            const addResult = await addTeamMemberRequest(
              teamId,
              newEmail,
              newRole
            );
            if (addResult.error) {
              showNotification(
                "Error",
                addResult.error || "Failed to add new member.",
                "error"
              );
              return;
            }
            const inviteResult = await sendTeamInviteRequest(
              teamId,
              newEmail,
              newRole
            );
            if (inviteResult.error) {
              showNotification(
                "Error",
                inviteResult.error || "Failed to send invitation.",
                "error"
              );
              return;
            }
            showNotification(
              "Success",
              "Member updated and invitation sent successfully!",
              "success"
            );
            const teams = await getTeamsRequest();
            updateTeamsUI(teams);
            renderMembersView();
          } catch (error) {
            console.error("Error updating member:", error);
            showNotification(
              "Error",
              "An error occurred while updating the member.",
              "error"
            );
          }
        },
        () => {
          showNotification("Info", "Email change canceled.", "info");
        }
      );
      return;
    }

    // Handle role or other field changes
    if (
      newRole !== member.role ||
      newFullName !== (member.fullName || "") ||
      newPhone !== (member.phone || "")
    ) {
      try {
        const result = member.userId
          ? await editTeamMemberRequest(
              teamId,
              member.userId,
              newRole,
              newFullName,
              newPhone
            )
          : await editTeamMemberByEmailRequest(teamId, originalEmail, newRole);
        if (result.error) {
          showNotification(
            "Error",
            result.error || "Failed to update role.",
            "error"
          );
          return;
        }
        showNotification(
          "Success",
          "Member details updated successfully!",
          "success"
        );
        const teams = await getTeamsRequest();
        updateTeamsUI(teams);
        renderMembersView();
      } catch (error) {
        console.error("Error updating member:", error);
        showNotification(
          "Error",
          "An error occurred while updating the member.",
          "error"
        );
      }
    } else {
      showNotification("Info", "No changes were made.", "info");
    }
  };

  // Close button handler
  closeBtn.onclick = () => {
    modal.classList.remove("show");
    modal.setAttribute("aria-hidden", "true");
  };

  // Close on outside click
  window.addEventListener("click", (event) => {
    if (event.target === modal) {
      modal.classList.remove("show");
      modal.setAttribute("aria-hidden", "true");
    }
  });

  // Delete button handler
  const deleteBtn = document.getElementById("teamCardEditMemberDeleteBtn");
  deleteBtn.addEventListener("click", () => {
    showConfirmationPopup(
      "Delete Member",
      "Are you sure you want to delete this member? This action cannot be undone.",
      async () => {
        closeModal(modal);
        await deleteMember(
          teamId,
          member.userId,
          member.email,
          member.role,
          true
        );
      },
      () => {
        showNotification("Info", "Member deletion canceled.", "info");
      }
    );
  });

  // Make sure email field has text truncation
  emailInput.classList.add("text-truncate");
}

// Helper function to add individual edit buttons to fields
function addFieldEditButton(inputElement, fieldName) {
  // Create container for the field
  const container = document.createElement("div");
  container.className = "field-edit-container";
  container.style.position = "relative";
  container.style.display = "flex";
  container.style.alignItems = "center";

  // Create edit button
  const editButton = document.createElement("button");
  editButton.className = "field-edit-btn";
  editButton.innerHTML = edit;
  editButton.style.position = "absolute";
  editButton.style.right = "10px";
  editButton.style.top = "50%";
  editButton.style.transform = "translateY(-50%)";
  editButton.style.background = "transparent";
  editButton.style.border = "none";
  editButton.style.cursor = "pointer";
  editButton.style.padding = "5px";
  editButton.style.borderRadius = "50%";
  editButton.style.display = "flex";
  editButton.style.alignItems = "center";
  editButton.style.justifyContent = "center";
  editButton.title = `Edit ${fieldName}`;

  // Add hover effect
  editButton.addEventListener("mouseenter", () => {
    editButton.style.backgroundColor = "rgba(255, 111, 97, 0.1)";
  });

  editButton.addEventListener("mouseleave", () => {
    editButton.style.backgroundColor = "transparent";
  });

  // Add click handler to make the field editable
  editButton.addEventListener("click", () => {
    if (inputElement.tagName.toLowerCase() === "select") {
      inputElement.disabled = false;
    } else {
      inputElement.readOnly = false;
    }
    inputElement.focus();

    // Enable save button
    document.getElementById("teamCardEditMemberSaveBtn").disabled = false;

    // Add visual indication that field is editable
    inputElement.style.backgroundColor = "rgba(255, 111, 97, 0.05)";
    inputElement.style.borderColor = "var(--highlight-color)";
  });

  // Insert the button next to the input
  const parent = inputElement.parentNode;
  parent.appendChild(editButton);
}

export async function handleAddMemberFormSubmission(e) {
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
    const inviteResult = await sendTeamInviteRequest(teamId, email, role);
    const addMemberResult = await addTeamMemberRequest(teamId, email, role);

    if (addMemberResult.error) {
      showNotification("Error", addMemberResult.error, "error");
      return;
    }

    showNotification("Success", "Member added successfully!", "success");
    document.getElementById("addMemberModal").classList.remove("show");
    const teams = await getTeamsRequest();
    updateTeamsUI(teams);
  } catch (error) {
    console.error("Error in handleAddMemberFormSubmission:", error);
    showNotification("Error", "Failed to add member.", "error");
  }
}
