import { sidebarIcons } from "../components/sidebar-icons.js";
import { switchToTeamsView, switchToMembersView } from "./team.js"; // Import view-switching functions

const sidebarHTML = `
<aside class="sidebar">
  <div class="sidebar-header">
    <!-- ...existing header code... -->
  </div>
  <div class="sidebar-content">
    <nav class="sidebar-menu">
      <ul>
        <li class="sidebar-menu-item">
          <a href="/dashboard" class="sidebar-menu-link dashboard-link">
            <span id="back-to-dashboard-icon" class="sidebar-icon"></span>
            <span>Back to Dashboard</span>
          </a>
        </li>
        <li id="sidebar-teams" class="sidebar-menu-item">
          <a href="#" class="sidebar-menu-link">
            <span id="teams-icon" class="sidebar-icon"></span>
            <span>Teams</span>
          </a>
        </li>
        <li id="sidebar-members" class="sidebar-menu-item">
          <a href="#" class="sidebar-menu-link">
            <span id="members-icon" class="sidebar-icon"></span>
            <span>Members</span>
          </a>
        </li>
      </ul>
    </nav>
    <div class="sidebar-action-buttons">
      <h3>Actions</h3>
      <button id="openModalBtn" class="sidebar-action-button">
        <span class="sidebar-icon"></span>
        <span>Add New Team</span>
      </button>
      <button id="addNewMemberBtn" class="sidebar-action-button">
        <span class="sidebar-icon"></span>
        <span>Add New Member</span>
      </button>
    </div>
  </div>
  <div class="sidebar-footer">
    <div class="sidebar-actions">
      <button id="toggle-sidebar" class="sidebar-toggle">
        ${sidebarIcons.toggleSidebar}
      </button>
    </div>
  </div>
</aside>
`;

export function initSidebar() {
  let sidebar = document.querySelector(".sidebar");
  if (!sidebar) {
    const container = document.getElementById("sidebar-container");
    if (container) {
      console.log("Rendering sidebar..."); // Debugging log
      container.innerHTML = sidebarHTML;
      sidebar = container.querySelector(".sidebar");
    } else {
      console.error("Sidebar container not found."); // Debugging log
    }
  }

  if (!sidebar) {
    console.error("Sidebar initialization failed."); // Debugging log
    return;
  }

  console.log("Sidebar initialized successfully."); // Debugging log

  const toggleSidebarBtn = document.getElementById("toggle-sidebar");
  if (toggleSidebarBtn) {
    toggleSidebarBtn.addEventListener("click", () => {
      sidebar.classList.toggle("collapsed");
      localStorage.setItem(
        "sidebarCollapsed",
        sidebar.classList.contains("collapsed")
      );
    });
  }

  const sidebarCollapsed = localStorage.getItem("sidebarCollapsed") === "true";
  if (sidebarCollapsed) {
    sidebar.classList.add("collapsed");
  }

  initSidebarIcons();

  const teamsMenuItem = document.getElementById("sidebar-teams");
  const membersMenuItem = document.getElementById("sidebar-members");

  if (teamsMenuItem && membersMenuItem) {
    teamsMenuItem.addEventListener("click", (event) => {
      event.preventDefault();
      membersMenuItem.classList.remove("active");
      teamsMenuItem.classList.add("active");
      switchToTeamsView(); // Delegate to team.js
    });

    membersMenuItem.addEventListener("click", (event) => {
      event.preventDefault();
      teamsMenuItem.classList.remove("active");
      membersMenuItem.classList.add("active");
      switchToMembersView(); // Delegate to team.js
    });
  }
}

function initSidebarIcons() {
  const backToDashboardIcon = document.getElementById("back-to-dashboard-icon");
  const teamsIcon = document.getElementById("teams-icon");
  const membersIcon = document.getElementById("members-icon");

  if (backToDashboardIcon)
    backToDashboardIcon.innerHTML = sidebarIcons.backToDashboard;
  if (teamsIcon) teamsIcon.innerHTML = sidebarIcons.teams;
  if (membersIcon) membersIcon.innerHTML = sidebarIcons.members;
}
