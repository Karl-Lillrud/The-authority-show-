import { fetchRSSData } from '../requests/podcastRequests.js';
import { sendInvitationEmail } from '../requests/invitationRequests.js';

document.addEventListener("DOMContentLoaded", function () {
  // Only using the Pod Name and Email sections.
  const goToEmailSection = document.getElementById("goToEmailSection");
  const skipToDashboard = document.getElementById("skipToDashboard");
  const podNameForm = document.getElementById("podNameForm");

  if (goToEmailSection) {
    goToEmailSection.addEventListener("click", async () => {
      const podNameElement = document.getElementById("podName");
      const podRssElement = document.getElementById("podRss");
      const userEmailElement = document.getElementById("loggedInUserEmail");

      const podName = podNameElement ? podNameElement.value.trim() : "";
      const podRss = podRssElement ? podRssElement.value.trim() : "";
      const userEmail = userEmailElement ? userEmailElement.value.trim() : "";

      console.log("User email:", userEmail);
      console.log("Podcast Name:", podName);
      console.log("Podcast RSS:", podRss);

      if (!userEmail || !podName || !podRss) {
        alert("Please enter all required fields: Email, Podcast Name, and RSS URL.");
        return;
      }
      try {
        console.log("Sending invitation email to:", userEmail);
        await sendInvitationEmail(userEmail, podName, podRss);
        // Hide the Pod Name section and show the Email section.
        document.getElementById("pod-name-section").classList.add("hidden");
        document.getElementById("email-section").classList.remove("hidden");
      } catch (error) {
        console.error("Error sending invitation email:", error);
        alert("Something went wrong. Please try again.");
      }
    });
  }

  if (skipToDashboard) {
    skipToDashboard.addEventListener("click", () => {
      window.location.href = "dashboard";
    });
  }

  const podRssInput = document.getElementById("podRss");
  if (podRssInput) {
    podRssInput.addEventListener("input", async function () {
      const rssUrl = this.value.trim() || "";
      if (rssUrl) {
        try {
          const feed = await fetchRSSData(rssUrl); // function from podcastRequests.js
          document.getElementById("podName").value = feed.title || "";
        } catch (error) {
          console.error("Error processing RSS feed:", error);
        }
      }
    });
  }

  // ...existing code for dark mode, language selection, and fetchRSSData remains unchanged...
});

// ...additional functions such as dark mode toggle remain unchanged...
