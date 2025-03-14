import { fetchRSSData } from "../requests/podcastRequests.js";
import { sendInvitationEmail } from "../requests/invitationRequests.js";

document.addEventListener("DOMContentLoaded", function () {
  // DOM Elements
  const darkModeToggle = document.getElementById("dark-mode-toggle");
  const goToEmailSection = document.getElementById("goToEmailSection");
  const skipToDashboard = document.getElementById("skipToDashboard");
  const podNameSection = document.getElementById("pod-name-section");
  const emailSection = document.getElementById("email-section");
  const podNameForm = document.getElementById("podNameForm");
  const podRssInput = document.getElementById("podRss");
  const podNameInput = document.getElementById("podName");
  const creditsContainer = document.getElementById("creditsContainer");
  const welcomePopup = document.getElementById("welcome-popup");
  const closeWelcomePopup = document.getElementById("close-welcome-popup");

  // Dark Mode Toggle
  darkModeToggle.addEventListener("click", function () {
    document.body.classList.toggle("dark-mode");

    // Update moon/sun emoji based on dark mode state
    if (document.body.classList.contains("dark-mode")) {
      darkModeToggle.textContent = "☀️"; // Sun for dark mode
    } else {
      darkModeToggle.textContent = "🌙"; // Moon for light mode
    }
  });

  // RSS Feed Input Handler
  if (podRssInput) {
    podRssInput.addEventListener("input", async function () {
      const rssUrl = this.value.trim();
      if (rssUrl) {
        try {
          const rssData = await fetchRSSData(rssUrl);
          podNameInput.value = rssData.title; // Set the title correctly
        } catch (error) {
          console.error("Error processing RSS feed:", error);
        }
      }
    });
  }

  // Go to Email Section Button
  if (goToEmailSection) {
    goToEmailSection.addEventListener("click", async () => {
      const podName = podNameInput ? podNameInput.value.trim() : "";
      const podRss = podRssInput ? podRssInput.value.trim() : "";

      console.log("Podcast Name:", podName);
      console.log("Podcast RSS:", podRss);

      if (!podName || !podRss) {
        alert("Please enter all required fields: Podcast Name and RSS URL.");
        return;
      }

      try {
        console.log("Sending invitation email");
        await sendInvitationEmail(podName, podRss);

        // Redirect to dashboard and set a flag to show the popup
        sessionStorage.setItem("showWelcomePopup", "true");
        window.location.href = "/dashboard"; // Redirects to the dashboard
      } catch (error) {
        console.error("Error sending invitation email:", error);
        alert("Something went wrong. Please try again.");
      }
    });
  }

  // if (skipToDashboard) {
  //   skipToDashboard.addEventListener("click", () => {
  //     console.log("Navigating to dashboard");
  //     window.location.href = "/dashboard"; // Redirects to the dashboard
  //   });
  // }
});
