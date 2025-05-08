import { fetchPodcasts } from "/static/requests/podcastRequests.js";

document.addEventListener("DOMContentLoaded", () => {
  populateHeaderPodcastDropdown();
  populateLandingPageDropdown();
  setDynamicPageTitle();
  populateStoreCredits();

  const buyBtn = document.getElementById("buy-credits-btn");
  if (buyBtn) {
    buyBtn.addEventListener("click", () => {
      // Remove localStorage dependency and navigate directly to billing
      window.location.href = `/store`;
    });
  }
});

// 🔽 Landing Page Dropdown
function toggleLandingPage() {
  const dropdown = document.getElementById("dropdown-lp-content");
  const triangle = document.getElementById("triangle");

  if (dropdown.style.display === "none" || dropdown.style.display === "") {
    dropdown.style.display = "block";
    triangle.classList.replace("triangle-down", "triangle-up");
  } else {
    dropdown.style.display = "none";
    triangle.classList.replace("triangle-up", "triangle-down");
  }
}
window.toggleLandingPage = toggleLandingPage;

async function populateLandingPageDropdown() {
  const dropdown = document.getElementById("dropdown-lp-content");
  if (!dropdown) return;

  try {
    const data = await fetchPodcasts();
    const podcasts = data.podcast || [];
    const optionsContainer = dropdown.querySelector(".dropdown-lp-options");

    podcasts.forEach((podcast) => {
      const option = document.createElement("a");
      option.textContent = podcast.podName;
      option.href = `/landingpage/${podcast._id}`;

      option.addEventListener("click", (e) => {
        e.preventDefault();
        window.location.href = `/landingpage/${podcast._id}`;
      });

      optionsContainer.appendChild(option);
    });
  } catch (err) {
    console.error("Error populating landing page dropdown:", err);
  }
}

// 🔽 Header Dropdown for `/podcast/:id`
async function populateHeaderPodcastDropdown() {
  const dropdownContainer = document.getElementById("headerPodcastDropdown");
  const dropdownSelected =
    dropdownContainer.querySelector(".dropdown-selected");
  const dropdownOptions = dropdownContainer.querySelector(".dropdown-options");

  try {
    const data = await fetchPodcasts();
    const podcasts = data.podcast || [];

    podcasts.forEach((podcast) => {
      const option = document.createElement("div");
      option.classList.add("dropdown-option");
      option.textContent = podcast.podName;
      option.dataset.id = podcast._id;

      option.addEventListener("click", () => {
        localStorage.setItem("selectedPodcastId", podcast._id);
        window.location.href = `/podcast/${podcast._id}`;
      });

      dropdownOptions.appendChild(option);
    });

    dropdownContainer.addEventListener("click", () => {
      dropdownOptions.style.display =
        dropdownOptions.style.display === "block" ? "none" : "block";
    });

    document.addEventListener("click", (e) => {
      if (!dropdownContainer.contains(e.target)) {
        dropdownOptions.style.display = "none";
      }
    });
  } catch (err) {
    console.error("Error populating header podcast dropdown:", err);
  }
}

// Function to fetch and display user credits
async function populateStoreCredits() {
  try {
    const creditsElement = document.getElementById("user-credits");
    if (!creditsElement) return; // Skip if element doesn't exist

    const response = await fetch("/api/credits", {
      credentials: "same-origin" // Include cookies for auth
    });

    // Handle non-JSON responses or errors
    if (!response.ok) {
      console.warn("Failed to fetch credits:", response.status);
      creditsElement.textContent = "-";
      return;
    }

    const data = await response.json();
    creditsElement.textContent = data.availableCredits;
  } catch (err) {
    console.error("Error fetching user credits:", err);
    const creditsElement = document.getElementById("user-credits");
    if (creditsElement) creditsElement.textContent = "-";
  }
}

// 🔧 Toggle mobile menu
function toggleMenu() {
  const menu = document.getElementById("menu");
  const menuToggle = document.querySelector(".menu-toggle");

  if (menu) {
    menuToggle.classList.toggle("active");

    if (menu.classList.contains("active")) {
      menu.style.transform = "scale(0.95)";
      menu.style.opacity = "0";

      setTimeout(() => {
        menu.classList.remove("active");
        menu.style.display = "none";
      }, 300);
    } else {
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

// 🔐 Logout modal
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
  confirmLogout.addEventListener("click", async () => {
    try {
      const response = await fetch("/auth/logout", { // Ensure this is /auth/logout
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
      });

      if (!response.ok) {
        // Attempt to parse error if JSON, otherwise use status text
        let errorData;
        try {
          errorData = await response.json();
        } catch (e) {
          // If not JSON, use status text or a generic message
          throw new Error(
            `Logout failed with status: ${response.status} ${response.statusText}`,
          );
        }
        console.error("Logout failed:", errorData);
        throw new Error(errorData.error || "Logout failed");
      }

      const data = await response.json();
      console.log("Logout successful:", data);

      // Clear any client-side session storage or state related to the user
      sessionStorage.clear(); // Example: clear all session storage
      localStorage.clear(); // Example: clear all local storage (use with caution)

      // Redirect to the signin page or the URL provided in the response
      if (data.redirect_url) {
        window.location.href = data.redirect_url;
      } else {
        window.location.href = "/signin"; // Default fallback
      }
    } catch (error) {
      console.error("Error during logout:", error);
      // Display a user-friendly message if needed
      // alert(`Logout error: ${error.message}`);
    }
  });
}
window.addEventListener("click", (e) => {
  if (e.target === logoutModal) {
    logoutModal.style.display = "none";
  }
});

// Close menu on outside click
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

// 🧠 Dynamic Page Title
function setDynamicPageTitle() {
  const pageTitleElement = document.getElementById("page-title");
  if (pageTitleElement) {
    const pageTitles = {
      "/account": "Account",
      "/podcastmanagement": "Podcast Management",
      "/dashboard": "Dashboard",
      "/team": "Team Management",
      "/guest": "Guest View",
      "/episode-to-do": "Episode To-Do",
      "/enterprise": "Enterprise",
      "/lia": "LIA", // Add this line
    };

    const currentPath = window.location.pathname;
    const pageTitle = pageTitles[currentPath] || "Store";
    pageTitleElement.textContent = pageTitle;
  }
}

window.populateStoreCredits = populateStoreCredits;
