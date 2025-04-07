import { signin, sendVerificationCode, loginWithVerificationCode } from "/static/requests/authRequests.js";

document.addEventListener("DOMContentLoaded", function () {
  const loginForm = document.getElementById("login-form");
  const signinWithCodeContainer = document.getElementById("signin-with-code-container");
  const verificationCodeContainer = document.getElementById("verification-code-container");
  const sendVerificationCodeButton = document.getElementById("send-verification-code-button");
  const verifyCodeButton = document.getElementById("verify-code-button");
  const backToEmailButton = document.getElementById("back-to-email-button");
  const signinEmailInput = document.getElementById("signin-email");
  const verificationCodeInput = document.getElementById("verification-code");
  const sendCodeMessage = document.getElementById("send-code-message");
  const verificationCodeForm = document.getElementById("verification-code-form");
  const verificationCodeFormAlt = document.getElementById("verification-code-form-alt");
  const verifyCodeButtonAlt = document.getElementById("login-with-code-button-verification");

  const backToLoginButton1 = document.getElementById("back-to-login-1");
  const backToLoginButton2 = document.getElementById("back-to-login-2");
  const loginWithCodeButtonVerification1 = document.getElementById("login-with-code-button-verification-1");
  const loginWithCodeButtonVerification2 = document.getElementById("login-with-code-button-verification-2");
  const verificationCodeInput1 = document.getElementById("verification-code-verification-1");
  const verificationCodeInput2 = document.getElementById("verification-code-verification-2");

  if (!signinEmailInput) {
    console.error("❌ ERROR: Element with id 'signin-email' not found in the DOM.");
  }

  // Hantera "Send Verification Code"-knappen
  if (sendVerificationCodeButton) {
    sendVerificationCodeButton.addEventListener("click", async function () {
      const email = signinEmailInput.value.trim();

      if (!email) {
        sendCodeMessage.textContent = "Please enter your email.";
        sendCodeMessage.style.display = "block";
        sendCodeMessage.style.color = "red";
        return;
      }

      try {
        const response = await sendVerificationCode(email);

        console.log("Server response:", response);

        if (response.success) {
          sendCodeMessage.textContent = "Verification code sent successfully.";
          sendCodeMessage.style.display = "block";
          sendCodeMessage.style.color = "green";
        } else {
          throw new Error(response.message || "Failed to send verification code.");
        }
      } catch (error) {
        console.error("Error:", error);
        sendCodeMessage.textContent = error.message || "An error occurred. Please try again.";
        sendCodeMessage.style.display = "block";
        sendCodeMessage.style.color = "red";
      }
    });
  } else {
    console.error("❌ ERROR: Element with id 'send-verification-code-button' not found in the DOM.");
  }

  // Hantera "Verify Code"-knappen för första formuläret
  verifyCodeButton.addEventListener("click", async function () {
    const email = signinEmailInput.value.trim();
    const code = verificationCodeInput.value.trim();

    if (!code) {
      alert("Please enter the verification code.");
      return;
    }

    try {
      const response = await loginWithVerificationCode(email, code);

      if (response.redirect_url) {
        alert("Verification successful! Redirecting...");
        window.location.href = response.redirect_url;
      } else {
        throw new Error(response.message || "Verification failed.");
      }
    } catch (error) {
      console.error("Error verifying code:", error);
      alert(error.message || "An error occurred. Please try again.");
    }
  });

  // Hantera "Verify Code"-knappen för andra formuläret
  verifyCodeButtonAlt.addEventListener("click", async function () {
    const verificationCodeElement = document.getElementById("verification-code-verification");
    if (!verificationCodeElement) {
      console.error("Verification code element not found.");
      return;
    }

    const code = verificationCodeElement.value.trim();
    if (!code) {
      alert("Please enter the verification code.");
      return;
    }
    // Lägg till din verifieringslogik här
    console.log("Verifying code (alt):", code);
  });

  // Hantera "Back to Email"-knappen
  backToEmailButton.addEventListener("click", function () {
    verificationCodeContainer.style.display = "none";
    signinWithCodeContainer.style.display = "block";
  });

  // Exempel: Visa loginForm och dölja andra containrar
  document.getElementById("back-to-login-button").addEventListener("click", function () {
    loginForm.style.display = "block";
    signinWithCodeContainer.style.display = "none";
    verificationCodeContainer.style.display = "none";
  });

  // Handle "Back to Login" button click for the first form
  if (backToLoginButton1) {
    backToLoginButton1.addEventListener("click", function () {
      document.getElementById("verification-form").style.display = "none";
      document.getElementById("login-form").style.display = "block";
    });
  }

  // Handle "Back to Login" button click for the second form
  if (backToLoginButton2) {
    backToLoginButton2.addEventListener("click", function () {
      document.getElementById("verification-code-container").style.display = "none";
      document.getElementById("signin-with-code-container").style.display = "block";
    });
  }

  // Handle "Login with Code" button click for the first form
  if (loginWithCodeButtonVerification1) {
    loginWithCodeButtonVerification1.addEventListener("click", async function () {
      const code = verificationCodeInput1.value.trim();
      if (!code) {
        alert("Please enter the verification code.");
        return;
      }
      // Add your login logic here
      console.log("Logging in with code (form 1):", code);
    });
  }

  // Handle "Login with Code" button click for the second form
  if (loginWithCodeButtonVerification2) {
    loginWithCodeButtonVerification2.addEventListener("click", async function () {
      const code = verificationCodeInput2.value.trim();
      if (!code) {
        alert("Please enter the verification code.");
        return;
      }
      // Add your login logic here
      console.log("Logging in with code (form 2):", code);
    });
  }

  loginForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!email || !password) {
      alert("Please enter both email and password.");
      return;
    }

    try {
      const redirectUrl = await signin(email, password);
      window.location.href = redirectUrl;
    } catch (error) {
      console.error("Error signing in:", error);
      alert(error.message || "An error occurred. Please try again.");
    }
  });

  const backToLoginButton = document.getElementById("back-to-login-button");

  if (backToLoginButton) {
    backToLoginButton.addEventListener("click", function () {
      loginForm.style.display = "block";
      signinWithCodeContainer.style.display = "none";
      verificationCodeContainer.style.display = "none";
    });
  } else {
    console.error("❌ ERROR: Element with id 'back-to-login-button' not found in the DOM.");
  }

  if (verificationCodeForm) {
    verificationCodeForm.addEventListener("submit", function (event) {
      event.preventDefault();
      const code = document.getElementById("verification-code").value.trim();

      if (!code) {
        alert("Please enter the verification code.");
        return;
      }

      // Lägg till din verifieringslogik här
      console.log("Verifying code from verificationCodeForm:", code);
    });
  }

  if (verificationCodeFormAlt) {
    verificationCodeFormAlt.addEventListener("submit", function (event) {
      event.preventDefault();
      const code = document.getElementById("verification-code-verification").value.trim();

      if (!code) {
        alert("Please enter the verification code.");
        return;
      }

      // Lägg till din verifieringslogik här
      console.log("Verifying code from verificationCodeFormAlt:", code);
    });
  }

  // Kontrollera om elementet med id="show-login-form" finns
  const showLoginFormButton = document.getElementById("show-login-form");

  if (showLoginFormButton) {
    showLoginFormButton.addEventListener("click", function () {
      document.getElementById("login-form").style.display = "block";
    });
  } else {
    console.error("❌ ERROR: Element med id 'show-login-form' not found in the DOM.");
  }

  // Kontrollera om elementet med id="login-with-code-button-verification" finns
  if (verifyCodeButtonAlt) {
    verifyCodeButtonAlt.addEventListener("click", async function () {
      const verificationCodeElement = document.getElementById("verification-code-verification");
      if (!verificationCodeElement) {
        console.error("Verification code element not found.");
        return;
      }

      const code = verificationCodeElement.value.trim();
      if (!code) {
        alert("Please enter the verification code.");
        return;
      }

      console.log("Verifying code (alt):", code);
    });
  } else {
    console.error("❌ ERROR: Element with id 'login-with-code-button-verification' not found in the DOM.");
  }

  signinWithCodeContainer.style.display = "block"; // Ensure the container is visible
});

document.getElementById("show-login-form").addEventListener("click", function () {
  document.getElementById("login-form").style.display = "block";
});