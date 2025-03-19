// forgot-password.js
import {
    forgotPasswordRequest
  } from "/static/requests/forgotpasswordRequest.js";

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("forgotPasswordForm");
  const successMessage = document.getElementById("success-message");
  const errorMessage = document.getElementById("error-message");

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    const email = document.getElementById("email").value;

    try {
      const response = await forgotPasswordRequest(email);

      if (response.message) {
        successMessage.textContent =
          "Reset code sent successfully. Please check your email.";
        successMessage.style.display = "block";
        window.location.href = `/enter-code?email=${encodeURIComponent(email)}`;
      } else {
        alert("Error sending reset code: " + response.error);
      }
    } catch (error) {
      errorMessage.textContent = error.message;
      errorMessage.style.display = "block";
    }
  });
});
