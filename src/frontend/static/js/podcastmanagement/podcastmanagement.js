import { initPodcastFunctions } from "./podcast-functions.js";
import { initEpisodeFunctions } from "./episode-functions.js";
import { initGuestFunctions, showAddGuestPopup } from "./guest-functions.js"; // <-- Add showAddGuestPopup here
import { svgpodcastmanagement } from "./svgpodcastmanagement.js";
import { showNotification } from "../components/notifications.js";
import { initEmailConfigFunctions } from "./emailconfig-functions.js";

console.log("podcastmanagement.js loaded");

// Utility functions
function initializeSvgIcons() {
  // Sidebar menu icons
  document.getElementById("back-to-dashboard-icon").innerHTML =
    svgpodcastmanagement.backToDashboard;
  document.getElementById("podcasts-icon").innerHTML =
    svgpodcastmanagement.podcasts;

  document.getElementById("episodes-icon").innerHTML =
    svgpodcastmanagement.episodes;

  document.getElementById("guests-icon").innerHTML =
    svgpodcastmanagement.guests;

  // Action button icons
  document.getElementById("add-icon-podcast").innerHTML =
    svgpodcastmanagement.add;
  document.getElementById("add-icon-episode").innerHTML =
    svgpodcastmanagement.add;
  document.getElementById("add-icon-guest").innerHTML =
    svgpodcastmanagement.add;
}


// Function to update edit buttons to use pen icons
export function updateEditButtons() {
  // Find all edit buttons in the top-right actions
  const editButtons = document.querySelectorAll(".top-right-actions .edit-btn");

  editButtons.forEach((button) => {
    // Skip if button has already been processed
    if (button.querySelector("svg")) return;

    // Clear the button content
    button.innerHTML = svgpodcastmanagement.edit;
  });
}

// Add this function to observe DOM changes and update edit buttons when new content is added
function observeEditButtons() {
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.addedNodes.length) {
        updateEditButtons();
      }
    });
  });

  observer.observe(document.body, { childList: true, subtree: true });
}


function checkAndTriggerAddPodcast() {
  const addPodcastFlag = sessionStorage.getItem("Addpodcast");

  if (addPodcastFlag === "true") {
    // simulate a click
    const addPodcastBtn = document.getElementById("add-podcast-btn");
    if (addPodcastBtn) {
        addPodcastBtn.click();
    }
    // Reset the session storage flag to prevent repeated actions
    sessionStorage.setItem("Addpodcast", "false");
  }
}

// Function to close popups when clicking outside
function enablePopupCloseOnOutsideClick() {
  // Handle existing popups
  const popups = document.querySelectorAll(".popup");
  popups.forEach((popup) => {
    popup.addEventListener("click", (event) => {
      if (event.target === popup) {
        popup.style.display = "none";
      }
    });
  });

  // Set up a mutation observer to handle dynamically created popups
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.addedNodes.length) {
        mutation.addedNodes.forEach((node) => {
          if (node.classList && node.classList.contains("popup")) {
            node.addEventListener("click", (event) => {
              if (event.target === node) {
                node.style.display = "none";
              }
            });
          }
        });
      }
    });
  });

  observer.observe(document.body, { childList: true, subtree: true });
}

// Function to hide all popups
function hideAllPopups() {
  document.querySelectorAll(".popup").forEach(popup => {
    popup.style.display = "none";
  });
}

