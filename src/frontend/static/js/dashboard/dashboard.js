import { fetchAllEpisodes } from "/static/requests/episodeRequest.js";
import { fetchGuestsByEpisode,editGuestRequest } from "/static/requests/guestRequests.js";
import {
  fetchPodcast,
  fetchPodcasts
} from "/static/requests/podcastRequests.js";
import { initTaskManagement } from "/static/js/dashboard/task.js";
import { svgdashboard } from "./svgdashboard.js";
import { getTeamsRequest } from "/static/requests/teamRequests.js";
import { getActivitiesRequest } from "/static/requests/activityRequests.js";
import { updateEpisode } from "/static/requests/episodeRequest.js";
import { svgIcons } from "./svgdashboard.js";
import { fetchAccount } from "/static/requests/accountRequests.js";

document.addEventListener("DOMContentLoaded", async () => {
  // Cache DOM elements
  const podcastCountElement = document.getElementById("podcast-count");
  const episodeCountElement = document.getElementById("episode-count");
  const guestCountElement = document.getElementById("guest-count");
  const taskCountElement = document.getElementById("task-count");
  const episodesContainer = document.querySelector(".episodes-section .cards-container");
  const activityTimeline = document.querySelector(".activity-section .activity-timeline");
  const createEpisodeButton = document.querySelector(".create-episode.action-button");
  const viewAllEpisodesLink = document.querySelector(".episodes-section .view-all");
  const pendingGuestsPopup = document.getElementById("pending-guests-popup");
  const closePendingGuestsPopup = document.getElementById("close-pending-guests-popup");
  const pendingGuestsList = document.querySelector(".pending-guests-list");
  const guestStatCard = guestCountElement ? guestCountElement.closest(".stat-card") : null;

  // Function to set the page title
  function setPageTitle(title) {
    const pageTitleElement = document.getElementById("page-title");
    if (pageTitleElement) {
      pageTitleElement.textContent = title;
    } else {
      // Fallback if the element is not found, though it should be in header.html
      document.title = title; // Sets the browser tab title
    }
  }

  // Set the page title for the dashboard
  setPageTitle("Dashboard");

  // Function to fetch user account data
  async function fetchUserAccount() {
    try {
      const accountData = await fetchAccount();
      if (accountData && accountData.account) {
        // console.log("User account data:", accountData.account);
        // You can use accountData.account here to display user-specific info if needed
      } else {
        console.error("Failed to fetch user account data or account data is missing.");
      }
    } catch (error) {
      console.error("Error fetching user account:", error);
    }
  }

  // Call the function to fetch user account data
  fetchUserAccount();

  // Function to fetch dashboard data from the backend
  async function fetchDashboardData() {
    try {
      const response = await fetch("/dashboard/data");
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      // console.log("Fetched dashboard data:", data);
      return data;
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
      // Display an error message to the user on the dashboard
      if (episodesContainer) episodesContainer.innerHTML = "<p>Error loading episodes.</p>";
      if (activityTimeline) activityTimeline.innerHTML = "<p>Error loading activity.</p>";
      // Potentially update stat cards to show error or 'N/A'
      if (podcastCountElement) podcastCountElement.textContent = "N/A";
      if (episodeCountElement) episodeCountElement.textContent = "N/A";
      if (guestCountElement) guestCountElement.textContent = "N/A";
      if (taskCountElement) taskCountElement.textContent = "N/A";
      return null; // Return null or an empty structure to prevent further errors
    }
  }

  // Function to render stat cards
  function renderStats(data) {
    if (!data) return; // Guard clause if data fetching failed

    if (podcastCountElement) podcastCountElement.textContent = data.podcast_count || 0;
    if (episodeCountElement) episodeCountElement.textContent = data.episode_count || 0;
    if (guestCountElement) guestCountElement.textContent = data.guest_count || 0;
    if (taskCountElement) taskCountElement.textContent = data.task_count || 0;

    // Handle pending guests notification
    if (data.pending_guests && data.pending_guests.length > 0 && guestStatCard) {
      const notificationIcon = document.createElement("div");
      notificationIcon.className = "notification-icon active"; // 'active' class makes it visible
      notificationIcon.textContent = data.pending_guests.length;
      notificationIcon.title = `${data.pending_guests.length} pending guest invitations`;

      // Append to the notification container within the guest stat card
      const notificationContainer = guestStatCard.querySelector(".notification-container");
      if (notificationContainer) {
        notificationContainer.innerHTML = ""; // Clear previous icon
        notificationContainer.appendChild(notificationIcon);

        // Make the guest stat card clickable to show the popup
        guestStatCard.classList.add("clickable");
        guestStatCard.addEventListener("click", () => {
          renderPendingGuestsPopup(data.pending_guests);
          if (pendingGuestsPopup) pendingGuestsPopup.style.display = "flex";
        });
      } else {
        console.warn("Notification container not found in guest stat card.");
      }
    } else if (guestStatCard) {
      // Clear any existing notification if no pending guests
      const notificationContainer = guestStatCard.querySelector(".notification-container");
      if (notificationContainer) {
        notificationContainer.innerHTML = "";
      }
      guestStatCard.classList.remove("clickable");
      // Potentially remove event listener if it was added
    }
  }

  // Function to render pending guests in the popup
  function renderPendingGuestsPopup(pendingGuests) {
    if (!pendingGuestsList) {
      console.error("Pending guests list element not found.");
      return;
    }
    pendingGuestsList.innerHTML = ""; // Clear previous list

    if (pendingGuests.length === 0) {
      pendingGuestsList.innerHTML = "<li>No pending guest invitations.</li>";
      return;
    }

    pendingGuests.forEach((guest) => {
      const listItem = document.createElement("li");
      listItem.className = "pending-guest-item";

      const guestName = document.createElement("span");
      guestName.className = "guest-name";
      guestName.textContent = guest.name || "Unnamed Guest";

      const guestEmail = document.createElement("span");
      guestEmail.className = "guest-email";
      guestEmail.textContent = guest.email ? `(${guest.email})` : "(No email)";
      
      const guestStatus = document.createElement("span");
      guestStatus.className = `guest-status status-${(guest.status || 'pending').toLowerCase().replace(/\s+/g, '-')}`;
      guestStatus.textContent = guest.status || "Pending";

      listItem.appendChild(guestName);
      listItem.appendChild(guestEmail);
      listItem.appendChild(guestStatus);
      pendingGuestsList.appendChild(listItem);
    });
  }

  // Function to render episode cards
  function renderEpisodes(episodes) {
    if (!episodesContainer) {
      console.warn("Episodes container not found. Skipping episode rendering.");
      return;
    }
    episodesContainer.innerHTML = ""; // Clear existing episodes

    if (!episodes || episodes.length === 0) {
      episodesContainer.innerHTML = "<p>No episodes found.</p>";
      return;
    }

    // Sort episodes by creation date, newest first
    const sortedEpisodes = episodes.sort(
      (a, b) => new Date(b.created_at) - new Date(a.created_at),
    );

    sortedEpisodes.slice(0, 3).forEach((episode) => {
      // Limit to 3 episodes
      const card = document.createElement("div");
      card.className = "episode-card";
      card.dataset.episodeId = episode._id; // Use _id for dataset

      const imageSrc = episode.imageUrl || "/static/images/default.png"; // Use imageUrl, fallback to default

      // Determine status color
      let statusColorClass = "";
      switch ((episode.status || "Unknown").toLowerCase()) {
        case "published":
          statusColorClass = "status-published";
          break;
        case "editing":
        case "edited":
          statusColorClass = "status-editing";
          break;
        case "recorded":
          statusColorClass = "status-recorded";
          break;
        case "not recorded":
        case "not scheduled":
          statusColorClass = "status-not-recorded";
          break;
        default:
          statusColorClass = "status-unknown";
      }

      card.innerHTML = `
        <div class="episode-card-image" style="background-image: url('${imageSrc}');"></div>
        <div class="episode-card-content">
          <h4 class="episode-card-title">${episode.title || "Untitled Episode"}</h4>
          <p class="episode-card-podcast">${episode.podcast_title || "Unknown Podcast"}</p>
          <div class="episode-card-footer">
            <span class="episode-card-status ${statusColorClass}">${episode.status || "Unknown"}</span>
            <span class="episode-card-date">${
              episode.publishDate
                ? new Date(episode.publishDate).toLocaleDateString()
                : "N/A"
            }</span>
          </div>
        </div>
        <div class="episode-card-actions">
          <button class="action-btn view-details" title="View Details">${svgIcons.view}</button>
          <button class="action-btn edit-episode" title="Edit Episode">${svgIcons.edit}</button>
        </div>
      `;

      // Add event listeners for action buttons
      const viewButton = card.querySelector(".view-details");
      if (viewButton) {
        viewButton.addEventListener("click", (e) => {
          e.stopPropagation(); // Prevent card click event
          // console.log("View details for episode:", episode._id);
          // Store episode ID and redirect
          sessionStorage.setItem("selected_episode_id_from_dashboard", episode._id);
          sessionStorage.setItem("selected_podcast_id_from_dashboard", episode.podcast_id);
          window.location.href = "/podcastmanagement"; // Navigate to podcast management page
        });
      }

      const editButton = card.querySelector(".edit-episode");
      if (editButton) {
        editButton.addEventListener("click", (e) => {
          e.stopPropagation(); // Prevent card click event
          // console.log("Edit episode:", episode._id);
          // Store episode ID and redirect for editing
          sessionStorage.setItem("edit_episode_id_from_dashboard", episode._id);
          sessionStorage.setItem("selected_podcast_id_from_dashboard", episode.podcast_id);
          window.location.href = "/podcastmanagement"; // Navigate to podcast management page
        });
      }
      
      // Add click event listener to the card itself to navigate
      card.addEventListener("click", () => {
        // console.log("Card clicked for episode:", episode._id);
        sessionStorage.setItem("selected_episode_id_from_dashboard", episode._id);
        sessionStorage.setItem("selected_podcast_id_from_dashboard", episode.podcast_id);
        window.location.href = "/podcastmanagement";
      });


      if (episodesContainer) episodesContainer.appendChild(card);
    });
  }

  // Function to render activity timeline
  function renderActivity(activities) {
    if (!activityTimeline) {
      console.warn("Activity timeline container not found. Ensure .activity-timeline exists in the DOM.");
      return;
    }
    activityTimeline.innerHTML = ""; // Clear existing activities

    if (!activities || activities.length === 0) {
      const noActivityMessage = document.createElement("p");
      noActivityMessage.textContent = "No recent activity.";
      noActivityMessage.className = "no-activity-message";
      activityTimeline.appendChild(noActivityMessage);
      return;
    }
    
    // Sort activities by timestamp, newest first
    const sortedActivities = activities.sort(
      (a, b) => new Date(b.timestamp) - new Date(a.timestamp),
    );

    sortedActivities.forEach((activity) => {
      const item = document.createElement("div");
      item.className = "activity-item";

      const iconContainer = document.createElement("div");
      iconContainer.className = "activity-icon-container";
      
      let iconSvg = svgIcons.default_activity; // Default icon

      if (activity.type) {
        switch (activity.type.toLowerCase()) {
            case "episode_created":
            case "new_episode":
                iconSvg = svgIcons.episode_created;
                break;
            case "episode_updated":
            case "update_episode":
                iconSvg = svgIcons.episode_updated;
                break;
            case "episode_deleted":
                iconSvg = svgIcons.episode_deleted;
                break;
            case "podcast_created":
                iconSvg = svgIcons.podcast_created;
                break;
            case "podcast_updated":
                iconSvg = svgIcons.podcast_updated;
                break;
            case "guest_invited":
            case "guest_added":
                iconSvg = svgIcons.guest_invited;
                break;
            case "task_completed":
                iconSvg = svgIcons.task_completed;
                break;
            case "user_login":
                 iconSvg = svgIcons.user_login;
                 break;
            case "user_logout":
                 iconSvg = svgIcons.user_logout;
                 break;
            // Add more cases as needed for different activity types
        }
      }
      iconContainer.innerHTML = iconSvg;


      const content = document.createElement("div");
      content.className = "activity-content";

      const description = document.createElement("p");
      description.className = "activity-description";
      description.textContent = activity.description || "No description provided.";

      const timestamp = document.createElement("span");
      timestamp.className = "activity-timestamp";
      timestamp.textContent = new Date(activity.timestamp).toLocaleString();

      content.appendChild(description);
      content.appendChild(timestamp);
      item.appendChild(iconContainer);
      item.appendChild(content);
      activityTimeline.appendChild(item);
    });
  }

  // Function to initialize the dashboard
  async function initializeDashboard() {
    const data = await fetchDashboardData();
    if (data) {
      renderStats(data);
      renderEpisodes(data.episodes); // Make sure data.episodes is passed
      renderActivity(data.activities);
    } else {
      // Handle the case where data is null (e.g., due to a fetch error)
      console.error("Dashboard initialization failed: No data received.");
      // Optionally, display a more prominent error message on the dashboard
      const mainContent = document.querySelector(".main-content");
      if (mainContent) {
        mainContent.innerHTML = `
          <div class="error-container" style="padding: 20px; text-align: center;">
            <h2>Oops! Something went wrong.</h2>
            <p>We couldn't load your dashboard data. Please try refreshing the page or check back later.</p>
          </div>
        `;
      }
    }
  }

  // Event Listeners
  if (createEpisodeButton) {
    createEpisodeButton.addEventListener("click", () => {
      // console.log("Create new episode button clicked");
      sessionStorage.setItem("triggerCreateEpisodeModal", "true");
      window.location.href = "/podcastmanagement";
    });
  }

  if (viewAllEpisodesLink) {
    viewAllEpisodesLink.addEventListener("click", (e) => {
      e.preventDefault();
      // console.log("View all episodes link clicked");
      window.location.href = "/podcastmanagement"; // Navigate to the main podcast management page
    });
  }

  if (closePendingGuestsPopup) {
    closePendingGuestsPopup.addEventListener("click", () => {
      if (pendingGuestsPopup) pendingGuestsPopup.style.display = "none";
    });
  }

  // Click outside popup to close
  if (pendingGuestsPopup) {
    pendingGuestsPopup.addEventListener("click", (event) => {
      if (event.target === pendingGuestsPopup) {
        pendingGuestsPopup.style.display = "none";
      }
    });
  }
  
  // Placeholder for SVG icons - these should be actual SVG strings or loaded from a file
  // Example: svgIcons.podcast = '<svg>...</svg>';
  const statIcons = document.querySelectorAll(".stat-icon .svg-placeholder");
  statIcons.forEach((placeholder) => {
    if (placeholder.classList.contains("podcast-icon")) {
      placeholder.innerHTML = svgIcons.podcast;
    } else if (placeholder.classList.contains("episode-icon")) {
      placeholder.innerHTML = svgIcons.episode;
    } else if (placeholder.classList.contains("guest-icon")) {
      placeholder.innerHTML = svgIcons.guest;
    } else if (placeholder.classList.contains("task-icon")) {
      placeholder.innerHTML = svgIcons.task;
    } else if (placeholder.classList.contains("team-leaderboard-trophy")) {
      placeholder.innerHTML = svgIcons.team_leaderboard_trophy;
    }
  });

  // Initialize the dashboard when the script runs
  initializeDashboard();
});
