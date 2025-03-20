import { initPodcastFunctions } from "./podcast-functions.js";
import { initEpisodeFunctions } from "./episode-functions.js";
import { initGuestFunctions } from "./guest-functions.js";
import { svgpodcastmanagement } from "./svgpodcastmanagement.js";

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

// Notification system
export function showNotification(title, message, type = "info") {
  // Remove any existing notification
  const existingNotification = document.querySelector(".notification");
  if (existingNotification) {
    existingNotification.remove();
  }

  // Create notification elements
  const notification = document.createElement("div");
  notification.className = `notification ${type}`;

  // Icon based on type
  let iconSvg = "";
  if (type === "success") {
    iconSvg = svgpodcastmanagement.success;
  } else if (type === "error") {
    iconSvg = svgpodcastmanagement.error;
  } else {
    iconSvg = svgpodcastmanagement.defaultIcon;
  }

  notification.innerHTML = `
  <div class="notification-icon">${iconSvg}</div>
  <div class="notification-content">
    <div class="notification-title">${title}</div>
    <div class="notification-message">${message}</div>
  </div>
  <div class="notification-close">
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <line x1="18" y1="6" x2="6" y2="18"></line>
      <line x1="6" y1="6" x2="18" y2="18"></line>
    </svg>
  </div>
  `;

  // Add to DOM
  document.body.appendChild(notification);

  // Add event listener to close button
  notification
    .querySelector(".notification-close")
    .addEventListener("click", () => {
      notification.classList.remove("show");
      setTimeout(() => {
        notification.remove();
      }, 500);
    });

  // Show notification with animation
  setTimeout(() => {
    notification.classList.add("show");
  }, 10);

  // Auto hide after 5 seconds
  setTimeout(() => {
    if (document.body.contains(notification)) {
      notification.classList.remove("show");
      setTimeout(() => {
        if (document.body.contains(notification)) {
          notification.remove();
        }
      }, 500);
    }
  }, 5000);
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

// Main initialization
document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM fully loaded and parsed");

  // Initialize SVG icons
  initializeSvgIcons();

  // Initialize module functions
  initPodcastFunctions();
  initEpisodeFunctions();
  initGuestFunctions();

  // Add this line to update edit buttons when the page loads
  updateEditButtons();

  // Observe DOM for changes to update edit buttons
  observeEditButtons();

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
});

// Export shared utilities and variables
export const shared = {
  selectedPodcastId: null,
  svgpodcastmanagement
};
