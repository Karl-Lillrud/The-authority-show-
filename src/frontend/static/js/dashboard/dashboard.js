import { fetchAllEpisodes } from "/static/requests/episodeRequest.js";
import { fetchGuestsByEpisode } from "/static/requests/guestRequests.js";
import {
  fetchPodcast,
  fetchPodcasts
} from "/static/requests/podcastRequests.js";
import { initTaskManagement } from "/static/js/dashboard/task.js";
import { svgdashboard } from "./svgdashboard.js";
import { getTeamsRequest } from "/static/requests/teamRequests.js";
import { getActivitiesRequest } from "/static/requests/activityRequests.js";

document.addEventListener("DOMContentLoaded", async () => {
  try {
    // Kör alla asynkrona datahämtningar parallellt
    await Promise.all([
      fetchAndDisplayEpisodesWithGuests(),
      fetchAndDisplayPodcastCount(),
      fetchAndDisplayEpisodeCount(),
      fetchAndDisplayGuestCount(),
      createTeamLeaderBoardRows(),
      fetchAndDisplayActivities()
    ]);

    // Initiera UI-komponenter efter att DOM är uppdaterad
    initializeSvgIcons();
    initProgressCircles();
    initDashboardActions();
    updateStatCounts();
    
  } catch (error) {
    console.error("Error initializing dashboard:", error);
  }

});

function initProgressCircles() {
  const progressCircles = document.querySelectorAll(".progress-circle");
  progressCircles.forEach((circle) => {
    const progress = circle.getAttribute("data-progress");
    if (progress) {
      circle.style.setProperty("--progress", progress);
    }
  });
}

function initDashboardActions() {
  const scheduleEpisodeBtn = document.querySelector(".schedule-episode");
  const createEpisodeBtn = document.querySelector(".create-episode");

  if (scheduleEpisodeBtn) {
    scheduleEpisodeBtn.addEventListener("click", () => {
      window.location.href = "/episode/new";
    });
  }

  if (createEpisodeBtn) {
    createEpisodeBtn.addEventListener("click", () => {
      window.location.href = "/podcastmanagement?openCreateEpisode=true"; // Redirect with query parameter
    });
  }
}

function initializeSvgIcons() {
  const iconSelectors = [
    { selector: ".schedule-episode-icon", svg: svgdashboard.scheduleEpisode },
    { selector: ".podcast-icon", svg: svgdashboard.podcastIcon },
    { selector: ".episode-icon", svg: svgdashboard.episodeIcon },
    { selector: ".guest-icon", svg: svgdashboard.guestIcon },
    { selector: ".task-icon", svg: svgdashboard.taskIcon },
    { selector: ".completed-icon", svg: svgdashboard.completedIcon },
    { selector: ".scheduled-icon", svg: svgdashboard.scheduledIcon },
    { selector: ".published-icon", svg: svgdashboard.publishedIcon },
    { selector: ".pending-icon", svg: svgdashboard.pendingIcon },
    { selector: ".episode-created-icon", svg: svgdashboard.episodeCreatedIcon },
    { selector: ".episode-updated-icon", svg: svgdashboard.episodeUpdatedIcon },
    { selector: ".episode-deleted-icon", svg: svgdashboard.episodeDeletedIcon },
    { selector: ".team-created-icon", svg: svgdashboard.teamCreatedIcon },
    { selector: ".team-deleted-icon", svg: svgdashboard.teamDeletedIcon },
    { selector: ".tasks-added-icon", svg: svgdashboard.tasksAddedIcon },
    { selector: ".podcast-created-icon", svg: svgdashboard.podcastCreatedIcon },
    { selector: ".podcast-deleted-icon", svg: svgdashboard.podcastDeletedIcon }
  ];

  iconSelectors.forEach(({ selector, svg }) => {
    // Use querySelectorAll to update all matching elements
    document.querySelectorAll(selector).forEach((element) => {
      element.innerHTML = svg;
    });
  });
}

