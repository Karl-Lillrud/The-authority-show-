// reset-password.js
import {
    resetPasswordRequest
  } from "/static/requests/forgotpasswordRequest.js";

document.addEventListener("DOMContentLoaded", function () {
  const urlParams = new URLSearchParams(window.location.search);
  const emailParam = urlParams.get("email");

  if (emailParam) {
    document.getElementById("email").value = emailParam; // Autofill email if found in URL
  } else {
    alert("Missing email parameter. Redirecting to forgot password.");
    window.location.href = "/forgotpassword";
  }

  document
    .getElementById("resetPasswordForm")
    .addEventListener("submit", function (event) {
      event.preventDefault();
      const email = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value.trim();

      resetPasswordRequest(email, password)
        .then((data) => {
          if (data.error) {
            alert("Error: " + data.error);
          } else {
            alert("Password reset successful! Redirecting to sign-in.");
            window.location.href = data.redirect_url;
          }
        })
        .catch((error) => console.error("Fetch Error:", error));
    });
});
