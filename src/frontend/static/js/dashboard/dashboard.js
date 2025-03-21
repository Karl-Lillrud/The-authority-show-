import { fetchGuestsByEpisode } from "/static/requests/guestRequests.js";

document.addEventListener("DOMContentLoaded", function () {

  // Fetch Episodes and Display Associated Guest Names
  async function fetchAndDisplayEpisodesWithGuests() {
    try {
      // Fetch all episodes for the current user
      const response = await fetch("/get_episodes");
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Failed to fetch episodes");
      }
      const episodes = data.episodes || [];
      const container = document.querySelector(".cards-container");
      container.innerHTML = "";

      for (const episode of episodes) {
        // Create a card for each episode
        const card = document.createElement("div");
        card.classList.add("card");

        // Display episode title
        const titleElem = document.createElement("h3");
        titleElem.textContent = episode.title;
        card.appendChild(titleElem);

        // Create a list to display guest names associated with this episode
        const guestList = document.createElement("ul");
        guestList.classList.add("guest-list");

        // Fetch guests for the current episode using its id (assumed to be _id)
        try {
          const guests = await fetchGuestsByEpisode(episode._id);
          if (guests.length > 0) {
            guests.forEach((guest) => {
              const li = document.createElement("li");
              li.textContent = guest.name;
              guestList.appendChild(li);
            });
          } else {
            const noGuestMsg = document.createElement("p");
            noGuestMsg.textContent = "No guest available";
            guestList.appendChild(noGuestMsg);
          }
        } catch (error) {
          console.error("Error fetching guests for episode:", error);
          const errorMsg = document.createElement("p");
          errorMsg.textContent = "Error loading guest info";
          guestList.appendChild(errorMsg);
        }

        card.appendChild(guestList);
        container.appendChild(card);
      }
    } catch (error) {
      console.error("Error fetching episodes with guests:", error);
    }
  }

  // Call the function to populate episode cards with guest names
  fetchAndDisplayEpisodesWithGuests();
});
