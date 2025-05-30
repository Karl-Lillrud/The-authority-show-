import { edit } from "./teamSvg.js";
import { showTeamDetailModal } from "./modals.js";
import { getTeamsRequest } from "/static/requests/teamRequests.js";

// Update the UI with retrieved teams
export function updateTeamsUI(teams) {
  let container = document.querySelector(".card-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "card-container";
    (document.querySelector("main") || document.body).appendChild(container);
  }
  container.innerHTML = "";
  if (teams.length === 0) {
    container.innerHTML = "<p>No teams available.</p>";
    return;
  }
  teams.forEach((team) => {
    const card = document.createElement("div");
    card.className = "team-card";
    card.setAttribute("data-id", team._id);
    card.innerHTML = `
  <div class="team-card-header">
    <h2 class="text-truncate">${team.name}</h2>
    <p class="text-truncate"><strong>Team Email:</strong> ${team.email}</p>
    <button class="action-btn edit-icon-btn">${edit}</button>
  </div>
  <div class="team-card-body">
    <p><strong>Description:</strong> <span class="description-text">${
      team.description || "No description available"
    }</span></p>
    <p><strong>Podcasts:</strong> <span class="text-truncate">${
      team.podNames || "N/A"
    }</span></p>
    <div class="members-section">
      <strong>Members:</strong>
      <div class="members-container">
        ${
          team.members.length > 0
            ? team.members
                .map(
                  (m) => `
                  <span class="member-chip" data-email="${m.email}">
                    <span class="member-email text-truncate">${m.email}</span>
                    ${
                      m.role === "creator"
                        ? '<span class="creator-badge">Creator</span>'
                        : `<span class="role-badge ${m.role.toLowerCase()}">${
                            m.role
                          }</span>`
                    }
                  </span>
                `
                )
                .join("")
            : "No members available"
        }
      </div>
    </div>
  </div>
`;
    card
      .querySelector(".edit-icon-btn")
      .addEventListener("click", () => showTeamDetailModal(team));

    // Add event listeners to member chips
    card.querySelectorAll(".member-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        import("./memberUI.js").then(({ showTeamCardEditMemberModal }) => {
          const memberEmail = chip.getAttribute("data-email");
          const member = team.members.find((m) => m.email === memberEmail);
          if (member) {
            showTeamCardEditMemberModal(team._id, member);
          }
        });
      });
    });

    container.appendChild(card);
  });
}

export function switchToTeamsView() {
  console.log("Switching to Teams view");
  const mainContent = document.querySelector(".main-content");
  mainContent.innerHTML = `
    <div class="main-header">
      <h1>Teams</h1>
    </div>
    <div class="card-container">
      <!-- Team cards will be dynamically inserted here -->
    </div>
  `;
  getTeamsRequest()
    .then((teams) => updateTeamsUI(teams))
    .catch((error) => console.error("Error rendering teams view:", error));
}
