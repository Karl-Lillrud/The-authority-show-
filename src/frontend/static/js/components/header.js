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
      text.includes("team management")
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
  try {
    const response = await fetchPodcasts();
    const podcasts = response.podcast || [];
    const podcastDropdownMenu = document.getElementById("podcast-dropdown-menu");
    
    // Add null check before using querySelector
    if (!podcastDropdownMenu) {
      console.warn("Podcast dropdown menu element not found in the DOM");
      return;
    }
    
    const podcastList = podcastDropdownMenu.querySelector(".dropdown-menu");
    if (!podcastList) {
      console.warn("Dropdown menu list element not found inside podcast dropdown");
      return;
    }

    // Clear existing content
    podcastList.innerHTML = "";

    if (!podcasts.length) {
      const emptyItem = document.createElement("div");
      emptyItem.className = "dropdown-item disabled";
      emptyItem.textContent = "No podcasts found";
      podcastList.appendChild(emptyItem);
      return;
    }

    // Add each podcast to the dropdown
    podcasts.forEach((podcast) => {
      const item = document.createElement("a");
      item.className = "dropdown-item";
      item.href = `/podcasts/${podcast._id}`;
      item.textContent = podcast.podName || "Untitled Podcast";
      podcastList.appendChild(item);
    });

    // Add a divider and link to manage podcasts
    const divider = document.createElement("div");
    divider.className = "dropdown-divider";
    podcastList.appendChild(divider);

    const manageLink = document.createElement("a");
    manageLink.className = "dropdown-item";
    manageLink.href = "/podcastmanagement";
    manageLink.textContent = "Manage Podcasts";
    podcastList.appendChild(manageLink);
  } catch (error) {
    console.error("Error populating podcast dropdown:", error);
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
      const response = await fetch("/logout", { // Ensure this is /logout
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
      "/publish": "Publish", // <-- Add this line for the publish endpoint
    };

    const currentPath = window.location.pathname;
    const pageTitle = pageTitles[currentPath]
    pageTitleElement.textContent = pageTitle;
  }
}

window.populateStoreCredits = populateStoreCredits;
