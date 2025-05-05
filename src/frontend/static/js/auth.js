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
  
    const errorMessage = document.getElementById("error-message");
  
    // Login form submission
    const loginForm = document.getElementById("login-form");
  
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();
  
      const email = document.getElementById("email").value;
  
      try {
        const response = await fetch(`${API_BASE_URL}/signin`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email })
        });
  
        if (!response.ok) {
          throw new Error("Invalid email");
        }
  
        const result = await response.json();
        if (result.redirect_url) {
          window.location.href = result.redirect_url;
        } else {
          window.location.href = "/podprofile"; // Redirect to podprofile
        }
      } catch (error) {
        errorMessage.textContent = error.message;
        errorMessage.style.display = "block";
      }
    });
  });