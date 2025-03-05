document.addEventListener("DOMContentLoaded", function () {
  // Only using the Pod Name and Email sections.
  const goToEmailSection = document.getElementById("goToEmailSection");
  const skipToDashboard = document.getElementById("skipToDashboard");
  const podNameForm = document.getElementById("podNameForm");

  if (goToEmailSection) {
    goToEmailSection.addEventListener("click", async () => {
      const podName = document.getElementById("podName").value.trim();
      const podRss = document.getElementById("podRss").value.trim();
      const userEmail = document.getElementById("loggedInUserEmail").value.trim();
      console.log("User email:", userEmail); // Add this line to log the user email
      if (!podName || !podRss) {
        alert("Please enter both Podcast Name and RSS URL.");
        return;
      }
      try {
        await postPodcastData(podName, podRss);
        console.log("Sending invitation email to:", userEmail);
        await sendInvitationEmail(userEmail);
        // Hide the Pod Name section and show the Email section.
        document.getElementById("pod-name-section").classList.add("hidden");
        document.getElementById("email-section").classList.remove("hidden");
      } catch (error) {
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
      const rssUrl = this.value.trim();
      if (rssUrl) {
        try {
          const feed = await fetchRSSData(rssUrl); // function from podprofileRequests.js
          document.getElementById("podName").value = feed.title || "";
        } catch (error) {
          console.error("Error processing RSS feed:", error);
        }
      }
    });
  }

  // ...existing code for dark mode, language selection, and fetchRSSData remains unchanged...
});

async function sendInvitationEmail(email) {
  try {
    const response = await fetch("/send_invitation", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: email,
        subject: "Welcome to PodManager.ai!",
      }),
    });
    if (!response.ok) {
      throw new Error("Failed to send invitation email.");
    }
  } catch (error) {
    console.error("Error sending invitation email:", error);
  }
}

// ...additional functions such as dark mode toggle remain unchanged...
