// In dashboard.js
import { fetchAllEpisodes } from "/static/requests/episodeRequest.js";
import { fetchGuestsByEpisode } from "/static/requests/guestRequests.js";

document.addEventListener("DOMContentLoaded", function () {
  async function fetchAndDisplayEpisodesWithGuests() {
    try {
      // Fetch episodes using the function from episodeRequest.js
      const episodes = await fetchAllEpisodes();
      const container = document.querySelector(".cards-container");
      container.innerHTML = "";

      for (const episode of episodes) {
        const card = document.createElement("div");
        card.classList.add("card");

        const titleElem = document.createElement("h3");
        titleElem.textContent = episode.title;
        card.appendChild(titleElem);

        const guestList = document.createElement("ul");
        guestList.classList.add("guest-list");

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

  fetchAndDisplayEpisodesWithGuests();
});
