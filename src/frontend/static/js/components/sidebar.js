// Se team.js + team.html för att se hur man använder sidebar.
// För nya ikoner lägg till de i side-bar-icons.js och importera de i din .js. se team.js för exempel.

export function initSidebar() {
  const sidebar = document.querySelector(".sidebar");
  const appContainer = document.querySelector(".app-container");
  const toggleSidebarBtn = document.getElementById("toggle-sidebar");

  if (!sidebar || !toggleSidebarBtn || !appContainer) {
    console.error("Sidebar or toggle button not found.");
    return;
  }

  console.log("Sidebar initialized successfully.");

  toggleSidebarBtn.addEventListener("click", () => {
    const collapsed = sidebar.classList.toggle("collapsed");
    appContainer.classList.toggle("sidebar-collapsed", collapsed);

    // Save state
    localStorage.setItem("sidebarCollapsed", collapsed);

    // Fire custom event
    document.dispatchEvent(new CustomEvent("sidebarToggled", { detail: { collapsed } }));

    // ✅ FIX: Ensure podcast list is shown when expanding the sidebar
    const podcastList = document.getElementById("podcast-list");
    if (podcastList && !collapsed) {
      podcastList.style.display = "flex"; // or "block" depending on layout
      console.log("Sidebar expanded – podcast list shown.");
    }
  });

  // Load state from localStorage
  const sidebarCollapsed = localStorage.getItem("sidebarCollapsed") === "true";
  if (sidebarCollapsed) {
    sidebar.classList.add("collapsed");
    appContainer.classList.add("sidebar-collapsed");
  }
}
