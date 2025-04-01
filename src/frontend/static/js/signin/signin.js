import { signin, sendVerificationCode } from "/static/requests/authRequests.js";

document.addEventListener("DOMContentLoaded", function () {
  const urlParams = new URLSearchParams(window.location.search);
  const message = urlParams.get("message");
  const successMessage = document.getElementById("success-message");
  const errorMessage = document.getElementById("error-message");
  const form = document.getElementById("signin-form");
  const sendCodeButton = document.getElementById("send-code-button");
  const sendCodeMessage = document.getElementById("send-code-message");
  const loginWithCodeButton = document.getElementById("login-with-code-button");
  const emailInput = document.getElementById("email");
  const verificationCodeInput = document.getElementById("verification-code");

  // Display success message if present in URL params
  if (message) {
    successMessage.textContent = message;
    successMessage.style.display = "block";
    successMessage.style.color = "var(--highlight)";
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

  // Handle "Sign in with Verification Code" button click
  sendCodeButton.addEventListener("click", async function () {
    const email = emailInput.value.trim();

    if (!email) {
      sendCodeMessage.textContent = "Please enter your email.";
      sendCodeMessage.style.display = "block";
      sendCodeMessage.style.color = "red";
      return;
    }

    try {
      const result = await sendVerificationCode(email);
      sendCodeMessage.textContent = "Verification code sent successfully.";
      sendCodeMessage.style.display = "block";
      sendCodeMessage.style.color = "green";
      verificationCodeInput.style.display = "block";
      loginWithCodeButton.style.display = "block";
    } catch (error) {
      console.error("Error:", error);
      sendCodeMessage.textContent = error.message || "An error occurred. Please try again.";
      sendCodeMessage.style.display = "block";
      sendCodeMessage.style.color = "red";
    }
  });

  // Handle "Login with Code" button click
  loginWithCodeButton.addEventListener("click", async function () {
    const email = emailInput.value.trim();
    const code = verificationCodeInput.value.trim();

    if (!email || !code) {
      sendCodeMessage.textContent = "Please enter both email and verification code.";
      sendCodeMessage.style.display = "block";
      sendCodeMessage.style.color = "red";
      return;
    }

    try {
      const response = await fetch("/login-with-code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, code }),
      });

      const result = await response.json();
      if (response.ok) {
        sendCodeMessage.textContent = "Login successful!";
        sendCodeMessage.style.display = "block";
        sendCodeMessage.style.color = "green";
        window.location.href = result.redirect_url || "/dashboard";
      } else {
        sendCodeMessage.textContent = result.message || "Failed to log in with code.";
        sendCodeMessage.style.display = "block";
        sendCodeMessage.style.color = "red";
      }
    } catch (error) {
      console.error("Error:", error);
      sendCodeMessage.textContent = "An error occurred. Please try again.";
      sendCodeMessage.style.display = "block";
      sendCodeMessage.style.color = "red";
    }
  });
});