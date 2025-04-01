import { signin } from "/static/requests/authRequests.js";

document.addEventListener("DOMContentLoaded", function () {
  const urlParams = new URLSearchParams(window.location.search);
  const message = urlParams.get("message");
  const successMessage = document.getElementById("success-message");
  const errorMessage = document.getElementById("error-message");
  const form = document.getElementById("signin-form");
  const sendCodeButton = document.getElementById("send-code-button");
  const emailInput = document.getElementById("email");

  // Display success message if present in URL params
  if (message) {
    successMessage.textContent = message;
    successMessage.style.display = "block";
    successMessage.style.color = "var(--highlight)"; // Match error message color
  }

  // Ensure the form exists
  if (!form) {
    console.error("❌ ERROR: #signin-form not found in the DOM.");
    return;
  }

  // Handle "Sign In" form submission
  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const email = emailInput.value.trim();
    const password = document.getElementById("password").value.trim();

    if (!email || !password) {
      errorMessage.textContent = "Please enter both email and password.";
      errorMessage.style.display = "block";
      return;
    }

    try {
      const redirectUrl = await signin(email, password);
      window.location.href = redirectUrl;
    } catch (error) {
      errorMessage.textContent = error.message;
      errorMessage.style.display = "block";
    }
  });

  // Handle "Send Verification Code" button click
  if (sendCodeButton) {
    sendCodeButton.addEventListener("click", async function () {
      const email = emailInput.value.trim();

      if (!email) {
        errorMessage.textContent = "Please enter your email.";
        errorMessage.style.display = "block";
        return;
      }

      try {
        const response = await fetch("/send-verification-code", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        });

        const result = await response.json();
        if (response.ok) {
          successMessage.textContent = "Verification code sent to your email!";
          successMessage.style.display = "block";
          errorMessage.style.display = "none";
        } else {
          errorMessage.textContent =
            result.error || "Failed to send verification code.";
          errorMessage.style.display = "block";
          successMessage.style.display = "none";
        }
      } catch (error) {
        console.error("Error:", error);
        errorMessage.textContent = "An error occurred. Please try again.";
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
      }
    });
  }
});