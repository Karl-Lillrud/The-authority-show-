document.addEventListener("DOMContentLoaded", function () {
  const successMessage = document.getElementById("success-message");
  const errorMessage = document.getElementById("error-message");
  const sendLoginLinkButton = document.getElementById("send-login-link-button");
  const emailInput = document.getElementById("email");

  // Handle "Send Log-In Link" button click
  if (sendLoginLinkButton) {
    sendLoginLinkButton.addEventListener("click", async function () {
      const email = emailInput.value.trim();

      if (!email) {
        errorMessage.textContent = "Please enter your email address.";
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
        return;
      }

      try {
        const response = await fetch("/send-login-link", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email })
        });

        const result = await response.json();
        if (response.ok) {
          successMessage.textContent = "A login link has been sent to your email!";
          successMessage.style.display = "block";
          errorMessage.style.display = "none";
        } else {
          errorMessage.textContent =
            result.error ||
            "Failed to send login link. Please try again later.";
          errorMessage.style.display = "block";
          successMessage.style.display = "none";
        }
      } catch (error) {
        console.error("Error sending login link:", error);
        errorMessage.textContent =
          "An unexpected error occurred while sending the login link. Please try again later.";
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
      }
    });
  } else {
    console.warn("Login link button was not found in the DOM");
  }

  // Handle token-based login from URL
  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get("token");

  if (token) {
    // Automatically log in the user using the token
    fetch("/verify-login-token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token })
    })
      .then(async (response) => {
        if (!response.ok) {
          const result = await response.json();
          throw new Error(
            `HTTP error! Status: ${response.status}, Message: ${
              result.error || "Unknown error"
            }`
          );
        }
        return response.json();
      })
      .then((data) => {
        if (data.redirect_url) {
          window.location.href = data.redirect_url;
        } else {
          errorMessage.textContent =
            data.error || "Failed to log in using the provided link.";
          errorMessage.style.display = "block";
          successMessage.style.display = "none";
        }
      })
      .catch((error) => {
        console.error("Error verifying token:", error);
        const errorMsg = error.message.toLowerCase();
        if (errorMsg.includes("failed to create account")) {
          errorMessage.textContent =
            "Failed to create account. Please verify your email or contact support.";
        } else if (errorMsg.includes("token has expired")) {
          errorMessage.textContent =
            "The login link has expired. Please request a new one.";
        } else if (errorMsg.includes("invalid token")) {
          errorMessage.textContent =
            "The login link is invalid. Try a new link.";
        } else {
          errorMessage.textContent =
            "An error occurred during login. Please try again or contact support.";
        }
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
      });
  }

  // Handle email/password login form (if used)
  const form = document.getElementById("signin-form");
  if (form) {
    form.addEventListener("submit", async function (event) {
      event.preventDefault();

      const email = emailInput.value.trim();
      const password = document.getElementById("password")?.value?.trim();

      if (!email || (password !== undefined && !password)) {
        errorMessage.textContent = "Please enter both email and password.";
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
        return;
      }

      try {
        const response = await fetch("/signin", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password })
        });

        const result = await response.json();
        if (response.ok) {
          window.location.href = result.redirect_url || "/podprofile";
        } else {
          errorMessage.textContent =
            result.error || "Login failed. Please try again.";
          errorMessage.style.display = "block";
          successMessage.style.display = "none";
        }
      } catch (error) {
        console.error("Error during login:", error);
        errorMessage.textContent = "An error occurred. Please try again.";
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
      }
    });
  } else {
    console.warn("Login form was not found in the DOM");
  }
});
