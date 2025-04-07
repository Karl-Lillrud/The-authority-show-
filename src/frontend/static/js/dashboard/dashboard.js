import { fetchAllEpisodes } from "/static/requests/episodeRequest.js";
import { fetchGuestsByEpisode } from "/static/requests/guestRequests.js";
import { fetchPodcast, fetchPodcasts } from "/static/requests/podcastRequests.js";
import { fetchAccount, updateAccount } from "/static/requests/accountRequests.js";
import { initTaskManagement } from "/static/js/dashboard/task.js";

document.addEventListener("DOMContentLoaded", () => {
  initWelcomePopup();
  fetchAndDisplayEpisodesWithGuests();
  initProgressCircles();
  initDashboardActions();
  updateStatCounts();
});

async function initWelcomePopup() {
  try {
    const result = await fetchAccount();
    const account = result.account;
    if (account.isFirstLogin) {
      const welcomePopup = document.getElementById("welcome-popup");
      const closeWelcomePopup = document.getElementById("close-welcome-popup");
      const getStartedBtn = document.getElementById("get-started-btn");

      if (!welcomePopup) return;

      welcomePopup.style.display = "flex";

      closeWelcomePopup.addEventListener("click", () => {
        welcomePopup.style.display = "none";
        disableWelcomePopup();
      });

      getStartedBtn.addEventListener("click", () => {
        welcomePopup.style.display = "none";
        disableWelcomePopup();
      });

      welcomePopup.addEventListener("click", (e) => {
        if (e.target === welcomePopup) {
          welcomePopup.style.display = "none";
          disableWelcomePopup();
        }
      });
          return;
    }
  } catch (error) {
    console.error("Error initializing welcome popup:", error);
  }
}

async function disableWelcomePopup() {
  try {
    const data = {
      isFirstLogin: false
    }
    await updateAccount(data);

  }catch (error) {
    console.error("Error disabling welcome popup:", error);
  }
}

function initProgressCircles() {
  const progressCircles = document.querySelectorAll(".progress-circle");

  progressCircles.forEach((circle) => {
    const progress = circle.getAttribute("data-progress");
    circle.style.setProperty("--progress", progress + "%");
  });
}

function initDashboardActions() {
  const createPodcastBtn = document.querySelector(".create-podcast");
  const scheduleEpisodeBtn = document.querySelector(".schedule-episode");

  if (createPodcastBtn) {
    createPodcastBtn.addEventListener("click", () => {
      window.location.href = "/podcast/new";
    });
  }

  if (scheduleEpisodeBtn) {
    scheduleEpisodeBtn.addEventListener("click", () => {
      window.location.href = "/episode/new";
    });
  }
}

function updateStatCounts() {
  // Animate count up for stats
  const statValues = document.querySelectorAll(".stat-value");

  statValues.forEach((stat) => {
    const finalValue = parseInt(stat.textContent);
    animateCount(stat, 0, finalValue, 1500);
  });
}

function animateCount(element, start, end, duration) {
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    const currentCount = Math.floor(progress * (end - start) + start);
    element.textContent = currentCount;
    if (progress < 1) {
      window.requestAnimationFrame(step);
    }
  };
  window.requestAnimationFrame(step);
}

async function fetchAndDisplayEpisodesWithGuests() {
  try {
    const episodes = await fetchAllEpisodes();
    // Only show episodes with active status
    const activeEpisodes = episodes.filter(
      (ep) =>
        ep.status === "Not Recorded" ||
        ep.status === "Not Scheduled" ||
        ep.status === "Recorded" ||
        ep.status === "Edited"
    );
    const container = document.querySelector(".cards-container");
    const initialEpisodes = activeEpisodes.slice(0, 3);
    let isExpanded = false;

    // Initially display only the first 3 active episodes
    await displayEpisodes(initialEpisodes, container);

    // Set up toggle button for view all / view less
    const viewAllBtn = document.querySelector(".episodes-section .view-all");
    if (viewAllBtn) {
      viewAllBtn.textContent = "View All";

      viewAllBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        if (!isExpanded) {
          // Expand to show all active episodes
          await displayEpisodes(activeEpisodes, container);
          viewAllBtn.textContent = "View Less";
          isExpanded = true;
        } else {
          // Collapse back to original state (first 3 active episodes)
          await displayEpisodes(initialEpisodes, container);
          viewAllBtn.textContent = "View All";
          isExpanded = false;
        }
      });
    }
  } catch (error) {
    console.error("Error fetching episodes with guests:", error);
    const container = document.querySelector(".cards-container");
    if (container) {
      container.innerHTML = `<div class="error-message">Error loading episodes. Please try again later.</div>`;
    }

    // Display sample episodes for demo purposes
    displaySampleEpisodes();
  }
}

