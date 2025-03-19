import { 
signin
} from "/static/requests/authRequests.js";;

      document.addEventListener("DOMContentLoaded", function () {
        const urlParams = new URLSearchParams(window.location.search);
        const message = urlParams.get("message");
        const successMessage = document.getElementById("success-message");

        if (message) {
          successMessage.textContent = message;
          successMessage.style.display = "block";
          successMessage.style.color = "var(--highlight)"; // Match error message color
        }

        const form = document.getElementById("signin-form");
        const errorMessage = document.getElementById("error-message");

        if (!form) {
          console.error("❌ ERROR: #signin-form not found in the DOM.");
          return;
        }

        form.addEventListener("submit", async function (event) {
          event.preventDefault();

          const email = document.getElementById("email").value;
          const password = document.getElementById("password").value;

          try {
            const redirectUrl = await signin(email, password);
            window.location.href = redirectUrl;
          } catch (error) {
            errorMessage.textContent = error.message;
            errorMessage.style.display = "block";
          }
        });
      });