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

  const signinWithCodeButton = document.getElementById("signin-with-code-button");
  const signinContainer = document.getElementById("signin-container");
  const verificationCodeContainer = document.getElementById("verification-code-container");
  const verificationCodeGroup = document.getElementById("verification-code-group");
  const verificationCodeForm = document.getElementById("verification-code-form");

  if (signinWithCodeButton) {
    signinWithCodeButton.addEventListener("click", function () {
      signinContainer.style.display = "none";
      verificationCodeContainer.style.display = "block";
    });
  }

  verificationCodeForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    const email = document.getElementById("verification-email").value.trim();
    const codeInput = document.getElementById("verification-code");
    const code = codeInput ? codeInput.value.trim() : null;

    if (!email) {
      alert("Please enter your email.");
      return;
    }

    if (!code) {
      // If no code is entered, send the verification code
      try {
        const response = await fetch("/send-verification-code", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        });

        const result = await response.json();
        if (response.ok) {
          alert("Verification code sent to your email!");
          verificationCodeGroup.style.display = "block";
        } else {
          alert(result.error || "Failed to send verification code.");
        }
      } catch (error) {
        console.error("Error:", error);
        alert("An error occurred. Please try again.");
      }
    } else {
      // If code is entered, verify and sign in
      try {
        const response = await fetch("/verify-and-signin", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, code }),
        });

        const result = await response.json();
        if (response.ok) {
          window.location.href = result.redirect_url || "/";
        } else {
          alert(result.error || "Verification failed.");
        }
      } catch (error) {
        console.error("Error:", error);
        alert("An error occurred. Please try again.");
      }
    }
  });
});