function displaySampleEpisodes() {
  const container = document.querySelector(".cards-container");
  if (!container) return;

  const sampleEpisodes = [
    {
      id: "ep1",
      title: "Marketing Insights with Sarah Johnson",
      status: "Recorded",
      recordingDate: "2023-10-18",
      podcastName: "Business Insights",
      guests: ["Sarah Johnson", "Michael Chen"]
    },
    {
      id: "ep2",
      title: "Tech Trends 2023",
      status: "Not Recorded",
      recordingDate: "2023-10-25",
      podcastName: "Tech Talk",
      guests: ["Alex Turner", "Emily Roberts"]
    },
    {
      id: "ep3",
      title: "Startup Success Stories",
      status: "Edited",
      recordingDate: "2023-10-15",
      podcastName: "Entrepreneur Hour",
      guests: ["David Miller", "Lisa Wong"]
    }
  ];

  container.innerHTML = "";

  sampleEpisodes.forEach((episode) => {
    const card = createEpisodeCard(episode);
    container.appendChild(card);

    // Add sample podcast logo
    const logoElement = card.querySelector(".podcast-logo");
    logoElement.src = `/placeholder.svg?height=50&width=50`;

    // Add sample guests
    const guestList = card.querySelector(".guest-list");
    guestList.innerHTML = "";

    episode.guests.forEach((guest) => {
      const li = document.createElement("li");
      li.textContent = guest;
      guestList.appendChild(li);
    });
  });

  // Initialize task management after creating cards
  initTaskManagement();
}

async function displayEpisodes(episodes, container) {
  if (!container) return;

  container.innerHTML = "";

  if (episodes.length === 0) {
    container.innerHTML = `<div class="empty-message">No active episodes found.</div>`;
    return;
  }

  for (const episode of episodes) {
    const card = createEpisodeCard(episode);
    container.appendChild(card);
    await populatePodcastDetails(card, episode);
    await populateGuestList(card, episode);
  }

  // Initialize task management after creating all cards
  initTaskManagement();
}

function createEpisodeCard(episode) {
  const card = document.createElement("div");
  card.classList.add("episode-card");
  // Use episode.id if available; fallback to episode._id
  card.dataset.episodeId = episode.id || episode._id;

  // Determine status display
  let statusText = episode.status || "Not Scheduled";
  let statusClass = "status-" + statusText.toLowerCase().replace(/\s+/g, "-");

  // Use English status directly
  let englishStatus = statusText;

  card.innerHTML = `
    <div class="card-header">
      <img class="podcast-logo" src="/static/images/default-podcast-logo.png" alt="Podcast Logo">
      <div class="card-title">
        <h3>${episode.title}</h3>
        <div class="episode-meta">
          <span class="episode-status ${statusClass}">${englishStatus}</span>
          <span class="episode-date">${formatDate(
            episode.recordingDate || episode.createdAt || new Date()
          )}</span>
        </div>
      </div>
    </div>
    <div class="card-body">
      <h4>Guests</h4>
      <ul class="guest-list">
        <li>Loading guests...</li>
      </ul>
    </div>
    <div class="card-footer">
      <div class="episode-progress">
        <div class="progress-bar">
          <div class="progress" style="width: ${getRandomProgress()}%"></div>
        </div>
      </div>
      <button class="toggle-tasks" aria-label="Toggle tasks">+</button>
    </div>
    <div class="tasks-container" style="display: none;">
      <h4>Tasks</h4>
      <div class="task-actions">
        <button class="task-action-btn import-tasks">Import</button>
        <button class="task-action-btn add-task">Add Task</button>
      </div>
      <div class="task-list">
        <p class="no-tasks-message">No tasks yet. Add a task or import default tasks.</p>
      </div>
      <div class="task-workflow-actions">
        <button class="btn save-workflow-btn">Save Workflow</button>
        <button class="btn import-workflow-btn">Import Workflow</button>
      </div>
    </div>
  `;
  return card;
}

function formatDate(dateString) {
  const date = new Date(dateString);
  // Format date in English style
  return date.toLocaleDateString("en-US", {
    day: "numeric",
    month: "short",
    year: "numeric"
  });
}

function getRandomProgress() {
  // For demo purposes, return a random progress percentage
  return Math.floor(Math.random() * 100);
}

async function populatePodcastDetails(card, episode) {
  try {
    const podcastId = episode.podcastId || episode.podcast_id;
    if (!podcastId) {
      console.error("Error: Missing podcastId for episode:", episode);
      return;
    }
    const podcastResponse = await fetchPodcast(podcastId);
    const podcast = podcastResponse.podcast || {};

    const logoElement = card.querySelector(".podcast-logo");
    if (podcast.logoUrl) {
      logoElement.src = podcast.logoUrl;
    }
    logoElement.alt = podcast.podName || "Podcast Logo";
  } catch (error) {
    console.error("Error fetching podcast details:", error);
  }
}

async function populateGuestList(card, episode) {
  try {
    const guestList = card.querySelector(".guest-list");
    if (!guestList) return;

    const guests = await fetchGuestsByEpisode(episode.id || episode._id);

    guestList.innerHTML = "";
    if (guests.length > 0) {
      guests.forEach((guest) => {
        const li = document.createElement("li");
        li.textContent = guest.name;
        guestList.appendChild(li);
      });
    } else {
      const noGuestMsg = document.createElement("li");
      noGuestMsg.textContent = "No guests available";
      guestList.appendChild(noGuestMsg);
    }
  } catch (error) {
    console.error("Error fetching guests for episode:", error);
    const guestList = card.querySelector(".guest-list");
    if (guestList) {
      guestList.innerHTML = "<li>Error loading guest information</li>";
    }
  }
}
