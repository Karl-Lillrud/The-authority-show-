import { fetchAllEpisodes } from "/static/requests/episodeRequest.js"
import { fetchGuestsByEpisode } from "/static/requests/guestRequests.js"
import { fetchPodcast } from "/static/requests/podcastRequests.js"

document.addEventListener("DOMContentLoaded", () => {
  // Initialize welcome popup
  initWelcomePopup()

  // Fetch and display episodes
  fetchAndDisplayEpisodesWithGuests()

  // Populate leaderboard with mock data (replace with actual data fetch)
  populateLeaderboard()
})

function initWelcomePopup() {
  const welcomePopup = document.getElementById("welcome-popup")
  const closeWelcomePopup = document.getElementById("close-welcome-popup")
  const getStartedBtn = document.getElementById("get-started-btn")

  // Show popup
  welcomePopup.style.display = "flex"

  // Close popup when clicking close button
  closeWelcomePopup.addEventListener("click", () => {
    welcomePopup.style.display = "none"
  })

  // Close popup when clicking get started button
  getStartedBtn.addEventListener("click", () => {
    welcomePopup.style.display = "none"
  })

  // Close popup when clicking outside
  welcomePopup.addEventListener("click", (e) => {
    if (e.target === welcomePopup) {
      welcomePopup.style.display = "none"
    }
  })
}

async function fetchAndDisplayEpisodesWithGuests() {
  try {
    const episodes = await fetchAllEpisodes() // Fetch all episodes
    const container = document.querySelector(".cards-container")
    container.innerHTML = "" // Clear existing content

    const limitedEpisodes = episodes.slice(0, 3) // Show up to 3 cards

    for (const episode of limitedEpisodes) {
      // Create episode card
      const card = createEpisodeCard(episode)
      container.appendChild(card)

      // Fetch and populate podcast details
      await populatePodcastDetails(card, episode)

      // Fetch and populate guest list
      await populateGuestList(card, episode)
    }
  } catch (error) {
    console.error("Error fetching episodes with guests:", error)
    const container = document.querySelector(".cards-container")
    container.innerHTML = `<div class="error-message">Error loading episodes. Please try again later.</div>`
  }
}

function createEpisodeCard(episode) {
  const card = document.createElement("div")
  card.classList.add("episode-card")
  card.dataset.episodeId = episode._id

  // Card structure
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
      <span>Episode #${episode.episode_number || "N/A"}</span>
      <button class="toggle-tasks">+</button>
    </div>
    <div class="tasks-container" style="display: none;">
      <p>Tasks for this episode will be displayed here.</p>
    </div>
  `

  // Add event listener for toggle tasks button
  const toggleButton = card.querySelector(".toggle-tasks")
  const tasksContainer = card.querySelector(".tasks-container")

  toggleButton.addEventListener("click", () => {
    if (tasksContainer.style.display === "none") {
      tasksContainer.style.display = "block"
      toggleButton.textContent = "-"
    } else {
      tasksContainer.style.display = "none"
      toggleButton.textContent = "+"
    }
  })

  return card
}

async function populatePodcastDetails(card, episode) {
  try {
    const podcastId = episode.podcast_id

    if (!podcastId) {
      console.error("Error: Missing podcastId for episode:", episode)
      return
    }

    const podcastResponse = await fetchPodcast(podcastId)
    const podcast = podcastResponse.podcast || {}

    // Update podcast logo and title
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
    const guests = await fetchGuestsByEpisode(episode._id)

    guestList.innerHTML = "" // Clear loading message

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

