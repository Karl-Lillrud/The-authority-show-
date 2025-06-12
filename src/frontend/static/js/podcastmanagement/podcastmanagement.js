import { initPodcastFunctions } from "./podcast-functions.js"
import { initEpisodeFunctions } from "./episode-functions.js"
import { initGuestFunctions } from "./guest-functions.js"
import { svgpodcastmanagement } from "./svgpodcastmanagement.js"
import { showNotification } from "../components/notifications.js"
import { initEmailConfigFunctions } from "./emailconfig-functions.js"
 
console.log("podcastmanagement.js loaded")
 
// Utility functions
function initializeSvgIcons() {
  const backToDashboardIcon = document.getElementById("back-to-dashboard-icon");
  if (backToDashboardIcon) backToDashboardIcon.innerHTML = svgpodcastmanagement.backToDashboard;

  const podcastsIcon = document.getElementById("podcasts-icon");
  if (podcastsIcon) podcastsIcon.innerHTML = svgpodcastmanagement.podcasts;

  const episodesIcon = document.getElementById("episodes-icon");
  if (episodesIcon) episodesIcon.innerHTML = svgpodcastmanagement.episodes;

  const guestsIcon = document.getElementById("guests-icon");
  if (guestsIcon) guestsIcon.innerHTML = svgpodcastmanagement.guests;

  const addIconPodcast = document.getElementById("add-icon-podcast");
  if (addIconPodcast) addIconPodcast.innerHTML = svgpodcastmanagement.add;

  const addIconEpisode = document.getElementById("add-icon-episode");
  if (addIconEpisode) addIconEpisode.innerHTML = svgpodcastmanagement.add;

  const addIconGuest = document.getElementById("add-icon-guest");
  if (addIconGuest) addIconGuest.innerHTML = svgpodcastmanagement.add;
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

  // Check for 'openAddGuest' query parameter
  const openAddGuest = urlParams.get("openAddGuest");
  const episodeIdFromQuery = urlParams.get("episodeId");
  const podcastIdFromQuery = urlParams.get("podcastId");

  if (openAddGuest === "true") {
    if (episodeIdFromQuery) {
      shared.selectedEpisodeIdForGuestModal = episodeIdFromQuery;
    }
    if (podcastIdFromQuery) {
      shared.selectedPodcastIdForGuestModal = podcastIdFromQuery;
    }
    
    const addGuestButton = document.getElementById("add-guest-btn"); // The button in the sidebar
    if (addGuestButton) {
      addGuestButton.click(); // Simulate click to open the popup via existing mechanism
    }
    // Clean up query params to prevent re-triggering on refresh if not desired
    // Consider if this is needed or if the modal clearing shared vars is enough
    // window.history.replaceState({}, document.title, window.location.pathname + window.location.hash);
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
  selectedEpisodeIdForGuestModal: null, 
  selectedPodcastIdForGuestModal: null, 
  svgpodcastmanagement,
}
 
document.getElementById("guests-link").addEventListener("click", (event) => {
  event.preventDefault()
})

document.addEventListener("DOMContentLoaded", function () {
  const addPodcastModal = document.getElementById("addPodcastModal");
  const openAddPodcastModalBtn = document.getElementById(
    "openAddPodcastModalBtn"
  );
  const closeAddPodcastModalBtn = document.getElementById(
    "closeAddPodcastModalBtn"
  );
  const cancelAddPodcastBtn = document.getElementById("cancelAddPodcastBtn");
  const connectCalendarModalBtn = document.getElementById(
    "connect-calendar-modal-btn" // This ID must match the button in your HTML
  );
  const addPodcastForm = document.getElementById("addPodcastForm");

  if (openAddPodcastModalBtn) {
    openAddPodcastModalBtn.addEventListener("click", function () {
      if (addPodcastModal) addPodcastModal.style.display = "flex";
    });
  }

  if (closeAddPodcastModalBtn) {
    closeAddPodcastModalBtn.addEventListener("click", function () {
      if (addPodcastModal) addPodcastModal.style.display = "none";
    });
  }

  if (cancelAddPodcastBtn) {
    cancelAddPodcastBtn.addEventListener("click", function () {
      if (addPodcastModal) addPodcastModal.style.display = "none";
    });
  }

  // Close modal if clicked outside the form-box
  if (addPodcastModal) {
    addPodcastModal.addEventListener("click", function (event) {
      if (event.target === addPodcastModal) {
        addPodcastModal.style.display = "none";
      }
    });
  }

  // Event listener for the "Connect Google Calendar" button in the modal
  if (connectCalendarModalBtn) {
    connectCalendarModalBtn.addEventListener("click", function() {
      // Redirect to the Google Calendar OAuth flow
      window.location.href = "/connect_calendar";
    });
  }
  
  // Calendar info button and tooltip functionality
  const calendarInfoBtn = document.getElementById("calendar-info-btn");
  const calendarInfoTooltip = document.getElementById("calendar-info-tooltip");
  const tooltipCloseBtn = document.querySelector(".tooltip-close-btn");
  
  if (calendarInfoBtn && calendarInfoTooltip) {
    // Show tooltip when info button is clicked
    calendarInfoBtn.addEventListener("click", function(event) {
      event.stopPropagation(); // Prevent click from bubbling to document
      calendarInfoTooltip.style.display = "block";
    });
    
    // Hide tooltip when close button is clicked
    if (tooltipCloseBtn) {
      tooltipCloseBtn.addEventListener("click", function(event) {
        event.stopPropagation(); // Prevent click from bubbling
        calendarInfoTooltip.style.display = "none";
      });
    }
    
    // Hide tooltip when clicking outside
    document.addEventListener("click", function(event) {
      if (calendarInfoTooltip.style.display === "block" && 
          !calendarInfoTooltip.contains(event.target) && 
          event.target !== calendarInfoBtn) {
        calendarInfoTooltip.style.display = "none";
      }
    });
  }
  
  if (addPodcastForm) {
    addPodcastForm.addEventListener("submit", function (event) {
      event.preventDefault();
      // Logic to handle new podcast submission
      // This is placeholder logic, adapt to your actual implementation
      const formData = new FormData(addPodcastForm);
      const data = Object.fromEntries(formData.entries());
      console.log("Submitting new podcast:", data);
      // Example fetch:
      // fetch('/api/podcasts', { 
      //   method: 'POST', 
      //   body: JSON.stringify(data), 
      //   headers: {'Content-Type': 'application/json'} 
      // })
      // .then(response => response.json())
      // .then(result => {
      //   console.log('Podcast created:', result);
      //   if (addPodcastModal) addPodcastModal.style.display = 'none';
      //   // Optionally, refresh podcast list or give user feedback
      // })
      // .catch(error => console.error('Error creating podcast:', error));
      alert("Podcast creation logic needs to be implemented here.");
    });
  }

  // Placeholder for any other functions like loading podcasts
  // function loadPodcasts() {
  //   console.log("Loading podcasts...");
  //   // Fetch and display podcasts
  // }
  // if (document.getElementById("podcastListContainer")) {
  //    loadPodcasts();
  // }
});

// Add this to your DOMContentLoaded event handler
document.addEventListener("DOMContentLoaded", function() {
  // Event listener for the Connect Google Calendar button
  const connectCalendarModalBtn = document.getElementById("connect-calendar-modal-btn");
  if (connectCalendarModalBtn) {
    connectCalendarModalBtn.addEventListener("click", function() {
      window.location.href = "/connect_calendar";
    });
  }
  
  // Question mark tooltip functionality
  const calendarInfoBtn = document.getElementById("calendar-info-btn");
  const tooltipContent = document.getElementById("calendar-tooltip-content");
  
  if (calendarInfoBtn && tooltipContent) {
    let tooltipVisible = false;
    
    // Toggle tooltip display on question mark click
    calendarInfoBtn.addEventListener("click", function(event) {
      event.stopPropagation();
      tooltipVisible = !tooltipVisible;
      
      if (tooltipVisible) {
        tooltipContent.classList.add("active");
      } else {
        tooltipContent.classList.remove("active");
      }
    });
    
    // Hide tooltip when clicking elsewhere
    document.addEventListener("click", function(event) {
      if (tooltipVisible && event.target !== calendarInfoBtn && !tooltipContent.contains(event.target)) {
        tooltipContent.classList.remove("active");
        tooltipVisible = false;
      }
    });
  }
});
