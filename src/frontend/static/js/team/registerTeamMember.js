import { registerTeamMember } from "../../requests/authRequests.js"

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("registerTeamMemberForm")
  const registerButton = document.getElementById("registerButton")
  const loadingText = document.getElementById("loadingText")
  const errorMessage = document.getElementById("errorMessage")

  // Attach event listeners for password toggles
  document.querySelectorAll(".toggle-password").forEach((button) => {
    button.addEventListener("click", function () {
      togglePassword(this.getAttribute("data-target"), this)
    })
  })

  function togglePassword(fieldId, button) {
    const passwordField = document.getElementById(fieldId)
    if (passwordField.type === "password") {
      passwordField.type = "text"
      button.textContent = "Hide"
    } else {
      passwordField.type = "password"
      button.textContent = "Show"
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault()

    // Extract invite token from URL
    const urlParams = new URLSearchParams(window.location.search)
    const inviteToken = urlParams.get("token")

    if (!inviteToken) {
      showError("Missing invite token in URL.")
      return
    }

    // Disable button & show loading
    registerButton.disabled = true
    loadingText.style.display = "block"

    // Collect form data
    const formData = {
      fullName: document.getElementById("fullName").value.trim(),
      email: document.getElementById("email").value.trim(),
      phone: document.getElementById("phone").value.trim(),
      password: document.getElementById("password").value,
      confirmPassword: document.getElementById("confirmPassword").value,
      inviteToken: inviteToken,
    }

    // Password match validation
    if (formData.password !== formData.confirmPassword) {
      showError("Passwords do not match.")
      return
    }

    // Password strength validation (at least 8 characters, includes both numbers and letters)
    if (!isValidPassword(formData.password)) {
      showError("Password must be at least 8 characters long and contain both numbers and letters.")
      return
    }

    try {
      // Call function from authRequests.js to submit form
      const redirectUrl = await registerTeamMember(
        formData.email,
        formData.password,
        formData.fullName,
        formData.phone,
        formData.inviteToken,
      )
      window.location.href = redirectUrl
    } catch (error) {
      showError(error.message)
    } finally {
      registerButton.disabled = false
      loadingText.style.display = "none"
    }
  })

  function showError(message) {
    errorMessage.textContent = message
    errorMessage.style.display = "block"
    registerButton.disabled = false
    loadingText.style.display = "none"
  }

  function isValidPassword(password) {
    return password.length >= 8 && /[A-Za-z]/.test(password) && /\d/.test(password)
  }
})

