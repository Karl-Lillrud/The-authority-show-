import { initPodcastFunctions } from "./podcast-functions.js"
import { initEpisodeFunctions } from "./episode-functions.js"
import { initGuestFunctions } from "./guest-functions.js"
import { svgpodcastmanagement } from "./svgpodcastmanagement.js"
import { showNotification } from "../components/notifications.js"
import { initEmailConfigFunctions } from "./emailconfig-functions.js"
 
console.log("podcastmanagement.js loaded")
 
// Utility functions
function initializeSvgIcons() {
  // Sidebar menu icons
  document.getElementById("back-to-dashboard-icon").innerHTML = svgpodcastmanagement.backToDashboard
  document.getElementById("podcasts-icon").innerHTML = svgpodcastmanagement.podcasts
 
  document.getElementById("episodes-icon").innerHTML = svgpodcastmanagement.episodes
 
  document.getElementById("guests-icon").innerHTML = svgpodcastmanagement.guests
 
  // Action button icons
  document.getElementById("add-icon-podcast").innerHTML = svgpodcastmanagement.add
  document.getElementById("add-icon-episode").innerHTML = svgpodcastmanagement.add
  document.getElementById("add-icon-guest").innerHTML = svgpodcastmanagement.add
}
 
// Function to update edit buttons to use pen icons
export function updateEditButtons() {
  // Find all edit buttons in the top-right actions
  const editButtons = document.querySelectorAll(".top-right-actions .edit-btn")
 
  editButtons.forEach((button) => {
    // Skip if button has already been processed
    if (button.querySelector("svg")) return
 
    // Clear the button content
    button.innerHTML = svgpodcastmanagement.edit
  })
}
 
// Add this function to observe DOM changes and update edit buttons when new content is added
function observeEditButtons() {
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.addedNodes.length) {
        updateEditButtons()
      }
    })
  })
 
  observer.observe(document.body, { childList: true, subtree: true })
}
 
function checkAndTriggerAddPodcast() {
  const addPodcastFlag = sessionStorage.getItem("Addpodcast")
 
  if (addPodcastFlag === "true") {
    // simulate a click
    const addPodcastBtn = document.getElementById("add-podcast-btn")
    if (addPodcastBtn) {
      addPodcastBtn.click()
    }
    // Reset the session storage flag to prevent repeated actions
    sessionStorage.setItem("Addpodcast", "false")
  }
}
 
// Function to close popups when clicking outside
function enablePopupCloseOnOutsideClick() {
  // Handle existing popups
  const popups = document.querySelectorAll(".popup")
  popups.forEach((popup) => {
    popup.addEventListener("click", (event) => {
      if (event.target === popup) {
        popup.style.display = "none"
      }
    })
  })
 
  // Set up a mutation observer to handle dynamically created popups
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.addedNodes.length) {
        mutation.addedNodes.forEach((node) => {
          if (node.classList && node.classList.contains("popup")) {
            node.addEventListener("click", (event) => {
              if (event.target === node) {
                node.style.display = "none"
              }
            })
          }
        })
      }
    })
  })
 
  observer.observe(document.body, { childList: true, subtree: true })
}
 
