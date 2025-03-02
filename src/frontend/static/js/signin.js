document.addEventListener("DOMContentLoaded", () => {
  const themeToggle = document.getElementById("theme-toggle");
  const body = document.body;
  const passwordInput = document.getElementById("password");
  const togglePassword = document.getElementById("toggle-password");

  // Initialize Lucide icons
  const lucide = window.lucide; // Access lucide from the window object

  // Theme toggle
  themeToggle.addEventListener("click", () => {
    body.classList.toggle("dark-mode");
    const icon = themeToggle.querySelector("i");
    if (body.classList.contains("dark-mode")) {
      icon.setAttribute("data-lucide", "sun");
    } else {
      icon.setAttribute("data-lucide", "moon");
    }
    lucide.createIcons();
  });

  // Password visibility toggle
  togglePassword.addEventListener("click", () => {
    const type =
      passwordInput.getAttribute("type") === "password" ? "text" : "password";
    passwordInput.setAttribute("type", type);
    const icon = togglePassword.querySelector("i");
    icon.setAttribute("data-lucide", type === "password" ? "eye" : "eye-off");
    lucide.createIcons();
  });

  // Initialize Lucide icons
  lucide.createIcons();
});
