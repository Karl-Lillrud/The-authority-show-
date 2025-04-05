document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("verification-code-form");
  const email = document.getElementById("email").value;
  const verificationCodeInput = document.getElementById("verification-code");
  const errorMessage = document.getElementById("error-message");

  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const code = verificationCodeInput.value.trim();

    if (!code) {
      errorMessage.textContent = "Please enter the verification code.";
      errorMessage.style.display = "block";
      return;
    }

    try {
      const response = await fetch("/login-with-code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, code }),
      });

      if (!response.ok) {
        const result = await response.json().catch(() => {
          throw new Error("Unexpected response from server.");
        });
        throw new Error(result.error || "Failed to verify code.");
      }

      const result = await response.json();
      window.location.href = result.redirect_url || "/dashboard";
    } catch (error) {
      console.error("Error:", error);
      errorMessage.textContent = error.message || "An error occurred. Please try again.";
      errorMessage.style.display = "block";
    }
  });
});
