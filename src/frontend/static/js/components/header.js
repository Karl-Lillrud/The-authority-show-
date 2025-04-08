import { fetchPodcasts } from "/static/requests/podcastRequests.js";

document.addEventListener("DOMContentLoaded", () => {
  const aiEditLink = document.getElementById("ai-edit-link");
  if (aiEditLink) {
    const host = window.location.hostname;
    const streamlitURL = `http://${host}:8501/`;
    aiEditLink.href = streamlitURL;
  }

  populateHeaderPodcastDropdown();
  populateLandingPageDropdown();
  setDynamicPageTitle();
  populateUserCredits();
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
  const dropdownSelected = dropdownContainer.querySelector(".dropdown-selected");
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

    dropdownSelected.addEventListener("click", () => {
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
async function populateUserCredits() {
  let user_id = new URLSearchParams(window.location.search).get("user_id");
  if (!user_id || user_id === "null") {
    user_id = currentUserID || localStorage.getItem("user_id");
  }
  console.log("populateUserCredits: user_id =", user_id);
  if (!user_id) {
    console.warn("No user id provided, credits will not be fetched.");
    return;
  }

  try {
    const response = await fetch(`/api/credits?user_id=${user_id}`);
    if (!response.ok) throw new Error("Failed to fetch credits");
    const data = await response.json();
    const creditsElement = document.getElementById("user-credits");
    creditsElement.textContent = data.availableCredits;
  } catch (err) {
    console.error("Error fetching user credits:", err);
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
  confirmLogout.addEventListener("click", () => {
    document.cookie = "remember_me=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    window.location.href = logoutLink.href;
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
      "/team": "Team Members",
      "/guest": "Guest View",
      "/taskmanagement": "Task Management",
    };

    const currentPath = window.location.pathname;
    const pageTitle = pageTitles[currentPath] || "PodManager";
    pageTitleElement.textContent = pageTitle;
  }
}
