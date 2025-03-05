document.addEventListener("DOMContentLoaded", function () {
  // Only using the Pod Name and Email sections.
  const goToEmailSection = document.getElementById("goToEmailSection");
  const skipToDashboard = document.getElementById("skipToDashboard");
  const podNameForm = document.getElementById("podNameForm");

  if (goToEmailSection) {
    goToEmailSection.addEventListener("click", async () => {
      const podName = document.getElementById("podName").value.trim();
      const podRss = document.getElementById("podRss").value.trim();
      if (!podName || !podRss) {
        alert("Please enter both Podcast Name and RSS URL.");
        return;
      }
      try {
        await postPodcastData(podName, podRss);
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

// ...additional functions such as dark mode toggle remain unchanged...
