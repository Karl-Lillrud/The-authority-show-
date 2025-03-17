import { fetchPodcasts, fetchRSSData } from "../requests/podcastRequests.js";

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
      for (const podcast of podcasts) {
        const podcastItem = document.createElement("li");
        podcastItem.className = "podcast-item";
        podcastItem.style.cursor = "pointer"; // Change cursor to pointer on hover

        // Fetch additional information from the RSS feed
        let imageUrl =
          "{{ url_for('static', filename='images/mock-avatar.jpeg') }}";
        try {
          const rssData = await fetchRSSData(podcast.rssFeed);
          console.log("RSS Data:", rssData); // Log all RSS data
          imageUrl = rssData.imageUrl || imageUrl;
        } catch (error) {
          console.error("Error fetching RSS data:", error);
        }

        podcastItem.innerHTML = `
          <span class="podcast-title">${podcast.podName}</span>
          <img src="${imageUrl}" alt="${podcast.podName}" class="podcast-image" />
          <div class="podcast-item-actions">
            <button class="view-btn" data-id="${podcast._id}">View</button>
          </div>
        `;
        // Add click event to the entire podcast item that redirects to podcast management view details
        podcastItem.addEventListener("click", (e) => {
          e.stopPropagation();
          // Redirect to podcast management view details page for the selected podcast
          window.location.href = `/podcastmanagement?podcastId=${podcast._id}`;
        });

        podcastList.appendChild(podcastItem);
      }
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
