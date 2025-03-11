// List of keys to exclude from display
const excludedKeys = ["_id", "id", "podcast_id", "teamId", "accountId", "userId"];

function renderObject(obj) {
    return Object.entries(obj)
      .filter(([key]) => !excludedKeys.includes(key))
      .map(([key, value]) => `<p><strong>${key}:</strong> ${value}</p>`)
      .join("");
  }

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
      document.getElementById("podcast-details").innerHTML = renderObject(podcast);

      // Fetch episodes and filter by podcast_id matching the selected podcast
      const episodesRes = await fetch("/get_episodes");
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

      // Fetch guests using a query parameter for podcastId
      // (Assuming the backend supports filtering via query parameters)
      const guestsRes = await fetch("/get_guests");
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
  } catch (error) {
    console.error("Error fetching data:", error);
  }
});