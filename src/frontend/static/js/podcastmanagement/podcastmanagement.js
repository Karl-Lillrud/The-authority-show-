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

// Function to close popups when clicking outside
function enablePopupCloseOnOutsideClick() {
  const popups = document.querySelectorAll(".popup");
  popups.forEach((popup) => {
    popup.addEventListener("click", (event) => {
      if (event.target === popup) {
        popup.style.display = "none";
      }
    });
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

  // Add this line to update edit buttons when the page loads
  updateEditButtons();

  // Observe DOM for changes to update edit buttons
  observeEditButtons();

  // Enable closing popups by clicking outside
  enablePopupCloseOnOutsideClick();

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

  // Close / Cancel popup
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
});

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
