// Se team.js + team.html för att se hur man använder sidebar.
// För nya ikoner lägg till de i side-bar-icons.js och importera de i din .js. se team.js för exempel.

export function initSidebar() {
  const sidebar = document.querySelector(".sidebar");
  if (!sidebar) {
    console.error("Sidebar element not found."); // Debugging log
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
}
