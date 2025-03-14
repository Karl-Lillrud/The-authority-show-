import { fetchPodcasts } from "../requests/podcastRequests.js";

document.addEventListener("DOMContentLoaded", function () {
  const podcastPopup = document.getElementById("podcast-popup");
  const podcastList = document.getElementById("podcast-list");
  const closePodcastPopup = document.getElementById("close-podcast-popup");

  async function fetchAndDisplayPodcasts() {
    try {
      console.log("Fetching podcasts...");
      const data = await fetchPodcasts();
      const podcasts = data.podcast; // Access the podcast property
      console.log("Podcasts fetched:", podcasts);
      podcastList.innerHTML = ""; // Clear existing content
      podcasts.forEach((podcast) => {
        const podcastItem = document.createElement("li");
        podcastItem.className = "podcast-item";
        podcastItem.innerHTML = `
          <span class="podcast-title">${podcast.podName}</span>
          <div class="podcast-item-actions">
            <button class="view-btn" data-id="${podcast._id}">View</button>
          </div>
        `;
        // Add click event to the View button that redirects to podcast management view details
        const viewBtn = podcastItem.querySelector(".view-btn");
        viewBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          // Redirect to podcast management view details page for the selected podcast
          window.location.href = `/podcastmanagement?podcastId=${podcast._id}`;
        });
        podcastList.appendChild(podcastItem);
      });
    } catch (error) {
      console.error("Error fetching podcasts:", error);
    }
  }
  window.fetchAndDisplayPodcasts = fetchAndDisplayPodcasts; // Expose the function to window

  // Fetch and display podcasts when the podcast popup is shown
  podcastPopup.addEventListener("click", function (e) {
    if (e.target === podcastPopup) {
      fetchAndDisplayPodcasts();
    }
  });

  // Close podcast popup on clicking the close button
  closePodcastPopup.addEventListener("click", function () {
    podcastPopup.style.display = "none";
  });

  // Close podcast popup if clicking outside the popup-content
  podcastPopup.addEventListener("click", function (e) {
    if (e.target === podcastPopup) {
      podcastPopup.style.display = "none";
    }
  });
});
