import { fetchPodcast } from "/static/requests/podcastRequests.js";
import { fetchEpisodesByPodcast } from "/static/requests/episodeRequest.js";
import { fetchGuestsRequest } from "/static/requests/guestRequests.js";
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
    const podcastData = await fetchPodcast(podcastId).catch(error => {
      console.error("Failed to fetch podcast details:", error);
      return null;
    });
    if (!podcastData || !podcastData.podcast) {
      console.error("Failed to fetch podcast details.");
      return;
    }
    const podcast = podcastData.podcast;
    console.log("Podcast Data:", podcast);

    // Display podcast details
    const podcastContainer = document.getElementById("podcast-container");
    podcastContainer.innerHTML = `
      <img src="${podcast.logoUrl || '/static/images/default-podcast.jpg'}" alt="${podcast.podName}" class="podcast-logo">
      <div class="podcast-info">
        <h1>${podcast.podName}</h1>
        <p class="podcast-category">${podcast.category || 'No category available'}</p>
        <p class="podcast-host">Hosted by ${podcast.hostName || 'No host available'}</p>
        <p class="podcast-description">${podcast.description || 'No description available'}</p>
      </div>
    `;

    // Fetch episodes and display with Transcript button
    const episodesData = await fetchEpisodesByPodcast(podcastId).catch(error => {
      console.error("Failed to fetch episodes:", error);
      return [];
    });
    const episodesDiv = document.getElementById("episodes-container");

    // Update episode template
    const episodeTemplate = episode => {
      const episodeId = episode.id || episode._id || "unknown";
      const audioUrl = episode.audioUrl || '';
      
      return `
        <div class="episode-card">
          <div class="episode-content">
            <h3 class="episode-title">${episode.title}</h3>
            <div class="episode-meta">
              <span class="duration-badge">${episode.duration || 'N/A'}</span>
              <span class="release-date">${formatDate(episode.publishDate)}</span>
            </div>
            <div class="episode-actions">
              ${audioUrl ? `
                <audio controls class="episode-audio">
                  <source src="${audioUrl}" type="audio/mpeg">
                  Your browser does not support the audio element.
                </audio>
              ` : ''}
              <button class="ai-edit-btn" data-episode-id="${episodeId}">Edit</button>
            </div>
          </div>
        </div>
      `;
    };

    // Add date formatter helper
    function formatDate(dateString) {
      if (!dateString) return 'No date';
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    }

    // Update where episodes are rendered - show all episodes
    if (episodesData && episodesData.length > 0) {
      episodesDiv.innerHTML = episodesData
        .map(episode => episodeTemplate(episode))
        .join("");
    } else {
      episodesDiv.innerHTML = "<p>No episodes found for this podcast.</p>";
    }

    // Add button click handlers
    document.querySelectorAll('.add-btn').forEach(button => {
      button.addEventListener('click', () => {
        const action = button.textContent.trim();
        let targetUrl = '/podcastmanagement'; // Default URL

        if (action === 'Add Guest') {
          targetUrl = '/podcastmanagement#add-guest';
        } else if (action === 'Add Task') {
          targetUrl = '/podcastmanagement#add-task';
        } else if (action === 'Add Member') {
          targetUrl = '/podcastmanagement#add-member';
        }

        window.location.href = targetUrl;
      });
    });

    // Right after rendering episode cards
    document.querySelectorAll('.ai-edit-btn').forEach(button => {
      button.addEventListener('click', () => {
        const episodeId = button.getAttribute('data-episode-id');
        if (!episodeId || episodeId === "unknown") {
          alert("Invalid episode ID. Please try again.");
          return;
        }
        const aiEditsURL = `/transcription/ai_edits?episodeId=${episodeId}`;
        console.log("Navigating to:", aiEditsURL); // Debugging
        window.location.href = aiEditsURL;
      });
    });

    // Fetch guests, filter, and display
    const guests = await fetchGuestsRequest().catch(error => {
      console.error("Failed to fetch guests:", error);
      return [];
    });
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
    const tasksData = await fetchTasks().catch(error => {
      console.error("Failed to fetch tasks:", error);
      return [];
    });
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
    const teams = await getTeamsRequest().catch(error => {
      console.error("Failed to fetch teams:", error);
      return [];
    });
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
