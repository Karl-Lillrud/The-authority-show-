import { fetchPodcasts } from '/static/requests/podcastRequests.js';

async function populatePodcastDropdown() {
  const dropdown = document.getElementById("headerPodcastDropdown");
  if (!dropdown) {
    console.error("Header podcast dropdown element not found.");
    return;
  }

  try {
    // Fetch the podcasts
    const data = await fetchPodcasts();
    console.log("Podcasts fetched:", data);
    const podcasts = data.podcast || [];

    if (podcasts.length < 2) {
      dropdown.style.display = 'none';
      return;
    }

    // Populate the dropdown with the fetched podcasts
    podcasts.forEach(podcast => {
      const option = document.createElement("option");
      option.value = podcast._id;
      option.textContent = podcast.podName;
      dropdown.appendChild(option);
    });

    // Check if we're on podcast page
    if (window.location.pathname === "/podcast") {
      const savedPodcastId = localStorage.getItem('selectedPodcastId');
      console.log("Loaded saved podcast ID from localStorage:", savedPodcastId);

      if (savedPodcastId) {
        // Set the saved podcast as selected in the dropdown
        dropdown.value = savedPodcastId;
        console.log("Podcast selected in dropdown:", savedPodcastId);
      } else {
        // Reset to default option if no saved podcast is found
        dropdown.selectedIndex = 0;
        console.log("No saved podcast found. Resetting to default option.");
      }
    } else {
      // Reset dropdown to default for other pages (non-podcast pages)
      dropdown.selectedIndex = 0;
      console.log("Not on podcast page. Resetting dropdown to default.");
    }
  } catch (err) {
    console.error("Error populating dropdown:", err);
  }
}

function toggleMenu() {
  const menu = document.getElementById("menu");
  if (menu) {
    menu.style.display = menu.style.display === "flex" ? "none" : "flex";
    if (menu.style.display === "flex") {
      menu.style.position = "absolute";
    }
  }
}
window.toggleMenu = toggleMenu;

const podcastDropdown = document.querySelector("#headerPodcastDropdown");

if (podcastDropdown) {
  podcastDropdown.addEventListener("change", function () {
    const selectedPodcast = this.value;
    console.log("Selected podcast:", selectedPodcast);
      window.location.href = "/podcast"; // Redirect to podcast.html after saving selection
      localStorage.setItem('selectedPodcastId', selectedPodcast);
    console.log("Saved podcast ID to localStorage:", selectedPodcast);
    
  });

  // Clear localStorage ONLY when navigating away from podcast.html
  window.addEventListener("beforeunload", () => {
    if (window.location.pathname === "/podcast") {
      // Do nothing when leaving podcast.html
    } else {
      localStorage.removeItem('selectedPodcastId');
      console.log("Cleared selected podcast from localStorage on page unload.");
      // Reset dropdown to default when leaving the podcast page
      if (podcastDropdown) {
        podcastDropdown.selectedIndex = 0;
        console.log("Dropdown reset to default.");
      }
    }
  });
}

// Ensure the dropdown is populated when the document is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", populatePodcastDropdown);
} else {
  populatePodcastDropdown();
}

const logoutLink = document.getElementById("logout-link");
const logoutModal = document.getElementById("logout-modal");
const cancelLogout = document.getElementById("cancel-logout");
const confirmLogout = document.getElementById("confirm-logout");

if (logoutLink) {
  logoutLink.addEventListener("click", function (e) {
    e.preventDefault();
    logoutModal.style.display = "flex";
  });
}

if (cancelLogout) {
  cancelLogout.addEventListener("click", function () {
    logoutModal.style.display = "none";
  });
}

if (confirmLogout) {
  confirmLogout.addEventListener("click", function () {
    document.cookie =
      "remember_me=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    window.location.href = logoutLink.href;
  });
}

window.addEventListener("click", function (e) {
  if (e.target === logoutModal) {
    logoutModal.style.display = "none";
  }
});