// Main initialization
document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM fully loaded and parsed")
 
  // Initialize SVG icons
  initializeSvgIcons()
 
  // Initialize module functions
  initPodcastFunctions()
  // DEV_NOTE: Within initPodcastFunctions (or the functions it calls for adding a podcast):
  // Ensure that when calling `addPodcast` from `podcastRequests.js`,
  // you catch the specific error for incomplete account setup.
  // Example:
  // try {
  //   await addPodcast(podcastData);
  //   // ... success logic
  // } catch (error) {
  //   if (error.code === "ACCOUNT_NOT_FOUND") {
  //     showNotification(
  //       "Account Incomplete",
  //       "Your account setup is incomplete. Please go to your profile to finalize your account before adding a podcast.",
  //       "warning", // or "error"
  //       {
  //         duration: 7000, // Longer duration for important messages
  //         // Optional: Add a button to redirect to profile
  //         // actions: [{ text: "Go to Profile", onClick: () => window.location.href = '/profile' }]
  //       }
  //     );
  //   } else {
  //     showNotification("Error", error.message || "Failed to add podcast.", "error");
  //   }
  // }
 
  initEpisodeFunctions()
  initGuestFunctions()
  initEmailConfigFunctions()
 
  // Add this line to update edit buttons when the page loads
  updateEditButtons()
 
  // check if user is being redirected from dashboard to add a podcast
  checkAndTriggerAddPodcast()
 
  // Observe DOM for changes to update edit buttons
  observeEditButtons()
 
  // Enable closing popups by clicking outside
  enablePopupCloseOnOutsideClick()
 
  // Check for 'openCreateEpisode' query parameter
  const urlParams = new URLSearchParams(window.location.search)
  const openCreateEpisode = urlParams.get("openCreateEpisode")
 
  if (openCreateEpisode === "true") {
    // Trigger the "Create Episode" popup
    const createEpisodeButton = document.getElementById("create-episode-btn")
    if (createEpisodeButton) {
      createEpisodeButton.click() // Simulate a click to open the popup
    }
  }
 
  // Highlight editing logic
  function showHighlightPopup(highlight) {
    const popup = document.getElementById("highlight-form-popup")
    document.getElementById("highlight-title").value = highlight.title || ""
    document.getElementById("highlight-start-time").value = highlight.startTime || ""
    document.getElementById("highlight-end-time").value = highlight.endTime || ""
    popup.style.display = "flex"
  }
 
  document.getElementById("edit-highlight-form").addEventListener("submit", async (e) => {
    e.preventDefault()
    const highlightData = {
      title: document.getElementById("highlight-title").value.trim(),
      startTime: Number.parseInt(document.getElementById("highlight-start-time").value, 10),
      endTime: Number.parseInt(document.getElementById("highlight-end-time").value, 10),
    }
 
    try {
      const response = await fetch("/edit_highlight", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(highlightData),
      })
      const result = await response.json()
      if (response.ok) {
        showNotification("Success", "Highlight saved successfully!", "success")
        document.getElementById("highlight-form-popup").style.display = "none"
      } else {
        showNotification("Error", "Failed to save highlight: " + result.error, "error")
      }
    } catch (error) {
      console.error("Error saving highlight:", error)
      showNotification("Error", "Failed to save highlight.", "error")
    }
  })
 
  async function verifyHighlightConsistency(highlight) {
    try {
      const response = await fetch("/verify_highlight", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(highlight),
      })
      const result = await response.json()
      if (response.ok) {
        showNotification("Verified", "Highlight verified successfully!", "success")
      } else {
        showNotification("Error", "Highlight verification failed: " + result.error, "error")
      }
    } catch (error) {
      console.error("Error verifying highlight:", error)
      showNotification("Error", "Failed to verify highlight.", "error")
    }
  }
 
  // Close the popup
  document.getElementById("close-highlight-form-popup").addEventListener("click", () => {
    document.getElementById("highlight-form-popup").style.display = "none"
  })
 
  document.getElementById("cancel-highlight-form-btn").addEventListener("click", () => {
    document.getElementById("highlight-form-popup").style.display = "none"
  })
 
  // Find the header element from the base template
  const headerElement = document.querySelector("header")
  if (headerElement) {
    const headerHeight = headerElement.offsetHeight
    // Set the CSS variable for header height
    document.documentElement.style.setProperty("--header-height", headerHeight + "px")
  }
 
  // Add the decorative header to the top of the page
  const decorativeHeader = document.createElement("div")
  decorativeHeader.className = "decorative-header"
  document.body.prepend(decorativeHeader)
 
  setupMobileSidebar()
})
 
