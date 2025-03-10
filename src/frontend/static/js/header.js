import { fetchPodcasts } from '/static/requests/podcastRequests.js';

async function populatePodcastDropdown() {
  const dropdown = document.getElementById("headerPodcastDropdown");
  if (!dropdown) {
    console.error("Header podcast dropdown element not found.");
    return;
  }
  try {
    // fetchPodcasts returns an object; extract the array from the 'podcast' property.
    const data = await fetchPodcasts();
    console.log("Podcasts fetched in header:", data);
    const podcasts = data.podcast || [];
    podcasts.forEach(podcast => {
      const option = document.createElement("option");
      option.value = podcast._id;
      option.textContent = podcast.podName;
      dropdown.appendChild(option);
    });

    // Check localStorage for the saved podcast selection
    const savedPodcastId = localStorage.getItem('selectedPodcastId');
    if (savedPodcastId) {
      dropdown.value = savedPodcastId;
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

const podcastDropdown = document.querySelector("#headerPodcastDropdown");
if (podcastDropdown) {
  podcastDropdown.addEventListener("change", function () {
    console.log("Selected podcast:", this.value);
    // Save the selected podcast ID to localStorage
    localStorage.setItem('selectedPodcastId', this.value);
    window.location.href = "/podcast"; // Redirect to podcast.html
  });
  // Set the initial value based on localStorage (if available)
  if (podcastDropdown.value) {
    console.log("Podcast pre-selected:", podcastDropdown.value);
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", populatePodcastDropdown);
} else {
  populatePodcastDropdown();
}