// Main initialization
document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM fully loaded and parsed");

  // Initialize SVG icons
  initializeSvgIcons();

  // Initialize module functions
  initPodcastFunctions();
  initEpisodeFunctions();
  initGuestFunctions();
  initEmailConfigFunctions();
  
  // Add this line to update edit buttons when the page loads
  updateEditButtons();

  // check if user is being redirected from dashboard to add a podcast
  checkAndTriggerAddPodcast();

  // Observe DOM for changes to update edit buttons
  observeEditButtons();

  // Enable closing popups by clicking outside
  enablePopupCloseOnOutsideClick();

  // Check for 'openCreateEpisode' query parameter
  const urlParams = new URLSearchParams(window.location.search);
  const openCreateEpisode = urlParams.get("openCreateEpisode");

  if (openCreateEpisode === "true") {
    // Trigger the "Create Episode" popup
    const createEpisodeButton = document.getElementById("create-episode-btn");
    if (createEpisodeButton) {
      createEpisodeButton.click(); // Simulate a click to open the popup
    }
  }

  // Highlight editing logic
  function showHighlightPopup(highlight) {
    const popup = document.getElementById("highlight-form-popup");
    document.getElementById("highlight-title").value = highlight.title || "";
    document.getElementById("highlight-start-time").value =
      highlight.startTime || "";
    document.getElementById("highlight-end-time").value =
      highlight.endTime || "";
    popup.style.display = "flex";
  }

  document
    .getElementById("edit-highlight-form")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      const highlightData = {
        title: document.getElementById("highlight-title").value.trim(),
        startTime: parseInt(
          document.getElementById("highlight-start-time").value,
          10
        ),
        endTime: parseInt(
          document.getElementById("highlight-end-time").value,
          10
        )
      };

      try {
        const response = await fetch("/edit_highlight", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(highlightData)
        });
        const result = await response.json();
        if (response.ok) {
          showNotification(
            "Success",
            "Highlight saved successfully!",
            "success"
          );
          document.getElementById("highlight-form-popup").style.display =
            "none";
        } else {
          showNotification(
            "Error",
            "Failed to save highlight: " + result.error,
            "error"
          );
        }
      } catch (error) {
        console.error("Error saving highlight:", error);
        showNotification("Error", "Failed to save highlight.", "error");
      }
    });

  async function verifyHighlightConsistency(highlight) {
    try {
      const response = await fetch("/verify_highlight", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(highlight)
      });
      const result = await response.json();
      if (response.ok) {
        showNotification(
          "Verified",
          "Highlight verified successfully!",
          "success"
        );
      } else {
        showNotification(
          "Error",
          "Highlight verification failed: " + result.error,
          "error"
        );
      }
    } catch (error) {
      console.error("Error verifying highlight:", error);
      showNotification("Error", "Failed to verify highlight.", "error");
    }
  }

  // Close the popup
  document
    .getElementById("close-highlight-form-popup")
    .addEventListener("click", () => {
      document.getElementById("highlight-form-popup").style.display = "none";
    });

  document
    .getElementById("cancel-highlight-form-btn")
    .addEventListener("click", () => {
      document.getElementById("highlight-form-popup").style.display = "none";
    });

  // Find the header element from the base template
  const headerElement = document.querySelector("header");
  if (headerElement) {
    const headerHeight = headerElement.offsetHeight;
    // Set the CSS variable for header height
    document.documentElement.style.setProperty(
      "--header-height",
      headerHeight + "px"
    );
  }

  // Add the decorative header to the top of the page
  const decorativeHeader = document.createElement("div");
  decorativeHeader.className = "decorative-header";
  document.body.prepend(decorativeHeader);

  setupMobileSidebar();

  // Example: before showing any popup, call hideAllPopups()
  document.getElementById("add-guest-btn").addEventListener("click", () => {
    hideAllPopups();
    showAddGuestPopup();
  });
  document.getElementById("create-episode-btn").addEventListener("click", () => {
    hideAllPopups();
    // ...show episode popup logic...
  });
});

function setupMobileSidebar() {
  const sidebarContainer = document.getElementById("sidebar-container");
  const openSidebarArrowBtn = document.getElementById("openSidebarArrowBtn");
  const pmSidebarOverlay = document.getElementById("pmSidebarOverlay");
  const pmSidebarCloseBtn = document.getElementById("pmSidebarCloseBtn");

  if (!sidebarContainer || !openSidebarArrowBtn || !pmSidebarOverlay || !pmSidebarCloseBtn) {
    console.warn("Mobile sidebar toggle elements not all found. Skipping mobile sidebar setup.");
    return;
  }

  const openSidebar = () => {
    sidebarContainer.classList.add("is-open");
    pmSidebarOverlay.classList.add("is-visible");
    // Prevent body scroll only on mobile when sidebar is a full overlay
    if (window.innerWidth <= 992) { // Match CSS breakpoint
      document.body.style.overflow = 'hidden';
    }
  };

  const closeSidebar = () => {
    sidebarContainer.classList.remove("is-open");
    pmSidebarOverlay.classList.remove("is-visible");
    document.body.style.overflow = ''; // Always restore body scroll
  };

  openSidebarArrowBtn.addEventListener("click", openSidebar);
  pmSidebarOverlay.addEventListener("click", closeSidebar);
  pmSidebarCloseBtn.addEventListener("click", closeSidebar);

  // Close sidebar if a menu link or action button inside it is clicked
  const sidebarItemsToCloseOnClick = sidebarContainer.querySelectorAll(".sidebar-menu-link, .sidebar-action-button");
  sidebarItemsToCloseOnClick.forEach(item => {
    item.addEventListener("click", () => {
      if (sidebarContainer.classList.contains("is-open")) {
        // For menu links, we might only close if it's a real navigation.
        // For action buttons, we generally always want to close.
        // The current simple approach is to close for any click on these items.
        // If a menu link is just toggling a sub-menu within the sidebar (not the case here currently),
        // this would need a more specific condition for that link.
        closeSidebar(); 
      }
    });
  });
}

// Export shared utilities and variables
export const shared = {
  selectedPodcastId: null,
  svgpodcastmanagement
};

document
  .getElementById("guests-link")
  .addEventListener("click", function (event) {
    event.preventDefault();
  });
