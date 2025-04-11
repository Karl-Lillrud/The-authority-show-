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
        return;
      }

      try {
        const response = await fetch("/send-login-link", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
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
        console.error("Error:", error);
        errorMessage.textContent = "An error occurred. Please try again.";
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
      }
    });
  }

  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get("token");

  if (token) {
    // Automatically log in the user using the token
    fetch("/verify-login-token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.redirect_url) {
          window.location.href = data.redirect_url;
        } else {
          alert(data.error || "Failed to log in with the provided link.");
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        alert("An error occurred. Please try again.");
      });
  }

  const form = document.getElementById("login-form");
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
      const response = await signin(email, password);
      window.location.href = response.redirect_url || "/dashboard"; // Redirect to dashboard
    } catch (error) {
      errorMessage.textContent = error.message;
      errorMessage.style.display = "block";
    }
  });
});