function setupMobileSidebar() {
  const sidebarContainer = document.getElementById("sidebar-container")
  const openSidebarArrowBtn = document.getElementById("openSidebarArrowBtn")
  const pmSidebarOverlay = document.getElementById("pmSidebarOverlay")
  const pmSidebarCloseBtn = document.getElementById("pmSidebarCloseBtn")
 
  if (!sidebarContainer || !openSidebarArrowBtn || !pmSidebarOverlay || !pmSidebarCloseBtn) {
    console.warn("Mobile sidebar toggle elements not all found. Skipping mobile sidebar setup.")
    return
  }
 
  // Create a floating mobile menu button that's always visible
  const mobileMenuButton = document.createElement("button")
  mobileMenuButton.id = "mobile-menu-button"
  mobileMenuButton.className = "mobile-menu-button"
  mobileMenuButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>`
  document.body.appendChild(mobileMenuButton)
 
  const openSidebar = () => {
    sidebarContainer.classList.add("is-open")
    pmSidebarOverlay.classList.add("is-visible")
    // Add animation class
    sidebarContainer.classList.add("sidebar-animate-in")
    // Prevent body scroll only on mobile when sidebar is a full overlay
    if (window.innerWidth <= 992) {
      // Match CSS breakpoint
      document.body.style.overflow = "hidden"
    }
    // Hide the mobile menu button when sidebar is open
    mobileMenuButton.classList.add("hidden")
    // Hide the arrow button when sidebar is open
    openSidebarArrowBtn.style.display = "none"
    // Ensure close button is visible when sidebar is open
    pmSidebarCloseBtn.style.display = "flex"
  }
 
  const closeSidebar = () => {
    // Add animation class first
    sidebarContainer.classList.add("sidebar-animate-out")
 
    // Wait for animation to complete before hiding
    setTimeout(() => {
      sidebarContainer.classList.remove("is-open")
      sidebarContainer.classList.remove("sidebar-animate-in")
      sidebarContainer.classList.remove("sidebar-animate-out")
      pmSidebarOverlay.classList.remove("is-visible")
      document.body.style.overflow = "" // Always restore body scroll
      // Show the mobile menu button when sidebar is closed
      mobileMenuButton.classList.remove("hidden")
      // Show the arrow button when sidebar is closed (on mobile)
      if (window.innerWidth <= 992) {
        openSidebarArrowBtn.style.display = "flex"
      }
      // Hide close button when sidebar is closed
      pmSidebarCloseBtn.style.display = "none"
    }, 300) // Match this with your CSS transition time
  }
 
  // Hide close button initially
  pmSidebarCloseBtn.style.display = "none"
 
  // Make sure arrow button is visible on mobile
  if (window.innerWidth <= 992) {
    openSidebarArrowBtn.style.display = "flex"
  }
 
  openSidebarArrowBtn.addEventListener("click", openSidebar)
  mobileMenuButton.addEventListener("click", openSidebar)
  pmSidebarOverlay.addEventListener("click", closeSidebar)
  pmSidebarCloseBtn.addEventListener("click", closeSidebar)
 
  // Add swipe gesture support for mobile
  let touchStartX = 0
  let touchEndX = 0
 
  sidebarContainer.addEventListener(
    "touchstart",
    (e) => {
      touchStartX = e.changedTouches[0].screenX
    },
    false,
  )
 
  sidebarContainer.addEventListener(
    "touchend",
    (e) => {
      touchEndX = e.changedTouches[0].screenX
      handleSwipe()
    },
    false,
  )
 
  function handleSwipe() {
    // Swipe left (close sidebar)
    if (touchEndX < touchStartX - 50) {
      closeSidebar()
    }
  }
 
  // Close sidebar if a menu link or action button inside it is clicked
  const sidebarItemsToCloseOnClick = sidebarContainer.querySelectorAll(".sidebar-menu-link, .sidebar-action-button")
  sidebarItemsToCloseOnClick.forEach((item) => {
    item.addEventListener("click", () => {
      if (sidebarContainer.classList.contains("is-open")) {
        closeSidebar()
      }
    })
  })
 
  // Handle resize events to properly manage sidebar state
  window.addEventListener("resize", () => {
    if (window.innerWidth > 992) {
      // On larger screens
      document.body.style.overflow = ""
      mobileMenuButton.classList.add("hidden")
      // Hide arrow button on desktop
      openSidebarArrowBtn.style.display = "none"
    } else {
      // On mobile
      if (!sidebarContainer.classList.contains("is-open")) {
        mobileMenuButton.classList.remove("hidden")
        // Show arrow button on mobile when sidebar is closed
        openSidebarArrowBtn.style.display = "flex"
      } else {
        // Hide arrow button when sidebar is open
        openSidebarArrowBtn.style.display = "none"
      }
    }
  })
 
  // Initial state based on screen size
  if (window.innerWidth <= 992) {
    mobileMenuButton.classList.remove("hidden")
    // Show arrow button on mobile initially
    openSidebarArrowBtn.style.display = "flex"
  } else {
    mobileMenuButton.classList.add("hidden")
    // Hide arrow button on desktop
    openSidebarArrowBtn.style.display = "none"
  }
}
 
// Export shared utilities and variables
export const shared = {
  selectedPodcastId: null,
  svgpodcastmanagement,
}
 
document.getElementById("guests-link").addEventListener("click", (event) => {
  event.preventDefault()
})
 