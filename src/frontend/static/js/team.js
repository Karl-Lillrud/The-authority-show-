document.addEventListener("DOMContentLoaded", function () {
  // Helper to fetch podcasts
  async function fetchPodcasts() {
    try {
      const res = await fetch("/get_podcasts", { method: "GET" });
      const data = await res.json();
      return data.podcast || [];
    } catch (err) {
      console.error("Error fetching podcasts:", err);
      return [];
    }
  }

  // Update the UI with retrieved teams
  function updateTeamsUI(teams) {
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
      card.className = "card";
      card.setAttribute("data-id", team._id);
      card.innerHTML = `
        <p><strong>Podcasts:</strong> ${team.podNames || "N/A"}</p>
        <h4>${team.name}</h4>
        <p><strong>Email:</strong> ${team.email}</p>
        <p><strong>Description:</strong> ${team.description || ""}</p>
        <p><strong>Members:</strong> ${team.members
          .map((m) => m.userId)
          .join(", ")}</p>
      `;
      card.addEventListener("click", () => showTeamDetailModal(team));
      container.appendChild(card);
    });
  }

  // Helper to render assigned podcasts based on original assignments and pending changes.
  function renderAssignedPodcasts(
    teamId,
    originalAssignedPodcasts,
    pendingPodcastChanges
  ) {
    const container = document.getElementById("assignedPodcasts");
    container.innerHTML = "";
    const finalAssignments = {};
    originalAssignedPodcasts.forEach((p) => {
      finalAssignments[p._id] = p;
    });
    for (const [podcastId, newTeam] of Object.entries(pendingPodcastChanges)) {
      if (newTeam === teamId) {
        if (!finalAssignments[podcastId]) {
          finalAssignments[podcastId] = {
            _id: podcastId,
            podName: "Pending: " + podcastId
          };
        }
      } else if (newTeam === "REMOVE") {
        delete finalAssignments[podcastId];
      }
    }
    Object.values(finalAssignments).forEach((podcast) => {
      const chip = document.createElement("div");
      chip.className = "podcast-chip";
      chip.innerHTML = `${podcast.podName} <span class="remove-chip" data-id="${podcast._id}">&times;</span>`;
      container.appendChild(chip);
    });
  }

  // Helper to populate the podcast dropdown for assignment based on pending changes.
  async function populatePodcastDropdownForTeam(teamId, pendingPodcastChanges) {
    const dropdown = document.getElementById("podcastAssignmentDropdown");
    dropdown.innerHTML = '<option value="">Select Podcast to Add</option>';
    const podcasts = await fetchPodcasts();
    podcasts.forEach((podcast) => {
      let isAssigned = false;
      if (podcast.teamId === teamId) {
        isAssigned = true;
      }
      if (pendingPodcastChanges[podcast._id] === teamId) {
        isAssigned = true;
      }
      if (pendingPodcastChanges[podcast._id] === "REMOVE") {
        isAssigned = false;
      }
      if (!isAssigned) {
        const option = document.createElement("option");
        option.value = podcast._id;
        option.textContent = podcast.podName;
        dropdown.appendChild(option);
      }
    });
  }

  // Helper to close modals
  function closeModal(modal) {
    modal.classList.remove("show");
    modal.setAttribute("aria-hidden", "true");
  }

  // The team detail modal logic
  function showTeamDetailModal(team) {
    // Local state for pending podcast assignment changes
    let pendingPodcastChanges = {};
    let originalAssignedPodcasts = [];

    async function initAssignments() {
      const podcasts = await fetchPodcasts();
      originalAssignedPodcasts = podcasts.filter((p) => p.teamId === team._id);
      renderAssignedPodcasts(
        team._id,
        originalAssignedPodcasts,
        pendingPodcastChanges
      );
      populatePodcastDropdownForTeam(team._id, pendingPodcastChanges);
    }
    initAssignments();

    // Pre-populate team detail modal fields.
    document.getElementById("detailName").value = team.name;
    document.getElementById("detailEmail").value = team.email;
    document.getElementById("detailDescription").value = team.description;
    document.getElementById("detailMembers").textContent = team.members
      .map((m) => m.userId)
      .join(", ");

    const modal = document.getElementById("teamDetailModal");
    modal.classList.add("show");
    modal.setAttribute("aria-hidden", "false");

    // Handle podcast addition via dropdown.
    const dropdown = document.getElementById("podcastAssignmentDropdown");
    dropdown.onchange = () => {
      const podcastId = dropdown.value;
      if (podcastId) {
        pendingPodcastChanges[podcastId] = team._id;
        renderAssignedPodcasts(
          team._id,
          originalAssignedPodcasts,
          pendingPodcastChanges
        );
        populatePodcastDropdownForTeam(team._id, pendingPodcastChanges);
        dropdown.value = "";
        alert("Podcast addition pending. Press Save to finalize.");
      }
    };

    // Handle removal of a podcast chip.
    const assignedContainer = document.getElementById("assignedPodcasts");
    assignedContainer.onclick = (event) => {
      if (event.target.classList.contains("remove-chip")) {
        const podcastId = event.target.getAttribute("data-id");
        pendingPodcastChanges[podcastId] = "REMOVE";
        renderAssignedPodcasts(
          team._id,
          originalAssignedPodcasts,
          pendingPodcastChanges
        );
        populatePodcastDropdownForTeam(team._id, pendingPodcastChanges);
        alert("Podcast removal pending. Press Save to finalize.");
      }
    };

    // Delete button immediately deletes the team.
    const deleteBtn = document.getElementById("deleteTeamBtn");
    deleteBtn.onclick = async () => {
      try {
        const result = await deleteTeamRequest(team._id);
        alert(result.message || "Team deleted successfully!");
        const card = document.querySelector(`.card[data-id="${team._id}"]`);
        if (card) card.remove();
        closeModal(modal);
        const teams = await getTeamsRequest();
        updateTeamsUI(teams);
      } catch (error) {
        console.error("Error deleting team:", error);
      }
    };

    // Save button finalizes pending podcast assignment changes and updates team details.
    const saveBtn = document.getElementById("saveTeamBtn");
    saveBtn.onclick = async () => {
      try {
        for (const [podcastId, newTeam] of Object.entries(
          pendingPodcastChanges
        )) {
          if (newTeam === team._id) {
            const res = await fetch(`/get_podcasts/${podcastId}`, {
              method: "GET"
            });
            const data = await res.json();
            const existingTeamId = data.podcast ? data.podcast.teamId : null;
            if (existingTeamId && existingTeamId !== team._id) {
              alert(
                `Podcast "${data.podcast.podName}" is already assigned to another team.`
              );
              continue;
            }
            await updatePodcastTeamRequest(podcastId, { teamId: team._id });
          } else if (newTeam === "REMOVE") {
            await updatePodcastTeamRequest(podcastId, { teamId: "" });
          }
        }
      } catch (err) {
        console.error("Error updating podcast assignments:", err);
        alert("Error updating podcast assignments.");
        return;
      }

      const payload = {
        name: document.getElementById("detailName").value,
        email: document.getElementById("detailEmail").value,
        description: document.getElementById("detailDescription").value
      };

      try {
        const result = await editTeamRequest(team._id, payload);
        alert(result.message || "Team updated successfully!");
        closeModal(modal);
        const teams = await getTeamsRequest();
        updateTeamsUI(teams);
      } catch (error) {
        console.error("Error editing team:", error);
      }
    };

    // Modal close handler.
    document.getElementById("teamDetailCloseBtn").onclick = () =>
      closeModal(modal);
    window.addEventListener("click", (event) => {
      if (event.target === modal) {
        closeModal(modal);
      }
    });
  }

  // Existing functions for adding a team remain unchanged.
  getTeamsRequest().then((data) => {
    updateTeamsUI(data);
  });

  async function populatePodcastDropdown() {
    const podcastDropdown = document.getElementById("podcastDropdown");
    if (podcastDropdown) {
      try {
        const podcasts = await fetchPodcasts();
        podcasts.forEach((podcast) => {
          const option = document.createElement("option");
          option.value = podcast._id;
          option.textContent = podcast.podName;
          podcastDropdown.appendChild(option);
        });
      } catch (err) {
        console.error("Error fetching podcasts:", err);
      }
    }
  }
  populatePodcastDropdown();

  async function checkPodcastHasTeam(podcastId) {
    const res = await fetch(`/get_podcasts/${podcastId}`, { method: "GET" });
    const data = await res.json();
    return data.podcast && data.podcast.teamId;
  }

  const addTeamModal = document.getElementById("addTeamModal");
  const addTeamForm = addTeamModal
    ? addTeamModal.querySelector("form")
    : document.querySelector("form");

  if (addTeamForm) {
    addTeamForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      const formData = new FormData(addTeamForm);
      const payload = {
        name: formData.get("name"),
        email: formData.get("email"),
        description: formData.get("description"),
        podcastId: formData.get("podcastId") // Include podcast ID
      };
      const podcastId = formData.get("podcastId");

      const hasTeam = await checkPodcastHasTeam(podcastId);
      if (hasTeam) {
        alert(
          "This podcast already has a team. You cannot create a new team for it."
        );
        return;
      }

      try {
        const response = await addTeamRequest(payload);
        const teamId = response.team_id;
        alert("Team successfully created!");
        if (podcastId && teamId) {
          const updatePayload = { teamId: teamId };
          const updateResponse = await updatePodcastTeamRequest(
            podcastId,
            updatePayload
          );
          console.log("Podcast updated:", updateResponse);
        }
        closeModal(addTeamModal);
        const teams = await getTeamsRequest();
        updateTeamsUI(teams);
      } catch (error) {
        console.error("Error adding team or updating podcast:", error);
      }
    });
  }

  if (addTeamModal) {
    const openModalBtn = document.getElementById("openModalBtn");
    const closeButtons = document.querySelectorAll(
      "#modalCloseBtn, #modalCloseBtn2"
    );

    if (openModalBtn) {
      openModalBtn.addEventListener("click", () => {
        addTeamModal.classList.add("show");
        addTeamModal.setAttribute("aria-hidden", "false");
      });
    }

    closeButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        closeModal(addTeamModal);
      });
    });

    window.addEventListener("click", (event) => {
      if (event.target === addTeamModal) {
        closeModal(addTeamModal);
      }
    });

    window.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && addTeamModal.classList.contains("show")) {
        closeModal(addTeamModal);
      }
    });
  }
});
