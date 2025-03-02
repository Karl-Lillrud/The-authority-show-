document.addEventListener("DOMContentLoaded", () => {
  const body = document.body;

  // Initialize Lucide icons
  const lucide = window.lucide; // Access lucide from the window object

  // Set dark mode on page load
  body.classList.add("dark-mode");

  // Initialize Lucide icons
  lucide.createIcons();
});
