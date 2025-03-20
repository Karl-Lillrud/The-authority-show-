// Shared SVG icons for sidebar components
import { sidebarIcons } from "./sidebar-icons.js";

// New constant holding the sidebar HTML markup
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
        <li class="sidebar-menu-item active">
          <a href="#" class="sidebar-menu-link">
            <span id="teams-icon" class="sidebar-icon"></span>
            <span>Teams</span>
          </a>
        </li>
        <!-- Removed Podcasts menu item -->
        <li class="sidebar-menu-item">
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
        <!-- Optionally include toggle icon markup -->
        ${sidebarIcons.toggleSidebar}
      </button>
    </div>
  </div>
</aside>
`;

export function initSidebar() {
  let sidebar = document.querySelector(".sidebar");
  if (!sidebar) {
    // Render sidebar into the container (if available)
    const container = document.getElementById("sidebar-container");
    if (container) {
      container.innerHTML = sidebarHTML;
      sidebar = container.querySelector(".sidebar");
    }
  }

  if (!sidebar) {
    console.error("Sidebar container not found.");
    return;
  }

  // Toggle sidebar functionality using the rendered sidebar
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

  // Load saved sidebar state
  const sidebarCollapsed = localStorage.getItem("sidebarCollapsed") === "true";
  if (sidebarCollapsed) {
    sidebar.classList.add("collapsed");
  }

  // Initialize sidebar icons
  initSidebarIcons();
}

function initSidebarIcons() {
  // Set navigation icons
  const backToDashboardIcon = document.getElementById("back-to-dashboard-icon");
  const teamsIcon = document.getElementById("teams-icon");
  const membersIcon = document.getElementById("members-icon");
  // Set toggle sidebar icon is already set via sidebarHTML using sidebarIcons.toggleSidebar

  if (backToDashboardIcon)
    backToDashboardIcon.innerHTML = sidebarIcons.backToDashboard;
  if (teamsIcon) teamsIcon.innerHTML = sidebarIcons.teams;
  if (membersIcon) membersIcon.innerHTML = sidebarIcons.members;
  // ...existing icon initializations if needed...
}
