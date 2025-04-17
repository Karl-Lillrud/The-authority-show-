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
        errorMessage.textContent = "Please enter your email.";
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
          successMessage.textContent = "Log-in link sent to your email!";
          successMessage.style.display = "block";
          errorMessage.style.display = "none";
        } else {
          errorMessage.textContent =
            result.error || "Failed to send log-in link.";
          errorMessage.style.display = "block";
          successMessage.style.display = "none";
        }
      } catch (error) {
        console.error("Error sending login link:", error);
        errorMessage.textContent = "An error occurred. Please try again.";
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
      }
    });
  } else {
    console.warn("Send login link button not found in DOM");
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
          const text = await response.text();
          throw new Error(
            `HTTP error! Status: ${response.status}, Response: ${text}`
          );
        }
        return response.json();
      })
      .then((data) => {
        if (data.redirect_url) {
          window.location.href = data.redirect_url;
        } else {
          errorMessage.textContent =
            data.error || "Failed to log in with the provided link.";
          errorMessage.style.display = "block";
          successMessage.style.display = "none";
        }
      })
      .catch((error) => {
        console.error("Error verifying token:", error);
        errorMessage.textContent =
          "An error occurred during login. Please try again.";
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
            result.error || "Failed to sign in. Please try again.";
          errorMessage.style.display = "block";
          successMessage.style.display = "none";
        }
      } catch (error) {
        console.error("Error during sign-in:", error);
        errorMessage.textContent = "An error occurred. Please try again.";
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
      }
    });
  } else {
    console.warn("Sign-in form not found in DOM");
  }
});
