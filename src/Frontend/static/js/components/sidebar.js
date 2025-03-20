// Sidebar component functionality
import { sidebarIcons } from "./sidebar-icons.js";

export function initSidebar() {
  // Initialize sidebar toggle functionality
  const sidebar = document.querySelector(".sidebar");
  const toggleSidebarBtn = document.getElementById("toggle-sidebar");

  if (toggleSidebarBtn) {
    toggleSidebarBtn.addEventListener("click", () => {
      sidebar.classList.toggle("collapsed");

      // Save sidebar state to localStorage
      localStorage.setItem(
        "sidebarCollapsed",
        sidebar.classList.contains("collapsed")
      );
    });
  }

  // Load sidebar state from localStorage
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
  const podcastsIcon = document.getElementById("podcasts-icon");
  const episodesIcon = document.getElementById("episodes-icon");
  const guestsIcon = document.getElementById("guests-icon");
  const teamsIcon = document.getElementById("teams-icon");

  // Set toggle sidebar icon
  const toggleSidebarIcon = document.getElementById("toggle-sidebar-icon");

  // Set action button icons
  const addPodcastIcon = document.getElementById("add-icon-podcast");
  const addEpisodeIcon = document.getElementById("add-icon-episode");
  const addGuestIcon = document.getElementById("add-icon-guest");

  // Set icons if elements exist
  if (backToDashboardIcon)
    backToDashboardIcon.innerHTML = sidebarIcons.backToDashboard;
  if (podcastsIcon) podcastsIcon.innerHTML = sidebarIcons.podcasts;
  if (episodesIcon) episodesIcon.innerHTML = sidebarIcons.episodes;
  if (guestsIcon) guestsIcon.innerHTML = sidebarIcons.guests;
  if (teamsIcon) teamsIcon.innerHTML = sidebarIcons.teams;

  if (toggleSidebarIcon)
    toggleSidebarIcon.innerHTML = sidebarIcons.toggleSidebar;

  if (addPodcastIcon) addPodcastIcon.innerHTML = sidebarIcons.add;
  if (addEpisodeIcon) addEpisodeIcon.innerHTML = sidebarIcons.add;
  if (addGuestIcon) addGuestIcon.innerHTML = sidebarIcons.add;
}
