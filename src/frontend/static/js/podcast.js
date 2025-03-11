document.addEventListener("DOMContentLoaded", async () => {
  const podcastId = localStorage.getItem("selectedPodcastId");
  if (!podcastId) {
    console.error("No podcast selected.");
    return;
  }

  try {
    // Fetch podcast details to get teamId
    const podcastRes = await fetch(`/get_podcasts/${podcastId}`);
    if (!podcastRes.ok) throw new Error("Failed to fetch podcast details.");
    const podcastData = await podcastRes.json();
    const podcast = podcastData.podcast;
    const teamId = podcast.teamId; // The teamId associated with the selected podcast

    // Display podcast details
    document.getElementById("podcast-details").innerHTML = renderObject(podcast);

    // Fetch episodes linked to the podcastId
    const episodesRes = await fetch(`/get_episodes?podcastId=${podcastId}`);
    if (!episodesRes.ok) throw new Error("Failed to fetch episodes.");
    const episodesData = await episodesRes.json();
    const relatedEpisodes = episodesData.episodes.filter(ep => ep.podcast_id === podcastId);
    const episodesDiv = document.getElementById("episodes");
    if (relatedEpisodes.length > 0) {
      episodesDiv.innerHTML = relatedEpisodes.map(ep =>
        `<div class="episode">${renderObject(ep)}</div>`
      ).join("");
    } else {
      episodesDiv.innerHTML = "<p>No episodes found for this podcast.</p>";
    }

    // Fetch guests linked to the podcastId
    const guestsRes = await fetch(`/get_guests?podcastId=${podcastId}`);
    if (!guestsRes.ok) throw new Error("Failed to fetch guests.");
    const guestsData = await guestsRes.json();
    const relatedGuests = guestsData.guests.filter(guest => guest.podcastId === podcastId);
    const guestsDiv = document.getElementById("guests");
    if (relatedGuests.length > 0) {
      guestsDiv.innerHTML = relatedGuests.map(guest =>
        `<div class="guest">${renderObject(guest)}</div>`
      ).join("");
    } else {
      guestsDiv.innerHTML = "<p>No guests found for this podcast.</p>";
    }

    // Fetch and display tasks linked to the podcastId
    const tasks = await fetchTasks(podcastId);
    const tasksDiv = document.getElementById("tasks");
    if (tasks.length > 0) {
      tasksDiv.innerHTML = tasks.map(task =>
        `<div class="task">${renderObject(task)}</div>`
      ).join("");
    } else {
      tasksDiv.innerHTML = "<p>No tasks found for this podcast.</p>";
    }

    // Fetch all teams and filter them based on the teamId from the selected podcast
    const teams = await getTeamsRequest();
    console.log("Fetched teams:", teams); // Debug: Log fetched teams

    // Filter teams by teamId (from the podcast data)
    const filteredTeams = teams.filter(team => team._id === teamId);  
    console.log("Filtered teams:", filteredTeams); // Debug: Log filtered teams

    const teamsDiv = document.getElementById("teams");
    if (filteredTeams.length > 0) {
      teamsDiv.innerHTML = filteredTeams.map(team =>
        `<div class="team">${renderObject(team)}</div>`
      ).join("");
    } else {
      teamsDiv.innerHTML = "<p>No teams found for this podcast.</p>";
    }

  } catch (error) {
    console.error("Error fetching data:", error);
  }
});

async function fetchTasks(podcastId) {
  try {
    const response = await fetch(`/get_podtasks?podcastId=${podcastId}`);
    const data = await response.json();

    if (response.ok) {
      return data.podtasks;
    } else {
      console.error("Failed to fetch tasks:", data.error);
      alert("Failed to fetch tasks: " + data.error);
    }
  } catch (error) {
    console.error("Error fetching tasks:", error);
    alert("Failed to fetch tasks.");
  }
}

async function getTeamsRequest() {
  const res = await fetch("/get_teams", { method: "GET" });
  const teamsData = await res.json();
  return teamsData;
}

// Helper function to render an object
function renderObject(obj) {
  const excludedKeys = ["_id", "id", "podcast_id", "teamId", "accountId", "userId"];
  return Object.entries(obj)
    .filter(([key]) => !excludedKeys.includes(key))
    .map(([key, value]) => `<p><strong>${key}:</strong> ${value}</p>`)
    .join("");
}
