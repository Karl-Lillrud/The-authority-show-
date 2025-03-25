import { fetchAllEpisodes } from "/static/requests/episodeRequest.js"
import { fetchGuestsByEpisode } from "/static/requests/guestRequests.js"
import { fetchPodcast } from "/static/requests/podcastRequests.js"
import { initTaskManagement } from "/static/js/dashboard/task.js"

document.addEventListener("DOMContentLoaded", () => {
  initWelcomePopup()
  fetchAndDisplayEpisodesWithGuests()
  populateLeaderboard()
})

function initWelcomePopup() {
  const welcomePopup = document.getElementById("welcome-popup")
  const closeWelcomePopup = document.getElementById("close-welcome-popup")
  const getStartedBtn = document.getElementById("get-started-btn")

  welcomePopup.style.display = "flex"

  closeWelcomePopup.addEventListener("click", () => {
    welcomePopup.style.display = "none"
  })

  getStartedBtn.addEventListener("click", () => {
    welcomePopup.style.display = "none"
  })

  welcomePopup.addEventListener("click", (e) => {
    if (e.target === welcomePopup) {
      welcomePopup.style.display = "none"
    }
  })
}

async function fetchAndDisplayEpisodesWithGuests() {
  try {
    const episodes = await fetchAllEpisodes()
    // Only show episodes with active status
    const activeEpisodes = episodes.filter(ep => ep.status === "active")
    const container = document.querySelector(".cards-container")
    const initialEpisodes = activeEpisodes.slice(0, 3)
    let isExpanded = false

    // Initially display only the first 3 active episodes
    await displayEpisodes(initialEpisodes, container)

    // Set up toggle button for view all / view less
    const viewAllBtn = document.querySelector('.episodes-section .view-all')
    viewAllBtn.textContent = "View All"

    viewAllBtn.addEventListener('click', async (e) => {
      e.preventDefault()
      if (!isExpanded) {
        // Expand to show all active episodes
        await displayEpisodes(activeEpisodes, container)
        viewAllBtn.textContent = "View Less"
        isExpanded = true
      } else {
        // Collapse back to original state (first 3 active episodes)
        await displayEpisodes(initialEpisodes, container)
        viewAllBtn.textContent = "View All"
        isExpanded = false
      }
    })
  } catch (error) {
    console.error("Error fetching episodes with guests:", error)
    const container = document.querySelector(".cards-container")
    container.innerHTML = `<div class="error-message">Error loading episodes. Please try again later.</div>`
  }
}

async function displayEpisodes(episodes, container) {
  container.innerHTML = ""
  for (const episode of episodes) {
    const card = createEpisodeCard(episode)
    container.appendChild(card)
    await populatePodcastDetails(card, episode)
    await populateGuestList(card, episode)
  }
  initTaskManagement()
}

function createEpisodeCard(episode) {
  const card = document.createElement("div")
  card.classList.add("episode-card")
  // Use episode.id if available; fallback to episode._id
  card.dataset.episodeId = episode.id || episode._id

  card.innerHTML = `
    <div class="card-header">
      <img class="podcast-logo" src="/static/images/default-podcast-logo.png" alt="Podcast Logo">
      <div class="card-title">
        <h3>${episode.title}</h3>
      </div>
    </div>
    <div class="card-body">
      <h4>Guests:</h4>
      <ul class="guest-list">
        <li>Loading guests...</li>
      </ul>
    </div>
    <div class="card-footer">
      <span>Episode #${episode.episode || "N/A"}</span>
      <button class="toggle-tasks" aria-label="Toggle tasks">+</button>
    </div>
    <div class="tasks-container" style="display: none;">
      <p>Tasks for this episode will be displayed here.</p>
    </div>
  `
  return card
}

async function populatePodcastDetails(card, episode) {
  try {
    const podcastId = episode.podcastId || episode.podcast_id
    if (!podcastId) {
      console.error("Error: Missing podcastId for episode:", episode)
      return
    }
    const podcastResponse = await fetchPodcast(podcastId)
    const podcast = podcastResponse.podcast || {}

    const logoElement = card.querySelector(".podcast-logo")
    if (podcast.logoUrl) {
      logoElement.src = podcast.logoUrl
    }
    logoElement.alt = podcast.podName || "Podcast Logo"
  } catch (error) {
    console.error("Error fetching podcast details:", error)
  }
}

async function populateGuestList(card, episode) {
  try {
    const guestList = card.querySelector(".guest-list")
    const guests = await fetchGuestsByEpisode(episode.id || episode._id)

    guestList.innerHTML = ""
    if (guests.length > 0) {
      guests.forEach((guest) => {
        const li = document.createElement("li")
        li.textContent = guest.name
        guestList.appendChild(li)
      })
    } else {
      const noGuestMsg = document.createElement("li")
      noGuestMsg.textContent = "No guests available"
      guestList.appendChild(noGuestMsg)
    }
  } catch (error) {
    console.error("Error fetching guests for episode:", error)
    const guestList = card.querySelector(".guest-list")
    guestList.innerHTML = "<li>Error loading guest info</li>"
  }
}

function populateLeaderboard() {
  // Replace this mock implementation with an actual data fetch if needed
  console.log("Populating leaderboard with mock data...")
}
