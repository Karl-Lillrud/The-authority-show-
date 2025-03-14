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

  if (podRssInput) {
    podRssInput.addEventListener("input", async function () {
      const rssUrl = this.value.trim() || "";
      if (rssUrl) {
        try {
          const feed = await fetchRSSData(rssUrl); // function from podcastRequests.js
          document.getElementById("podName").value = feed.title || "";
          document.getElementById("podLogoUrl").value = feed.image || ""; // Assuming feed.image contains the logo URL
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
      const podLogoUrl = document.getElementById("podLogoUrl").value.trim(); // Get the logo URL

      console.log("Podcast Name:", podName);
      console.log("Podcast RSS:", podRss);
      console.log("Podcast Logo URL:", podLogoUrl);

      if (!podName || !podRss) {
        alert("Please enter all required fields: Podcast Name and RSS URL.");
        return;
      }

      try {
        console.log("Sending invitation email");
        await sendInvitationEmail(podName, podRss, podLogoUrl); // Send the logo URL as well

        // Hide the Pod Name section and show the Email section
        podNameSection.classList.add("hidden");
        emailSection.classList.remove("hidden");

        // Show the credits container if it exists
        if (creditsContainer) {
          creditsContainer.classList.remove("hidden");
        }
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
