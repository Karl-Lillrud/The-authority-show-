document.addEventListener("DOMContentLoaded", () => {
  // Tab switching functionality
  const tabItems = document.querySelectorAll(".tab-item");
  const tabContents = document.querySelectorAll(".tab-content");

  tabItems.forEach((item) => {
    item.addEventListener("click", function () {
      // Remove active class from all tabs
      tabItems.forEach((tab) => tab.classList.remove("active"));
      tabContents.forEach((content) => content.classList.remove("active"));

      // Add active class to current tab
      this.classList.add("active");
      const tabId = this.getAttribute("data-tab") + "-tab";
      document.getElementById(tabId).classList.add("active");

      // Clear error messages when switching tabs
      document.getElementById("error-message").style.display = "none";
      document.getElementById("success-message").style.display = "none";
    });
  });

  // Get API base URL from the HTML template
  const API_BASE_URL = document.body.getAttribute("data-api-base-url");

  // Login form submission
  const loginForm = document.getElementById("login-form");
  const errorMessage = document.getElementById("error-message");

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
      const response = await fetch(`${API_BASE_URL}/signin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        throw new Error("Invalid email or password.");
      }

      const result = await response.json();
      if (result.redirect_url) {
        window.location.href = result.redirect_url;
      } else {
        window.location.href = "/";
      }
    } catch (error) {
      errorMessage.textContent = error.message;
      errorMessage.style.display = "block";
    }
  });

  // Register form submission
  const registerForm = document.getElementById("register-form");
  const successModal = document.getElementById("success-modal");
  const successOkButton = document.getElementById("success-ok-button");
  const successMessage = document.getElementById("success-message");

  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("reg-email").value;
    const password = document.getElementById("reg-password").value;

    try {
      const response = await fetch(`${API_BASE_URL}/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ email, password })
      });

      if (response.ok) {
        // Show success modal
        successMessage.textContent = "Registration successful! Please sign in.";
        successMessage.style.display = "block";

        // Clear form
        registerForm.reset();

        // Switch to login tab
        tabItems.forEach((tab) => tab.classList.remove("active"));
        tabContents.forEach((content) => content.classList.remove("active"));

        document.querySelector('[data-tab="signin"]').classList.add("active");
        document.getElementById("signin-tab").classList.add("active");

        // Focus on email field and pre-fill with registered email
        document.getElementById("email").value = email;
        document.getElementById("email").focus();
      } else {
        const result = await response.json();
        errorMessage.textContent =
          result.error || "An error occurred. Please try again.";
        errorMessage.style.display = "block";
      }
    } catch (error) {
      console.error("Error:", error);
      errorMessage.textContent = "Something went wrong. Please try again.";
      errorMessage.style.display = "block";
    }
  });
});
