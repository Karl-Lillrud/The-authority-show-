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

// Error handling wrapper function
async function safeApiCall(apiFunction, errorMessage) {
  try {
    return await apiFunction();
  } catch (error) {
    console.error(`${errorMessage}:`, error);
    showNotification("Error", `${errorMessage}. ${error.message}`, "error");
    return null;
  }
}

// Initialize the page
document.addEventListener("DOMContentLoaded", async () => {
  // Initialize sidebar
  initSidebar();
  initSidebarIcons();

  // Fetch teams data with improved error handling
  const teams = await safeApiCall(
    getTeamsRequest,
    "Failed to fetch teams data"
  );
  if (teams) {
    updateTeamsUI(teams);
  }

  // Initialize search functionality
  const searchInput = document.getElementById("teamSearch");
  const clearSearchBtn = document.getElementById("clearSearch");
  
  if (searchInput && clearSearchBtn) {
    searchInput.addEventListener("input", () => {
      const searchTerm = searchInput.value.toLowerCase();
      const teamCards = document.querySelectorAll(".team-card");
      
      teamCards.forEach(card => {
        const teamName = card.querySelector("h2").textContent.toLowerCase();
        const teamDescription = card.querySelector(".description-text")?.textContent.toLowerCase() || "";
        
        if (teamName.includes(searchTerm) || teamDescription.includes(searchTerm)) {
          card.style.display = "flex";
        } else {
          card.style.display = "none";
        }
      });
      
      // Show/hide clear button
      clearSearchBtn.style.display = searchInput.value ? "flex" : "none";
    });
    
    clearSearchBtn.addEventListener("click", () => {
      searchInput.value = "";
      const teamCards = document.querySelectorAll(".team-card");
      teamCards.forEach(card => {
        card.style.display = "flex";
      });
      clearSearchBtn.style.display = "none";
    });
    
    // Initially hide clear button
    clearSearchBtn.style.display = "none";
  }

  // Initialize podcast dropdown with improved error handling
  async function populatePodcastDropdown() {
    const podcastDropdown = document.getElementById("podcastDropdown");
    if (podcastDropdown) {
      const podcasts = await safeApiCall(
        fetchPodcasts,
        "Failed to fetch podcasts"
      );
      if (podcasts) {
        podcasts.forEach((podcast) => {
          const option = document.createElement("option");
          option.value = podcast._id;
          option.textContent = podcast.podName;
          podcastDropdown.appendChild(option);
        });
      }
    }
  }
  populatePodcastDropdown();

  // Setup Add Team Modal
  const addTeamModal = document.getElementById("addTeamModal");
  const addTeamForm = addTeamModal
    ? addTeamModal.querySelector("form")
    : document.querySelector("form");
  const teamFormValidation = document.getElementById("teamFormValidation");

  if (addTeamForm) {
    addTeamForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(addTeamForm);

      // Form validation
      const name = formData.get("name");
      const email = formData.get("email");
      
      if (!name || !email) {
        if (teamFormValidation) {
          teamFormValidation.textContent = "Team name and email are required";
          teamFormValidation.classList.add("show");
        } else {
          showNotification("Error", "Team name and email are required", "error");
        }
        return;
      }
      
      if (!email.includes('@')) {
        if (teamFormValidation) {
          teamFormValidation.textContent = "Please enter a valid email address";
          teamFormValidation.classList.add("show");
        } else {
          showNotification("Error", "Please enter a valid email address", "error");
        }
        return;
      }

      // Hide validation message if validation passes
      if (teamFormValidation) {
        teamFormValidation.classList.remove("show");
      }

      // Extract the selected podcast ID from the form
      const podcastId = formData.get("podcastId");
      const payload = {
        name: name,
        email: email,
        description: formData.get("description"),
        members: [] // Members is empty as it's not used here
      };

      try {
        // Show loading indicator
        window.showLoading && window.showLoading();
        
        // Show loading notification
        showNotification("Processing", "Creating team...", "info");
        
        const response = await addTeam(payload);
        console.log("Add team response:", response);
        const teamId = response.team_id;

        // If a podcast was selected, update it with the new team ID
        if (podcastId) {
          const { updatePodcastTeam } = await import("./teamOperations.js");
          const updateResponse = await updatePodcastTeam(podcastId, teamId);
          console.log("Podcast updated with teamId:", updateResponse);
        }
        
        // Reset form
        addTeamForm.reset();
        
        closeModal(addTeamModal);
        const teams = await getTeamsRequest();
        updateTeamsUI(teams);
      } catch (error) {
        console.error("Error adding team:", error);
        showNotification("Error", `Failed to create team: ${error.message}`, "error");
      } finally {
        // Hide loading indicator
        window.hideLoading && window.hideLoading();
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
        // Reset form before opening
        if (addTeamForm) {
          addTeamForm.reset();
          
          // Clear validation message
          if (teamFormValidation) {
            teamFormValidation.classList.remove("show");
          }
        }
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
  const memberEmail = document.getElementById("memberEmail");
  const memberRole = document.getElementById("memberRole");
  const memberFormValidation = document.getElementById("memberFormValidation");

  // Function to fetch teams and populate dropdown with improved error handling
  async function populateTeamDropdown() {
    try {
      const teams = await safeApiCall(
        getTeamsRequest,
        "Failed to fetch teams for dropdown"
      );
      if (teams) {
        teamSelect.innerHTML = '<option value="">Select a Team</option>';
        teams.forEach((team) => {
          const option = document.createElement("option");
          option.value = team._id;
          option.textContent = team.name;
          teamSelect.appendChild(option);
        });
      }
    } catch (err) {
      console.error("Error fetching teams for dropdown:", err);
    }
  }

  // Open modal on Add New Member button click
  if (addMemberBtnSidebar && addMemberModal) {
    addMemberBtnSidebar.addEventListener("click", () => {
      populateTeamDropdown();
      // Reset form
      if (addMemberForm) {
        addMemberForm.reset();
        
        // Clear validation message
        if (memberFormValidation) {
          memberFormValidation.classList.remove("show");
        }
      }
      addMemberModal.classList.add("show");
      addMemberModal.setAttribute("aria-hidden", "false");
      
      // Focus on the first input field for better UX
      if (memberEmail) {
        setTimeout(() => memberEmail.focus(), 100);
      }
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

  // Add form validation before submission
  if (addMemberForm) {
    // Remove any previously registered event handlers
    addMemberForm.removeEventListener("submit", handleAddMemberFormSubmission);
    
    // Add custom validation
    addMemberForm.addEventListener("submit", (event) => {
      event.preventDefault();
      
      // Validate email
      if (!memberEmail.value || !memberEmail.value.includes('@')) {
        if (memberFormValidation) {
          memberFormValidation.textContent = "Please enter a valid email address";
          memberFormValidation.classList.add("show");
        } else {
          showNotification("Error", "Please enter a valid email address", "error");
        }
        memberEmail.focus();
        return;
      }
      
      // Validate team selection
      if (!teamSelect.value) {
        if (memberFormValidation) {
          memberFormValidation.textContent = "Please select a team";
          memberFormValidation.classList.add("show");
        } else {
          showNotification("Error", "Please select a team", "error");
        }
        teamSelect.focus();
        return;
      }
      
      // Validate role selection
      if (!memberRole.value) {
        if (memberFormValidation) {
          memberFormValidation.textContent = "Please select a role";
          memberFormValidation.classList.add("show");
        } else {
          showNotification("Error", "Please select a role", "error");
        }
        memberRole.focus();
        return;
      }
      
      // Hide validation message if validation passes
      if (memberFormValidation) {
        memberFormValidation.classList.remove("show");
      }
      
      // If validation passes, proceed with submission
      handleAddMemberFormSubmission(event);
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
  
  // Add loading indicator
  const mainContent = document.querySelector('.main-content');
  if (mainContent) {
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'loading-indicator';
    loadingIndicator.innerHTML = '<div class="spinner"></div><p>Loading...</p>';
    loadingIndicator.style.display = 'none';
    mainContent.appendChild(loadingIndicator);
    
    // Show loading indicator when making API calls
    window.showLoading = function() {
      loadingIndicator.style.display = 'flex';
    };
    
    window.hideLoading = function() {
      loadingIndicator.style.display = 'none';
    };
  }
  
  // Edit Member Modal validation
  const editMemberForm = document.getElementById("editMemberForm");
  const editMemberFormValidation = document.getElementById("editMemberFormValidation");
  const editMemberEmail = document.getElementById("editMemberEmail");
  const editMemberRole = document.getElementById("editMemberRole");
  const saveEditMemberBtn = document.getElementById("saveEditMemberBtn");
  
  if (saveEditMemberBtn && editMemberFormValidation) {
    saveEditMemberBtn.addEventListener("click", () => {
      // Validate email
      if (!editMemberEmail.value || !editMemberEmail.value.includes('@')) {
        editMemberFormValidation.textContent = "Please enter a valid email address";
        editMemberFormValidation.classList.add("show");
        editMemberEmail.focus();
        return;
      }
      
      // Validate role selection
      if (editMemberRole && !editMemberRole.value) {
        editMemberFormValidation.textContent = "Please select a role";
        editMemberFormValidation.classList.add("show");
        editMemberRole.focus();
        return;
      }
      
      // Hide validation message if validation passes
      editMemberFormValidation.classList.remove("show");
      
      // Continue with the original save functionality
      // This assumes there's an existing event handler for this button
    });
  }
});
