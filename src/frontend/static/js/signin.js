document.addEventListener("DOMContentLoaded", () => {
  const themeToggle = document.getElementById("theme-toggle");
  const body = document.body;
  const form = document.getElementById("login-form");
  const errorMessage = document.getElementById("error-message");
  const passwordInput = document.getElementById("password");
  const submitButton = form.querySelector('button[type="submit"]');
  const buttonText = submitButton.querySelector(".button-text");

  // Initialize Lucide icons
  const lucide = window.lucide; // Access lucide from the window object
  lucide.createIcons(); // Initialize icons on page load

  // Reset button state on page load
  buttonText.style.display = "inline";
  submitButton.disabled = false;

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

  // Form submission
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorMessage.style.display = "none";
    submitButton.disabled = true;

    const email = document.getElementById("email").value;
    const password = passwordInput.value;

    try {
      const response = await fetch("/signin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }) // No need to send remember
      });

      if (!response.ok) {
        throw new Error("Invalid email or password.");
      }

      const result = await response.json();
      if (result.redirect_url) {
        window.location.href = result.redirect_url;
      } else {
        window.location.href = "/dashboard";
      }
    } catch (error) {
      errorMessage.textContent = error.message;
      errorMessage.style.display = "block";
      submitButton.disabled = false;
    }
  });

  // Initialize Lucide icons
  lucide.createIcons();
});
