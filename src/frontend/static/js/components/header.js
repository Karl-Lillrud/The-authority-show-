import { fetchPodcasts } from "/static/requests/podcastRequests.js";

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
      dropdown.style.display = "none";
      return;
    }

    // Visa dropdownen om det finns fler än 2 podcasts
    dropdown.style.display = "block";

    const selected = dropdown.querySelector(".dropdown-selected");
    const optionsContainer = dropdown.querySelector(".dropdown-options");

    podcasts.forEach((podcast) => {
      const option = document.createElement("div");
      option.textContent = podcast.podName;
      option.dataset.value = podcast._id;

      option.addEventListener("click", () => {
        selected.textContent = podcast.podName;
        localStorage.setItem("selectedPodcastId", podcast._id);
        window.location.href = "/podcast";
      });

      optionsContainer.appendChild(option);
    });

    dropdown.addEventListener("click", () => {
      dropdown.classList.toggle("active");
    });

    document.addEventListener("click", (e) => {
      if (!dropdown.contains(e.target)) {
        dropdown.classList.remove("active");
      }
    });
  } catch (err) {
    console.error("Error populating dropdown:", err);
  }
}

// Improved menu toggle with animation
function toggleMenu() {
  const menu = document.getElementById("menu");
  const menuToggle = document.querySelector(".menu-toggle");

  if (menu) {
    menuToggle.classList.toggle("active");

    if (menu.classList.contains("active")) {
      // Close menu with animation
      menu.style.transform = "scale(0.95)";
      menu.style.opacity = "0";

      setTimeout(() => {
        menu.classList.remove("active");
        menu.style.display = "none";
      }, 300);
    } else {
      // Open menu with animation
      menu.style.display = "flex";
      menu.style.transform = "scale(0.95)";
      menu.style.opacity = "0";

      setTimeout(() => {
        menu.classList.add("active");
        menu.style.transform = "scale(1)";
        menu.style.opacity = "1";
      }, 10);
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
    localStorage.setItem("selectedPodcastId", selectedPodcast);
    console.log("Saved podcast ID to localStorage:", selectedPodcast);
  });

  // Clear localStorage ONLY when navigating away from podcast.html
  window.addEventListener("beforeunload", () => {
    if (window.location.pathname === "/podcast") {
      // Do nothing when leaving podcast.html
    } else {
      localStorage.removeItem("selectedPodcastId");
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
  logoutLink.addEventListener("click", (e) => {
    e.preventDefault();
    logoutModal.style.display = "flex";
  });
}

if (cancelLogout) {
  cancelLogout.addEventListener("click", () => {
    logoutModal.style.display = "none";
  });
}

if (confirmLogout) {
  confirmLogout.addEventListener("click", () => {
    document.cookie =
      "remember_me=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    window.location.href = logoutLink.href;
  });
}

window.addEventListener("click", (e) => {
  if (e.target === logoutModal) {
    logoutModal.style.display = "none";
  }
});

// Close menu when clicking outside
document.addEventListener("click", (e) => {
  const menu = document.getElementById("menu");
  const menuToggle = document.querySelector(".menu-toggle");

  if (
    menu &&
    menu.classList.contains("active") &&
    !menu.contains(e.target) &&
    !menuToggle.contains(e.target)
  ) {
    toggleMenu();
  }
});