function updateStatCounts() {
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

async function fetchAndDisplayPodcastCount() {
  try {
    const allPodcasts = await fetchPodcasts();
    const podcastValue = document.getElementById("podcast-count");
    if (podcastValue) {
      podcastValue.innerHTML = allPodcasts.podcast.length;
    } else {
      console.warn("Element with ID podcast-count not found.");
    }
  } catch (error) {
    console.error("Error fetching podcast data:", error);
  }
}

async function fetchAndDisplayEpisodeCount() {
  try {
    const allEpisodes = await fetchAllEpisodes();
    const episodeValue = document.getElementById("episode-count");
    if (episodeValue) {
      episodeValue.innerHTML = allEpisodes.length;
    } else {
      console.warn("Element with ID episode-count not found.");
    }
  } catch (error) {
    console.error("Error fetching episode data:", error);
  }
}

async function fetchAndDisplayGuestCount() {
  try {
    const allGuests = await fetchGuestsRequest();
    const guestValue = document.getElementById("guest-count");
    if (guestValue) {
      guestValue.innerHTML = allGuests.length;
    } else {
      console.warn("Element with ID guest-count not found.");
    }
  } catch (error) {
    console.error("Error fetching guest data:", error);
  }
}

async function createTeamLeaderBoardRows() {
  try {
    const myTeam = await getTeamsRequest();
    const teamContainer = document.querySelector(".leaderboard-body");
    if (!teamContainer) {
      console.warn("Leaderboard body container not found.");
      return;
    }
    teamContainer.innerHTML = "";

    const generateRandomData = () => ({
      completedTasks: Math.floor(Math.random() * 50) + 1,
      points: Math.floor(Math.random() * 4901) + 100,
      monthsWon: Math.floor(Math.random() * 25) + 1,
      goalPercentage: Math.floor(Math.random() * 85) + 1
    });

    const teamWithRandomData = myTeam.map((member) => {
      const randomData = generateRandomData();
      return { ...member, ...randomData };
    });

    const sortedTeam = teamWithRandomData.sort(
      (a, b) => b.goalPercentage - a.goalPercentage
    );

    const topThreeTeam = sortedTeam.slice(0, 3);

    topThreeTeam.forEach((member) => {
      const initials = member.name
        .split(" ")
        .map((word) => word[0])
        .join("")
        .toUpperCase();

      const row = `
                <tr>
                    <td>
                        <div class="member-info">
                            <div class="member-avatar">${initials}</div>
                            <span>${member.name}</span>
                        </div>
                    </td>
                    <td>${member.completedTasks}</td>
                    <td>
                        <div class="points">
                            <span>${member.points.toLocaleString()}</span>
                            <div class="progress-bar">
                                <div class="progress" style="width: ${
                                  member.goalPercentage
                                }%"></div>
                            </div>
                        </div>
                    </td>
                    <td>${member.monthsWon}</td>
                    <td>
                        <div class="goal-progress">
                            <span>${member.goalPercentage}%</span>
                            <div class="progress-circle" data-progress="${
                              member.goalPercentage
                            }"></div>
                        </div>
                    </td>
                </tr>
            `;
      teamContainer.insertAdjacentHTML("beforeend", row);
    });

    initProgressCircles();
  } catch (error) {
    console.error("Error fetching team data:", error);
  }
}

async function fetchAndDisplayEpisodesWithGuests() {
  try {
    const episodes = await fetchAllEpisodes();
    const activeEpisodes = episodes.filter(
      (ep) =>
        ep.status === "Not Recorded" ||
        ep.status === "Not Scheduled" ||
        ep.status === "Recorded" ||
        ep.status === "Edited"
    );
    const container = document.querySelector(".cards-container");
    if (!container) {
      console.warn("Cards container not found.");
      return;
    }
    const initialEpisodes = activeEpisodes.slice(0, 3);
    let isExpanded = false;

    await displayEpisodes(initialEpisodes, container);

    const viewAllBtn = document.querySelector(".episodes-section .view-all");
    if (viewAllBtn) {
      viewAllBtn.textContent = "View All";
      viewAllBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        if (!isExpanded) {
          await displayEpisodes(activeEpisodes, container);
          viewAllBtn.textContent = "View Less";
          isExpanded = true;
        } else {
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

    const logoElement = card.querySelector(".podcast-logo");
    logoElement.src = `/placeholder.svg?height=50&width=50`;

    const guestList = card.querySelector(".guest-list");
    guestList.innerHTML = "";

    episode.guests.forEach((guest) => {
      const li = document.createElement("li");
      li.textContent = guest;
      guestList.appendChild(li);
    });
  });

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

  initTaskManagement();
}

function createEpisodeCard(episode) {
  const card = document.createElement("div");
  card.classList.add("episode-card");
  card.dataset.episodeId = episode.id || episode._id;

  let statusText = episode.status || "Not Scheduled";
  let statusClass = "status-" + statusText.toLowerCase().replace(/\s+/g, "-");
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
  return date.toLocaleDateString("en-US", {
    day: "numeric",
    month: "short",
    year: "numeric"
  });
}

function getRandomProgress() {
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

async function fetchAndDisplayActivities() {
  try {
    const timelineContainer = document.querySelector(".activity-timeline");
    if (!timelineContainer) {
      console.error(
        "Activity timeline container not found. Ensure .activity-timeline exists in the DOM."
      );
      return;
    }

    const activities = await getActivitiesRequest();
    timelineContainer.innerHTML = "";

    if (activities.length === 0) {
      timelineContainer.innerHTML = `<p class="no-activities-message">No recent activities found.</p>`;
      return;
    }

    // Only show the first 5 activities, but allow scroll for more
    activities.slice(0, 5).forEach((activity) => {
      const iconClass = getActivityIconClass(activity.type);
      const timelineItem = `
                <div class="timeline-item">
                    <div class="timeline-icon ${iconClass}">
                        <span class="svg-placeholder ${iconClass}-icon"></span>
                    </div>
                    <div class="timeline-content">
                        <h4>${formatActivityType(activity.type)}</h4>
                        <p>${activity.description}</p>
                        <span class="timeline-time">${formatDate(
                          activity.createdAt
                        )}</span>
                    </div>
                </div>
            `;
      timelineContainer.insertAdjacentHTML("beforeend", timelineItem);
    });

    // If there are more than 5, show the rest (hidden by scroll)
    if (activities.length > 5) {
      activities.slice(5).forEach((activity) => {
        const iconClass = getActivityIconClass(activity.type);
        const timelineItem = `
                  <div class="timeline-item">
                      <div class="timeline-icon ${iconClass}">
                          <span class="svg-placeholder ${iconClass}-icon"></span>
                      </div>
                      <div class="timeline-content">
                          <h4>${formatActivityType(activity.type)}</h4>
                          <p>${activity.description}</p>
                          <span class="timeline-time">${formatDate(
                            activity.createdAt
                          )}</span>
                      </div>
                  </div>
              `;
        timelineContainer.insertAdjacentHTML("beforeend", timelineItem);
      });
    }

    initializeSvgIcons();
  } catch (error) {
    console.error("Error fetching activities:", error);
    const timelineContainer = document.querySelector(".activity-timeline");
    if (timelineContainer) {
      timelineContainer.innerHTML = `<p class="error-message">Error loading activities. Please try again later.</p>`;
    } else {
      console.error("Activity timeline container not found in error handler.");
    }
  }
}

function getActivityIconClass(activityType) {
  const iconMap = {
    episode_created: "episode-created",
    episode_updated: "episode-updated",
    episode_deleted: "episode-deleted",
    team_created: "team-created",
    team_deleted: "team-deleted",
    tasks_added: "tasks-added",
    podcast_created: "podcast-created",
    podcast_deleted: "podcast-deleted"
  };
  return iconMap[activityType] || "pending";
}

function formatActivityType(type) {
  if (type === "podcast_created") return "Podcast Created";
  return type
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export async function refreshDashboardStats() {
  await Promise.all([
    fetchAndDisplayPodcastCount(),
    fetchAndDisplayEpisodeCount(),
    fetchAndDisplayGuestCount(),
    // Add more stat refreshers if needed
  ]);
  updateStatCounts();
}