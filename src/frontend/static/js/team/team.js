import { initSidebar } from "../components/sidebar.js";
import { sidebarIcons } from "../components/sidebar-icons.js";
import {
  getTeamsRequest,
  fetchPodcasts
} from "/static/requests/teamRequests.js";
import { updateTeamsUI, switchToTeamsView } from "./teamUI.js";
import {
  switchToMembersView,
  handleAddMemberFormSubmission
} from "./memberUI.js";
import { closeModal } from "./modals.js";
import { showNotification } from "../components/notifications.js";
import { addTeam } from "./teamOperations.js";

// Initialize sidebar icons
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

// Initialize the page
document.addEventListener("DOMContentLoaded", async () => {
  // Initialize sidebar
  initSidebar();
  initSidebarIcons();

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
        members: [] // Members is empty as it's not used here
      };

      try {
        const response = await addTeam(payload);
        console.log("Add team response:", response);
        const teamId = response.team_id;

        // If a podcast was selected, update it with the new team ID
        if (podcastId) {
          const { updatePodcastTeam } = await import("./teamOperations.js");
          const updateResponse = await updatePodcastTeam(podcastId, teamId);
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

  // Handle Add Member form submission
  if (addMemberForm) {
    // Remove any previously registered event handlers
    addMemberForm.removeEventListener("submit", handleAddMemberFormSubmission);
    // Add the event handler
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
