document.addEventListener("DOMContentLoaded", function () {
  const successMessage = document.getElementById("success-message");
  const errorMessage = document.getElementById("error-message");
  const sendLoginLinkButton = document.getElementById("send-login-link-button");
  const emailInput = document.getElementById("email");

  // Handle "Send Log-In Link" button click
  if (sendLoginLinkButton) {
    sendLoginLinkButton.addEventListener("click", async function () {
      const email = emailInput.value.trim();

      if (!email) {
        errorMessage.textContent = "Vänligen ange din e-postadress.";
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
        return;
      }

      try {
        const response = await fetch("/send-login-link", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email })
        });

        const result = await response.json();
        if (response.ok) {
          successMessage.textContent =
            "Inloggningslänk har skickats till din e-post!";
          successMessage.style.display = "block";
          errorMessage.style.display = "none";
        } else {
          errorMessage.textContent =
            result.error ||
            "Misslyckades att skicka inloggningslänk. Försök igen senare.";
          errorMessage.style.display = "block";
          successMessage.style.display = "none";
        }
      } catch (error) {
        console.error("Fel vid sändning av inloggningslänk:", error);
        errorMessage.textContent =
          "Ett oväntat fel uppstod vid sändning av inloggningslänk. Försök igen senare.";
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
      }
    });
  } else {
    console.warn("Knappen för att skicka inloggningslänk hittades inte i DOM");
  }

  // Handle token-based login from URL
  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get("token");

  if (token) {
    // Automatically log in the user using the token
    fetch("/verify-login-token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token })
    })
      .then(async (response) => {
        if (!response.ok) {
          const result = await response.json();
          throw new Error(
            `HTTP-fel! Status: ${response.status}, Meddelande: ${
              result.error || "Okänt fel"
            }`
          );
        }
        return response.json();
      })
      .then((data) => {
        if (data.redirect_url) {
          window.location.href = data.redirect_url;
        } else {
          errorMessage.textContent =
            data.error || "Misslyckades att logga in med den angivna länken.";
          errorMessage.style.display = "block";
          successMessage.style.display = "none";
        }
      })
      .catch((error) => {
        console.error("Fel vid verifiering av token:", error);
        const errorMsg = error.message.toLowerCase();
        if (errorMsg.includes("misslyckades att skapa konto")) {
          errorMessage.textContent =
            "Misslyckades att skapa konto. Kontrollera att din e-post är korrekt eller kontakta support.";
        } else if (errorMsg.includes("token har gått ut")) {
          errorMessage.textContent =
            "Inloggningslänken har gått ut. Skicka en ny länk.";
        } else if (errorMsg.includes("ogiltig token")) {
          errorMessage.textContent =
            "Inloggningslänken är ogiltig. Försök med en ny länk.";
        } else {
          errorMessage.textContent =
            "Ett fel uppstod under inloggningen. Försök igen eller kontakta support.";
        }
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
      });
  }

  // Handle email/password login form (if used)
  const form = document.getElementById("signin-form");
  if (form) {
    form.addEventListener("submit", async function (event) {
      event.preventDefault();

      const email = emailInput.value.trim();
      const password = document.getElementById("password")?.value?.trim();

      if (!email || (password !== undefined && !password)) {
        errorMessage.textContent = "Vänligen ange både e-post och lösenord.";
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
        return;
      }

      try {
        const response = await fetch("/signin", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password })
        });

        const result = await response.json();
        if (response.ok) {
          window.location.href = result.redirect_url || "/podprofile";
        } else {
          errorMessage.textContent =
            result.error || "Misslyckades att logga in. Försök igen.";
          errorMessage.style.display = "block";
          successMessage.style.display = "none";
        }
      } catch (error) {
        console.error("Fel under inloggning:", error);
        errorMessage.textContent = "Ett fel uppstod. Försök igen.";
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
      }
    });
  } else {
    console.warn("Inloggningsformulär hittades inte i DOM");
  }
});
