import { fetchPodcasts } from "/static/requests/podcastRequests.js";

function toggleLandingPage() {
  var dropdown = document.getElementById("dropdown-content");
  var triangle = document.getElementById("triangle");

  // Toggle dropdown visibility and triangle direction
  if (dropdown.style.display === "none" || dropdown.style.display === "") {
    dropdown.style.display = "block";
    triangle.classList.remove("triangle-down");
    triangle.classList.add("triangle-up");
  } else {
    dropdown.style.display = "none";
    triangle.classList.remove("triangle-up");
    triangle.classList.add("triangle-down");
  }
}
window.toggleLandingPage = toggleLandingPage;

async function populatePodcastDropdown() {
  const dropdown = document.getElementById("dropdown-content");
  if (!dropdown) {
    console.error("Header podcast dropdown element not found.");
    return;
  }

  try {
    // Fetch the podcasts
    const data = await fetchPodcasts();
    console.log("Podcasts fetched:", data);
    const podcasts = data.podcast || [];
    const optionsContainer = dropdown.querySelector(".dropdown-options");

    podcasts.forEach((podcast) => {
      const option = document.createElement("a");
      option.textContent = podcast.podName;
      option.href = "/landingpage/" + podcast._id;
      option.dataset.value = podcast._id;

      option.addEventListener("click", () => {
        window.location.href = "/landingpage/" + podcast._id;
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

document.addEventListener("DOMContentLoaded", async () => {
  const mainContent = document.querySelector("main");
  const pageTitleElement = document.getElementById("page-title");

  // Function to load content dynamically
  async function loadContent(url) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        const html = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");
        const newContent = doc.querySelector("main").innerHTML;

        if (mainContent) {
          mainContent.innerHTML = newContent;
        }

        // Update the page title dynamically
        const pageTitles = {
          "/account": "Account",
          "/podcastmanagement": "Podcast Management",
          "/dashboard": "Dashboard",
          "/team": "Team Members",
          "/guest": "Guest View",
          "/taskmanagement": "Task Management",
        };

        const currentPath = new URL(url).pathname;
        const pageTitle = pageTitles[currentPath] || "PodManager";

        if (pageTitleElement) {
          pageTitleElement.textContent = pageTitle;
        }

        // Update the <title> tag in the <head>
        document.title = pageTitle;
      } else {
        console.error("Failed to load content:", response.status);
      }
    } catch (err) {
      console.error("Error loading content dynamically:", err);
    }
  }

  // Load content for the current URL on page load
  await loadContent(window.location.href);

  // Handle navigation clicks
  const navLinks = document.querySelectorAll(".menu a, #landing-page-link");
  navLinks.forEach((link) => {
    link.addEventListener("click", async (e) => {
      e.preventDefault();
      const url = link.href;

      await loadContent(url);
      window.history.pushState({}, "", url);
    });
  });

  // Handle browser back/forward navigation
  window.addEventListener("popstate", async () => {
    await loadContent(window.location.href);
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const landingPageLink = document.getElementById("landing-page-link");

  if (landingPageLink) {
    const selectedPodcastId = localStorage.getItem("selectedPodcastId");

    // Set the href dynamically (good for right-click > open in new tab)
    if (selectedPodcastId) {
      landingPageLink.href = `/landingpage/${selectedPodcastId}`;
    }

    // On click, prevent default and redirect
    landingPageLink.addEventListener("click", (e) => {
      e.preventDefault();
      const id = localStorage.getItem("selectedPodcastId");
      if (id) {
        window.location.href = `/landingpage/${id}`;
      } else {
        alert("Please select a podcast first.");
      }
    });
  }
});
