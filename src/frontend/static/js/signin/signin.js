document.addEventListener("DOMContentLoaded", function () {
  const successMessage = document.getElementById("success-message");
  const errorMessage = document.getElementById("error-message");
  const sendLoginLinkButton = document.getElementById("send-login-link-button");
  const emailInput = document.getElementById("email");
  const slidingContainer = document.querySelector(".sliding-container");
  const overlay = document.querySelector(".overlay");
  const closeButton = document.querySelector(".close-button");

  // Function to toggle sliding container
  function toggleSlidingContainer() {
    slidingContainer.classList.toggle("active");
    overlay.classList.toggle("active");
    
    // Add/remove body scroll lock when popup is active
    if (slidingContainer.classList.contains("active")) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
  }

  // Add click event listener only to the About PodManager link
  const aboutLink = document.querySelector('.policy-links a[href*="about"]');
  if (aboutLink) {
    aboutLink.addEventListener('click', (e) => {
      e.preventDefault();
      toggleSlidingContainer();
    });
  }

  // Add click event listener to the close button
  if (closeButton) {
    closeButton.addEventListener('click', (e) => {
      e.stopPropagation(); // Prevent event from bubbling to container
      toggleSlidingContainer();
    });
  }

  // Add click event listener to the overlay to close the container
  if (overlay) {
    overlay.addEventListener('click', () => {
      toggleSlidingContainer();
    });
  }

  // Add escape key listener to close popup
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && slidingContainer.classList.contains('active')) {
      toggleSlidingContainer();
    }
  });

  // Handle "Get Log-In Link" button click
  if (sendLoginLinkButton) {
    sendLoginLinkButton.addEventListener("click", async function () {
      const email = emailInput.value.trim();
      const originalButtonText = sendLoginLinkButton.innerHTML;

      if (!email) {
        errorMessage.textContent = "Please enter your email address.";
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
        return;
      }

      try {
        // Change button text to "Sending..."
        sendLoginLinkButton.innerHTML = `<span>Sending...</span><div class="button-loader"></div>`;
        sendLoginLinkButton.disabled = true;

        const response = await fetch("/send-login-link", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email })
        });

        const result = await response.json();
        if (response.ok) {
          successMessage.textContent =
            "A login link has been sent to your email!";
          successMessage.style.display = "block";
          errorMessage.style.display = "none";
        } else {
          errorMessage.textContent =
            result.error ||
            "Failed to send login link. Please try again later.";
          errorMessage.style.display = "block";
          successMessage.style.display = "none";
        }
      } catch (error) {
        console.error("Error sending login link:", error);
        errorMessage.textContent =
          "An unexpected error occurred while sending the login link. Please try again later.";
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
      } finally {
        // Restore button text and enable it
        sendLoginLinkButton.innerHTML = originalButtonText;
        sendLoginLinkButton.disabled = false;
      }
    });
  } else {
    console.warn("Login link button was not found in the DOM");
  }

  // Handle token-based login from URL
  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get("token");

  if (token) {
    console.log("SIGNIN.JS: Token found in URL:", token);

    // Automatically log in the user using the token
    fetch("/verify-login-token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token })
    })
      .then(async (response) => {
        console.log(
          "SIGNIN.JS: Received response from /verify-login-token:",
          response.status
        );
        if (!response.ok) {
          const result = await response.json();
          throw new Error(
            `HTTP error! Status: ${response.status}, Message: ${
              result.error || "Unknown error"
            }`
          );
        }
        return response.json();
      })
      .then((data) => {
        console.log("SIGNIN.JS: Parsed response data:", data);
        if (data.redirect_url) {
          window.location.href = data.redirect_url;
        } else {
          errorMessage.textContent =
            data.error || "Failed to log in using the provided link.";
          errorMessage.style.display = "block";
          successMessage.style.display = "none";
        }
      })
      .catch((error) => {
        console.error(
          "SIGNIN.JS: Error during token verification fetch:",
          error
        );
        const errorMsg = error.message.toLowerCase();
        if (errorMsg.includes("failed to create account")) {
          errorMessage.textContent =
            "Failed to create account. Please verify your email or contact support.";
        } else if (errorMsg.includes("token has expired")) {
          errorMessage.textContent =
            "The login link has expired. Please request a new one.";
        } else if (errorMsg.includes("invalid token")) {
          errorMessage.textContent =
            "The login link is invalid. Try a new link.";
        } else {
          errorMessage.textContent =
            "An error occurred during login. Please try again or contact support.";
        }
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
      });
  } else {
    console.log("SIGNIN.JS: No token found in URL parameters.");
  }
});