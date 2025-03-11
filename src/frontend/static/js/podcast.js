document.addEventListener("DOMContentLoaded", async () => {
  const podcastId = localStorage.getItem("selectedPodcastId");
  if (!podcastId) {
    console.error("No podcast selected.");
    return;
  }

  try {
    // Fetch podcast details
    const podcastRes = await fetch(`/get_podcasts/${podcastId}`);
    if (!podcastRes.ok) throw new Error("Failed to fetch podcast details.");
    const podcastData = await podcastRes.json();
    const podcast = podcastData.podcast;

    console.log("Podcast Data:", podcast);  // Log podcast data

    // Display podcast details
    const podcastContainer = document.getElementById("podcast-container");
    podcastContainer.innerHTML = `
      <div class="card">
        <h2>${podcast.podName}</h2>
        <p><strong>Category:</strong> ${podcast.category || 'No category available'}</p>
        <p><strong>Owner:</strong> ${podcast.ownerName || 'yous aint gots no names'}</p>
        <p><strong>Host:</strong> ${podcast.hostName || 'No host available'}</p>
        <p><strong>Description:</strong> ${podcast.description || 'No description available'}</p>
      </div>
    `;

    // Fetch and display guests
    const guestsRes = await fetch(`/get_guests?podcastId=${podcastId}`);
    if (!guestsRes.ok) throw new Error("Failed to fetch guests.");
    const guestsData = await guestsRes.json();
    const guestsDiv = document.getElementById("guests-container");
    if (guestsData.guests && guestsData.guests.length > 0) {
      guestsDiv.innerHTML = guestsData.guests.map(guest =>
        `<div class="card">
          <h4>${guest.name}</h4>
          <p><strong>Bio:</strong> ${guest.bio || 'No bio available'}</p>
          <p><strong>Social Links:</strong> ${guest.socialLinks || 'None'}</p>
        </div>`).join('');
    } else {
      guestsDiv.innerHTML = "<p>No guests found for this podcast.</p>";
    }

    // Fetch and display episodes
    const episodesRes = await fetch(`/get_episodes?podcastId=${podcastId}`);
    if (!episodesRes.ok) throw new Error("Failed to fetch episodes.");
    const episodesData = await episodesRes.json();
    const episodesDiv = document.getElementById("episodes-container");
    if (episodesData.episodes && episodesData.episodes.length > 0) {
      episodesDiv.innerHTML = episodesData.episodes.map(episode =>
        `<div class="card">
          <h4>${episode.title}</h4>
          <p><strong>Duration:</strong> ${episode.duration || 'N/A'}</p>
          <p><strong>Release Date:</strong> ${episode.releaseDate || 'N/A'}</p>
        </div>`).join('');
    } else {
      episodesDiv.innerHTML = "<p>No episodes found for this podcast.</p>";
    }

    // Fetch and display tasks
    const tasksRes = await fetch(`/get_podtasks?podcastId=${podcastId}`);
    if (!tasksRes.ok) throw new Error("Failed to fetch tasks.");
    const tasksData = await tasksRes.json();
    const tasksDiv = document.getElementById("tasks-container");
    if (tasksData.podtasks && tasksData.podtasks.length > 0) {
      tasksDiv.innerHTML = tasksData.podtasks.map(task =>
        `<div class="card">
          <h4>${task.taskName}</h4>
          <p><strong>Due Date:</strong> ${task.dueDate || 'N/A'}</p>
          <p><strong>Status:</strong> ${task.status || 'N/A'}</p>
        </div>`).join('');
    } else {
      tasksDiv.innerHTML = "<p>No tasks found for this podcast.</p>";
    }

    // Fetch all teams and filter based on teamId of the podcast
    const teams = await getTeamsRequest();
    console.log("Fetched teams:", teams);  // Debug: Log fetched teams

    // Filter teams by teamId (from the podcast data)
    const filteredTeams = teams.filter(team => team._id === podcast.teamId);  
    console.log("Filtered teams:", filteredTeams); // Debug: Log filtered teams

    const teamsDiv = document.getElementById("teams-container");
    if (filteredTeams.length > 0) {
      const team = filteredTeams[0]; // Assuming there's only one team with the given teamId
      teamsDiv.innerHTML = `
        <div class="card">
          <h4>${team.name}</h4>
          <p><strong>Members:</strong> ${team.members.join(', ')}</p>
          <p><strong>Description:</strong> ${team.description || 'N/A'}</p>
        </div>
      `;
    } else {
      teamsDiv.innerHTML = "<p>No teams found for this podcast.</p>";
    }

  } catch (error) {
    console.error("Error fetching data:", error);
  }
});

async function getTeamsRequest() {
  const res = await fetch("/get_teams", { method: "GET" });
  const teamsData = await res.json();
  return teamsData;
}
