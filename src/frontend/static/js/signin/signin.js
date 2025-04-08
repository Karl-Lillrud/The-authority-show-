import { signin, sendVerificationCode, loginWithVerificationCode } from "/static/requests/authRequests.js";

document.addEventListener("DOMContentLoaded", function () {
  const urlParams = new URLSearchParams(window.location.search);
  const message = urlParams.get("message");
  const showVerificationCode = urlParams.get("showVerificationCode") === "true"; // Check if the verification code section should be shown
  const successMessage = document.getElementById("success-message");
  const errorMessage = document.getElementById("error-message");
  const form = document.getElementById("signin-form");
  const sendCodeButton = document.getElementById("send-code-button");
<<<<<<< HEAD
  const sendCodeMessage = document.getElementById("send-code-message");
  const loginWithCodeButton = document.getElementById("login-with-code-button");
  const emailInput = document.getElementById("email");
<<<<<<< HEAD
  const verificationForm = document.getElementById("verification-form");
  const verificationCodeInput = document.getElementById("verification-code");
  const backToLoginButton = document.getElementById("back-to-login");
=======
  const verificationCodeInput = document.getElementById("verification-code-login");
  const verificationCodeInputVerification = document.getElementById("verification-code-verification");
  const loginForm = document.getElementById("login-form");
  const verificationForm = document.getElementById("verification-form");
>>>>>>> parent of 003dcac05 (Add verification form and enhance sign-in process with improved error handling and code structure)
=======
  const emailInput = document.getElementById("email");
>>>>>>> parent of 072a6997d (Implement email verification code functionality for sign-in process)

  // Display success message if present in URL params
  if (message) {
    successMessage.textContent = message;
    successMessage.style.display = "block";
    successMessage.style.color = "var(--highlight)";
  }

  // Redirect to verification code section if specified in URL params
  if (showVerificationCode) {
    form.style.display = "none"; // Hide the login form
    verificationForm.style.display = "flex"; // Show the verification form
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

<<<<<<< HEAD
  // Handle "Sign in with Verification Code" button click
  if (sendCodeButton) {
    sendCodeButton.addEventListener("click", async function () {
      const email = emailInput ? emailInput.value.trim() : "";

<<<<<<< HEAD
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

      // Redirect to the verification code input section
      window.location.href = `${window.location.pathname}?showVerificationCode=true`;
    } catch (error) {
      console.error("Error:", error);
      sendCodeMessage.textContent = error.message || "An error occurred. Please try again.";
      sendCodeMessage.style.display = "block";
      sendCodeMessage.style.color = "red";
    }
  });

  // Handle "Verify Code" button click
  if (loginWithCodeButton) {
    loginWithCodeButton.addEventListener("click", async function () {
      const email = emailInput.value.trim();
      const code = verificationCodeInput.value.trim();
=======
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
>>>>>>> parent of 003dcac05 (Add verification form and enhance sign-in process with improved error handling and code structure)

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
<<<<<<< HEAD
=======
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
>>>>>>> parent of 003dcac05 (Add verification form and enhance sign-in process with improved error handling and code structure)
        }
      } catch (error) {
        console.error("Error:", error);
        sendCodeMessage.textContent = error.message || "An error occurred. Please try again.";
        sendCodeMessage.style.display = "block";
        sendCodeMessage.style.color = "red";
      }
    });
  }

  // Handle "Back to Login" button click
  if (backToLoginButton) {
    backToLoginButton.addEventListener("click", function () {
      // Show the login form and hide the verification form
      form.style.display = "flex"; // Show the login form
      verificationForm.style.display = "none"; // Hide the verification form
=======
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
>>>>>>> parent of 072a6997d (Implement email verification code functionality for sign-in process)
    });
  }
});