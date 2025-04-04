import { signin, sendVerificationCode, loginWithVerificationCode } from "/static/requests/authRequests.js";

document.addEventListener("DOMContentLoaded", function () {
  const urlParams = new URLSearchParams(window.location.search);
  const message = urlParams.get("message");
  const successMessage = document.getElementById("success-message");
  const errorMessage = document.getElementById("error-message");
  const form = document.getElementById("signin-form");
  const sendCodeButton = document.getElementById("send-code-button");
  const sendCodeMessage = document.getElementById("send-code-message");
  const loginWithCodeButton = document.getElementById("login-with-code-button");
  const loginWithCodeButtonVerification = document.getElementById("login-with-code-button-verification");
  const emailInput = document.getElementById("email");
  const verificationCodeInput = document.getElementById("verification-code-login");
  const verificationCodeInputVerification = document.getElementById("verification-code-verification");
  const loginForm = document.getElementById("login-form");
  const verificationForm = document.getElementById("verification-form");

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
  if (sendCodeButton) {
    sendCodeButton.addEventListener("click", async function () {
      const email = emailInput ? emailInput.value.trim() : "";

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

        // Show the verification form and hide the login form
        if (loginForm && verificationForm) {
          loginForm.style.display = "none";
          verificationForm.style.display = "block";
        }
      } catch (error) {
        console.error("Error:", error);
        sendCodeMessage.textContent = error.message || "An error occurred. Please try again.";
        sendCodeMessage.style.display = "block";
        sendCodeMessage.style.color = "red";
      }
    });
  } else {
    console.error("❌ ERROR: #send-code-button not found in the DOM.");
  }

  // Handle "Back to Login" button click
  const backToLoginButton = document.getElementById("back-to-login");
  if (backToLoginButton) {
    backToLoginButton.addEventListener("click", function () {
      // Show the login form and hide the verification form
      document.getElementById("verification-form").style.display = "none";
      document.getElementById("login-form").style.display = "block";
    });
  } else {
    console.error("❌ ERROR: #back-to-login not found in the DOM. Ensure the button exists in the HTML.");
  }

  // Handle "Login with Code" button click
  if (loginWithCodeButton) {
    loginWithCodeButton.addEventListener("click", async function () {
      const email = emailInput ? emailInput.value.trim() : "";
      const code = verificationCodeInput ? verificationCodeInput.value.trim() : "";

      if (!email || !code) {
        sendCodeMessage.textContent = "Please enter both email and verification code.";
        sendCodeMessage.style.display = "block";
        sendCodeMessage.style.color = "red";
        return;
      }

      try {
        const response = await loginWithVerificationCode(email, code);

        if (response.redirect_url) {
          sendCodeMessage.textContent = "Login successful!";
          sendCodeMessage.style.display = "block";
          sendCodeMessage.style.color = "green";
          window.location.href = response.redirect_url;
        } else {
          throw new Error("Failed to log in with code.");
        }
      } catch (error) {
        console.error("Error:", error);
        sendCodeMessage.textContent = error.message || "An error occurred. Please try again.";
        sendCodeMessage.style.display = "block";
        sendCodeMessage.style.color = "red";
      }
    });
  } else {
    console.error("❌ ERROR: #login-with-code-button not found in the DOM.");
  }

  // Handle "Login with Code Verification" button click
  if (loginWithCodeButtonVerification) {
    loginWithCodeButtonVerification.addEventListener("click", async function () {
      const code = verificationCodeInputVerification.value.trim();

      if (!email || !code) { // Use the existing 'email' variable
        sendCodeMessage.textContent = "Please enter both email and verification code.";
        sendCodeMessage.style.display = "block";
        sendCodeMessage.style.color = "red";
        return;
      }

      try {
        const response = await loginWithVerificationCode(email, code);

        if (response.redirect_url) {
          sendCodeMessage.textContent = "Login successful!";
          sendCodeMessage.style.display = "block";
          sendCodeMessage.style.color = "green";
          window.location.href = response.redirect_url;
        } else {
          throw new Error("Failed to log in with code.");
        }
      } catch (error) {
        console.error("Error:", error);
        sendCodeMessage.textContent = error.message || "An error occurred. Please try again.";
        sendCodeMessage.style.display = "block";
        sendCodeMessage.style.color = "red";
      }
    });
  } else {
    console.error("❌ ERROR: #login-with-code-button-verification not found in the DOM.");
  }
});