import { fetchPodcasts } from "/static/requests/podcastRequests.js";

document.addEventListener("DOMContentLoaded", () => {
  populateHeaderPodcastDropdown();
  populateLandingPageDropdown();
  setDynamicPageTitle();
  populateStoreCredits();

  const buyBtn = document.getElementById("buy-credits-btn");
  if (buyBtn) {
    buyBtn.addEventListener("click", () => {
      window.location.href = `/store`;
    });
  }

  // 🔒 Hide unfinished menu links by text content
  document.querySelectorAll("a").forEach((link) => {
    const text = link.textContent.trim().toLowerCase();
    if (
      text.includes("team management") ||
      text.includes("episode to-do")
    ) {
      link.style.display = "none";
      link.style.pointerEvents = "none";
    }
  });

  // Optional: hide dropdowns too
  const dropdownIds = ["dropdown-lp-content", "headerPodcastDropdown"];
  dropdownIds.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.style.display = "none";
  });
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
      const response = await fetch("/logout", { method: "GET" });
      const result = await response.json();
      if (response.ok) {
        window.location.href = result.redirect_url || "/signin";
      } else {
        console.error("Logout failed:", result.message);
        alert("Failed to log out. Please try again.");
      }
    } catch (error) {
      console.error("Error during logout:", error);
      alert("An error occurred. Please try again.");
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
    };

    const currentPath = window.location.pathname;
    const pageTitle = pageTitles[currentPath] || "Store";
    pageTitleElement.textContent = pageTitle;
  }
}
