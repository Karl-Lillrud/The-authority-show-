document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("register-form");
  const errorMessage = document.getElementById("error-message");
  const emailExistsModal = document.getElementById("email-exists-modal");
  const emailExistsOkButton = document.getElementById("email-exists-ok-button");
  const successModal = document.getElementById("success-modal");
  const successOkButton = document.getElementById("success-ok-button");

  if (
    !emailExistsModal ||
    !emailExistsOkButton ||
    !successModal ||
    !successOkButton
  ) {
    console.error("Modal elements not found in the DOM.");
    return;
  }

  const API_BASE_URL = window.API_BASE_URL;

  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
      const response = await fetch(`${API_BASE_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        const result = await response.json();
        if (result.error === "Email already registered.") {
          emailExistsModal.style.display = "block";
          emailExistsOkButton.addEventListener("click", function () {
            emailExistsModal.style.display = "none";
          });
        } else {
          throw new Error(result.error || "Registration failed.");
        }
      } else {
        successModal.style.display = "block";
        successOkButton.addEventListener("click", async function () {
          const result = await response.json();
          if (result.redirect_url) {
            window.location.href = result.redirect_url;
          } else {
            window.location.href = "/signin";
          }
        });
      }
    } catch (error) {
      errorMessage.textContent = error.message;
      errorMessage.style.display = "block";
    }
  });
});
