import { registerTeamMember } from "../../requests/authRequests.js";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("registerTeamMemberForm");
  const registerButton = document.getElementById("registerButton");
  const loadingText = document.getElementById("loadingText");
  const errorMessage = document.getElementById("errorMessage");

  // Extract all URL parameters in one place
  const urlParams = new URLSearchParams(window.location.search);
  const inviteToken = urlParams.get("token");
  const teamName = decodeURIComponent(
    urlParams.get("teamName") || "Unnamed Team"
  );
  const role = decodeURIComponent(urlParams.get("role"));
  const email = urlParams.get("email");

  // Update team name everywhere
  document.querySelectorAll(".teamName").forEach((el) => {
    if (el) el.textContent = teamName;
  });

  // Update role if element exists
  const teamRoleElement = document.getElementById("teamRole");
  if (teamRoleElement) teamRoleElement.textContent = role;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!inviteToken) {
      showError("Missing invite token in URL.");
      return;
    }

    // Disable button & show loading
    registerButton.disabled = true;
    loadingText.style.display = "block";

    // Collect form data
    const formData = {
      fullName: document.getElementById("fullName").value.trim(),
      email: document.getElementById("email").value.trim(),
      phone: document.getElementById("phone").value.trim(),
  
      inviteToken: inviteToken
    };

    try {
      // Call function from authRequests.js to submit form
      const redirectUrl = await registerTeamMember(
        formData.email,
       
        formData.fullName,
        formData.phone,
        formData.inviteToken
      );
      window.location.href = redirectUrl;
    } catch (error) {
      showError(error.message);
    } finally {
      registerButton.disabled = false;
      loadingText.style.display = "none";
    }
  });

  function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = "block";
    registerButton.disabled = false;
    loadingText.style.display = "none";
  }

});
