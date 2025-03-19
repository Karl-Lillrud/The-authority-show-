import { fetchPodcast } from "/static/requests/podcastRequests.js";
import { fetchEpisodesByPodcast } from "/static/requests/episodeRequest.js";
import { fetchGuestsRequest } from "/static/requests/guestRequests.js"; // Ensure to use the correct method for fetching guests
import { fetchTasks } from "/static/requests/podtaskRequest.js";
import { getTeamsRequest } from "/static/requests/teamRequests.js";

document.addEventListener("DOMContentLoaded", async () => {
  const podcastId = localStorage.getItem("selectedPodcastId");
  if (!podcastId) {
    console.error("No podcast selected.");
    return;
  }

  try {
    // Fetch podcast details
    const podcastData = await fetchPodcast(podcastId);
    if (!podcastData || !podcastData.podcast) {
      console.error("Failed to fetch podcast details.");
      return;
    }
    const podcast = podcastData.podcast;
    console.log("Podcast Data:", podcast);

    // Display podcast details
    const podcastContainer = document.getElementById("podcast-container");
    podcastContainer.innerHTML = `
      <div class="card">
        <h2>${podcast.podName}</h2>
        <p><strong>Category:</strong> ${podcast.category || 'No category available'}</p>
        <p><strong>Owner:</strong> ${podcast.ownerName || 'No owner available'}</p>
        <p><strong>Host:</strong> ${podcast.hostName || 'No host available'}</p>
        <p><strong>Description:</strong> ${podcast.description || 'No description available'}</p>
      </div>
    `;

    // Fetch episodes and display
    const episodesData = await fetchEpisodesByPodcast(podcastId);
    const episodesDiv = document.getElementById("episodes-container");
    if (episodesData && episodesData.length > 0) {
      episodesDiv.innerHTML = episodesData.map(
        episode => `
          <div class="card">
            <h4>${episode.title}</h4>
            <p><strong>Duration:</strong> ${episode.duration || 'N/A'}</p>
            <p><strong>Release Date:</strong> ${episode.publishDate || 'N/A'}</p>
          </div>
        `
      ).join("");
    } else {
      episodesDiv.innerHTML = "<p>No episodes found for this podcast.</p>";
    }

    // Fetch guests, filter, and display
    const guests = await fetchGuestsRequest();
    const filteredGuests = guests.filter(guest => guest.podcastId === podcastId);
    const guestsDiv = document.getElementById("guests-container");
    if (filteredGuests.length > 0) {
      guestsDiv.innerHTML = filteredGuests.map(
        guest => `
          <div class="card">
            <h4>${guest.name}</h4>
            <p><strong>Bio:</strong> ${guest.bio || 'No bio available'}</p>
            <p><strong>Social Links:</strong> ${guest.socialLinks || 'None'}</p>
          </div>
        `
      ).join("");
    } else {
      guestsDiv.innerHTML = "<p>No guests found for this podcast.</p>";
    }

    // Fetch tasks and filter by podcastId, then display
    const tasksData = await fetchTasks();
    const filteredTasks = tasksData.filter(task => task.podcastId === podcastId);
    const tasksDiv = document.getElementById("tasks-container");
    if (filteredTasks.length > 0) {
      tasksDiv.innerHTML = filteredTasks.map(
        task => `
          <div class="card">
            <h4>${task.taskName}</h4>
            <p><strong>Due Date:</strong> ${task.dueDate || 'N/A'}</p>
            <p><strong>Status:</strong> ${task.status || 'N/A'}</p>
          </div>
        `
      ).join("");
    } else {
      tasksDiv.innerHTML = "<p>No tasks found for this podcast.</p>";
    }

    // Fetch teams, filter by podcast's teamId, and display
    const teams = await getTeamsRequest();
    const filteredTeams = teams.filter(team => team._id === podcast.teamId);
    const teamsDiv = document.getElementById("teams-container");
    if (filteredTeams.length > 0) {
      const team = filteredTeams[0]; // Assuming one team per podcast
      teamsDiv.innerHTML = `
        <div class="card">
          <h4>${team.name}</h4>
          <p><strong>Members:</strong> ${team.members.join(", ")}</p>
          <p><strong>Description:</strong> ${team.description || 'No description available'}</p>
        </div>
      `;
    } else {
      teamsDiv.innerHTML = "<p>No teams found for this podcast.</p>";
    }

  } catch (error) {
    console.error("Error fetching data:", error);
  }
});
