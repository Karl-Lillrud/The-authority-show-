import { showNotification, showConfirmationPopup } from "../components/notifications.js";
import { updateTeamsUI } from "./teamUI.js";
import {
  getTeamsRequest,
  editTeamRequest,
  deleteTeamRequest,
  updatePodcastTeamRequest,
  fetchPodcasts
} from "/static/requests/teamRequests.js";

// Helper to close modals
export function closeModal(modal) {
  modal.classList.remove("show");
  modal.setAttribute("aria-hidden", "true");
}

// Helper to render assigned podcasts
export function renderAssignedPodcasts(
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

// Helper to populate podcast dropdown
export async function populatePodcastDropdownForTeam(
  teamId,
  pendingPodcastChanges
) {
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

// Team detail modal
export function showTeamDetailModal(team) {
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

  // Pre-populate team detail modal fields
  const nameInput = document.getElementById("detailName");
  const emailInput = document.getElementById("detailEmail");
  const descriptionInput = document.getElementById("detailDescription");

  nameInput.value = team.name;
  emailInput.value = team.email;
  descriptionInput.value = team.description;

  // Set all fields to readonly initially
  nameInput.readOnly = true;
  emailInput.readOnly = true;
  descriptionInput.readOnly = true;
  document.getElementById("podcastAssignmentDropdown").disabled = true;

  // New edit button handler for Team Details
  const editTeamDetailsBtn = document.getElementById("editTeamDetailsBtn");
  if (editTeamDetailsBtn) {
    editTeamDetailsBtn.onclick = () => {
      // Unlock Name, Team Email, Description and Podcast dropdown
      nameInput.readOnly = false;
      emailInput.readOnly = false;
      descriptionInput.readOnly = false; // Unlock description
      document.getElementById("podcastAssignmentDropdown").disabled = false; // Unlock podcast dropdown

      // Visual indication for unlocked fields
      nameInput.style.backgroundColor = "rgba(255, 111, 97, 0.05)";
      emailInput.style.backgroundColor = "rgba(255, 111, 97, 0.05)";
      descriptionInput.style.backgroundColor = "rgba(255, 111, 97, 0.05)"; // New visual cue
      nameInput.style.borderColor = "var(--highlight-color)";
      emailInput.style.borderColor = "var(--highlight-color)";
      descriptionInput.style.borderColor = "var(--highlight-color)"; // New visual cue

      // Enable save button and focus on name field
      document.getElementById("saveTeamBtn").disabled = false;
      nameInput.focus();
    };
  }

  const modal = document.getElementById("teamDetailModal");
  modal.classList.add("show");
  modal.setAttribute("aria-hidden", "false");

  // Handle podcast addition via dropdown
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

  // Handle removal of a podcast chip
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

  // Replace delete button handler with confirmation popup
  const deleteBtn = document.getElementById("deleteTeamDetailsBtn");
  deleteBtn.onclick = () => {
    showConfirmationPopup(
      "Delete Team",
      "Are you sure you want to delete this team? All members will be removed and this action cannot be undone.",
      async () => {
        try {
          const result = await deleteTeamRequest(team._id);
          showNotification(
            "Success",
            result.message || "Team deleted successfully!",
            "success"
          );
          const card = document.querySelector(
            `.team-card[data-id="${team._id}"]`
          );
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
      },
      () => {
        showNotification("Info", "Deletion canceled.", "info");
      }
    );
  };

  // Save button finalizes pending podcast assignment changes and updates team details
  const saveBtn = document.getElementById("saveTeamBtn");
  saveBtn.onclick = async () => {
    // First update all pending podcast assignments
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
      members: team.members // Preserve all members (including creator)
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

  // Modal close handler
  document.getElementById("teamDetailCloseBtn").onclick = () =>
    closeModal(modal);
  window.addEventListener("click", (event) => {
    if (event.target === modal) {
      closeModal(modal);
    }
  });
}

// Helper function to add individual edit buttons to fields
function addFieldEditButton(inputElement, fieldName) {
  // Create edit button
  const editButton = document.createElement("button");
  editButton.className = "field-edit-btn";
  editButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"></path>
  </svg>`;
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

    // Add visual indication that field is editable
    inputElement.style.backgroundColor = "rgba(255, 111, 97, 0.05)";
    inputElement.style.borderColor = "var(--highlight-color)";
  });

  // Create a wrapper if needed
  const parent = inputElement.parentNode;
  if (!parent.style.position) {
    parent.style.position = "relative";
  }

  // Insert the button next to the input
  parent.appendChild(editButton);
}
