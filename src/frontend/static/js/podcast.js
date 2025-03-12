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

    // Fetch and filter guests by podcastId
    const guests = await fetchGuestsRequest();
    console.log("Fetched guests:", guests);

    // Filter guests based on the selected podcastId
    const filteredGuests = guests.filter(guest => guest.podcastId === podcastId);
    console.log("Filtered guests:", filteredGuests);

    const guestsDiv = document.getElementById("guests-container");
    if (filteredGuests.length > 0) {
      guestsDiv.innerHTML = filteredGuests
        .map(
          guest =>
            `<div class="card">
              <h4>${guest.name}</h4>
              <p><strong>Bio:</strong> ${guest.bio || 'No bio available'}</p>
              <p><strong>Social Links:</strong> ${guest.socialLinks || 'None'}</p>
            </div>`
        )
        .join("");
    } else {
      guestsDiv.innerHTML = "<p>No guests found for this podcast.</p>";
    }

    // Fetch and display episodes
    const episodesRes = await fetch(`/get_episodes?podcastId=${podcastId}`);
    if (!episodesRes.ok) throw new Error("Failed to fetch episodes.");
    const episodesData = await episodesRes.json();
    const episodesDiv = document.getElementById("episodes-container");

    // Filter episodes based on podcastId
    const filteredEpisodes = episodesData.episodes.filter(episode => episode.podcast_id === podcastId);
    if (filteredEpisodes.length > 0) {
      episodesDiv.innerHTML = filteredEpisodes
        .map(
          episode =>
            `<div class="card">
              <h4>${episode.title}</h4>
              <p><strong>Duration:</strong> ${episode.duration || 'N/A'}</p>
              <p><strong>Release Date:</strong> ${episode.publishDate || 'N/A'}</p>
            </div>`
        )
        .join("");
    } else {
      episodesDiv.innerHTML = "<p>No episodes found for this podcast.</p>";
    }

    // Fetch and display tasks
    const tasksRes = await fetch(`/get_podtasks?podcastId=${podcastId}`);
    if (!tasksRes.ok) throw new Error("Failed to fetch tasks.");
    const tasksData = await tasksRes.json();
    const tasksDiv = document.getElementById("tasks-container");

    // Filter tasks based on podcastId
    const filteredTasks = tasksData.podtasks.filter(task => task.podcastId === podcastId);
    if (filteredTasks.length > 0) {
      tasksDiv.innerHTML = filteredTasks
        .map(
          task =>
            `<div class="card">
              <h4>${task.taskName}</h4>
              <p><strong>Due Date:</strong> ${task.dueDate || 'N/A'}</p>
              <p><strong>Status:</strong> ${task.status || 'N/A'}</p>
            </div>`
        )
        .join("");
    } else {
      tasksDiv.innerHTML = "<p>No tasks found for this podcast.</p>";
    }

    // Fetch and display teams
    const teams = await getTeamsRequest();
    console.log("Fetched teams:", teams);

    // Filter teams by teamId (from the podcast data)
    const filteredTeams = teams.filter(team => team._id === podcast.teamId);
    console.log("Filtered teams:", filteredTeams);

    const teamsDiv = document.getElementById("teams-container");
    if (filteredTeams.length > 0) {
      const team = filteredTeams[0]; // Assuming there's only one team with the given teamId
      teamsDiv.innerHTML = `
        <div class="card">
          <h4>${team.name}</h4>
          <p><strong>Members:</strong> ${team.members.join(", ")}</p>
          <p><strong>Description:</strong> ${team.description || "N/A"}</p>
        </div>
      `;
    } else {
      teamsDiv.innerHTML = "<p>No teams found for this podcast.</p>";
    }
  } catch (error) {
    console.error("Error fetching data:", error);
  }
});

async function fetchGuestsRequest() {
  const res = await fetch("/get_guests", { method: "GET" });
  if (!res.ok) {
    throw new Error("Failed to fetch guests");
  }
  const data = await res.json();
  return data.guests || []; // Assuming guests are returned in an array under "guests"
}

async function getTeamsRequest() {
  const res = await fetch("/get_teams", { method: "GET" });
  const teamsData = await res.json();
  return teamsData; // Assuming teams are returned as an array
}
