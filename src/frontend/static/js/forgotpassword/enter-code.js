// enter-code.js
import {
    enterCodeRequest,
    resendCodeRequest
  } from "/static/requests/forgotpasswordRequest.js";

document.addEventListener("DOMContentLoaded", function () {
  const urlParams = new URLSearchParams(window.location.search);
  const emailParam = urlParams.get("email");

  if (emailParam) {
    document.getElementById("email").value = emailParam; // Autofill email if found in URL
  }

  document
    .getElementById("enterCodeForm")
    .addEventListener("submit", function (event) {
      event.preventDefault();
      const email = document.getElementById("email").value.trim();
      const code = document.getElementById("code").value.trim();

      enterCodeRequest(email, code)
        .then((data) => {
          if (data.error) {
            alert("Error: " + data.error);
          } else if (data.redirect_url) {
            window.location.href = data.redirect_url + "?email=" + encodeURIComponent(email);
          } else {
            alert("Unexpected response from the server.");
          }
        })
        .catch((error) => console.error("Fetch Error:", error));
    });

  document
    .getElementById("resendCode")
    .addEventListener("click", function () {
      const email = document.getElementById("email").value.trim();

      if (!email) {
        alert("Please enter your email first.");
        return;
      }

      resendCodeRequest(email)
        .then((data) => {
          alert(data.message || data.error);
        })
        .catch((error) => console.error("Fetch Error:", error));
    });
});
