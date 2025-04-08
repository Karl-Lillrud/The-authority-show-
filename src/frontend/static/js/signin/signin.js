import { signin, sendVerificationCode, loginWithVerificationCode } from "/static/requests/authRequests.js";

document.addEventListener("DOMContentLoaded", function () {
  const urlParams = new URLSearchParams(window.location.search);
  const message = urlParams.get("message");
<<<<<<< HEAD
  const showVerificationCode = urlParams.get("showVerificationCode") === "true"; // Check if the verification code section should be shown
=======
>>>>>>> parent of 295f9066f (Implement email verification feature with code generation and validation)
  const successMessage = document.getElementById("success-message");
  const errorMessage = document.getElementById("error-message");
  const form = document.getElementById("signin-form");
  const sendCodeButton = document.getElementById("send-code-button");
  const sendCodeMessage = document.getElementById("send-code-message");
  const loginWithCodeButton = document.getElementById("login-with-code-button");
<<<<<<< HEAD
  const emailInput = document.getElementById("email");
  const verificationForm = document.getElementById("verification-form");
  const verificationCodeInput = document.getElementById("verification-code");
  const backToLoginButton = document.getElementById("back-to-login");
=======
  const loginWithCodeButtonVerification = document.getElementById("login-with-code-button-verification");
  const emailInput = document.getElementById("email");
  const verificationCodeInput = document.getElementById("verification-code");
  const verificationCodeInputVerification = document.getElementById("verification-code-verification");
>>>>>>> parent of 295f9066f (Implement email verification feature with code generation and validation)

  // Display success message if present in URL params
  if (message) {
    successMessage.textContent = message;
    successMessage.style.display = "block";
    successMessage.style.color = "var(--highlight)";
  }

<<<<<<< HEAD
  // Redirect to verification code section if specified in URL params
  if (showVerificationCode) {
    form.style.display = "none"; // Hide the login form
    verificationForm.style.display = "flex"; // Show the verification form
=======
  // Ensure the form exists
  if (!form) {
    console.error("❌ ERROR: #signin-form not found in the DOM.");
    return;
>>>>>>> parent of 295f9066f (Implement email verification feature with code generation and validation)
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
<<<<<<< HEAD
=======

      // Handle success response
>>>>>>> parent of 295f9066f (Implement email verification feature with code generation and validation)
      sendCodeMessage.textContent = "Verification code sent successfully.";
      sendCodeMessage.style.display = "block";
      sendCodeMessage.style.color = "green";

<<<<<<< HEAD
      // Redirect to the verification code input section
      window.location.href = `${window.location.pathname}?showVerificationCode=true`;
=======
      // Clear the verification code input field
      const verificationCodeInput = document.getElementById("verification-code");
      if (verificationCodeInput) {
        verificationCodeInput.value = "";
      }

      // Show the verification form and hide the login form
      document.getElementById("login-form").style.display = "none";
      document.getElementById("verification-form").style.display = "block";
>>>>>>> parent of 295f9066f (Implement email verification feature with code generation and validation)
    } catch (error) {
      console.error("Error:", error);
      sendCodeMessage.textContent = error.message || "An error occurred. Please try again.";
      sendCodeMessage.style.display = "block";
      sendCodeMessage.style.color = "red";
    }
  });

<<<<<<< HEAD
  // Handle "Verify Code" button click
  if (loginWithCodeButton) {
    loginWithCodeButton.addEventListener("click", async function () {
      const email = emailInput.value.trim();
      const code = verificationCodeInput.value.trim();
=======
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
  loginWithCodeButton.addEventListener("click", async function () {
    const code = verificationCodeInput.value.trim();

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

  // Handle "Login with Code Verification" button click
  if (loginWithCodeButtonVerification) {
    loginWithCodeButtonVerification.addEventListener("click", async function () {
      const email = emailInput.value.trim();
      const code = verificationCodeInputVerification.value.trim();
>>>>>>> parent of 295f9066f (Implement email verification feature with code generation and validation)

      if (!email || !code) {
        sendCodeMessage.textContent = "Please enter both email and verification code.";
        sendCodeMessage.style.display = "block";
        sendCodeMessage.style.color = "red";
        return;
      }

      try {
        const response = await loginWithVerificationCode(email, code);

<<<<<<< HEAD
        if (response.redirect_url) {
=======
        if (response && response.redirect_url) {
>>>>>>> parent of 295f9066f (Implement email verification feature with code generation and validation)
          sendCodeMessage.textContent = "Login successful!";
          sendCodeMessage.style.display = "block";
          sendCodeMessage.style.color = "green";
          window.location.href = response.redirect_url;
        } else {
<<<<<<< HEAD
          throw new Error("Failed to log in with code.");
=======
          throw new Error(response.message || "Failed to log in with code.");
>>>>>>> parent of 295f9066f (Implement email verification feature with code generation and validation)
        }
      } catch (error) {
        console.error("Error:", error);
        sendCodeMessage.textContent = error.message || "An error occurred. Please try again.";
        sendCodeMessage.style.display = "block";
        sendCodeMessage.style.color = "red";
      }
    });
<<<<<<< HEAD
  }

  // Handle "Back to Login" button click
  if (backToLoginButton) {
    backToLoginButton.addEventListener("click", function () {
      // Show the login form and hide the verification form
      form.style.display = "flex"; // Show the login form
      verificationForm.style.display = "none"; // Hide the verification form
    });
  }
=======
  } else {
    console.error("❌ ERROR: #login-with-code-button-verification not found in the DOM.");
  }
>>>>>>> parent of 295f9066f (Implement email verification feature with code generation and validation)
});