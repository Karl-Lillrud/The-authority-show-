document.addEventListener("DOMContentLoaded", function () {
  function setupNavigation() {
    const goToProductionTeam = document.getElementById("goToProductionTeam");
    const goToPodProfile = document.getElementById("goToPodProfile");
    const backToPodName = document.getElementById("backToPodName");
    const backToProductionTeam = document.getElementById(
      "backToProductionTeam"
    );
    const podProfileForm = document.getElementById("podProfileForm");
    const darkModeToggle = document.getElementById("dark-mode-toggle");
    const addTeamMemberButton = document.getElementById("addTeamMember");
    const teamMembersContainer = document.getElementById(
      "teamMembersContainer"
    );
    const skipToDashboard = document.getElementById("skipToDashboard");
    const goToEmailSection = document.getElementById("goToEmailSection");

    console.log("Setting up navigation");

    if (goToPodProfile) {
      goToPodProfile.addEventListener("click", async () => {
        const podName = document.getElementById("podName").value.trim();
        const podRss = document.getElementById("podRss").value.trim();

        if (!podName || !podRss) {
          alert("Please enter both Podcast Name and RSS URL.");
          return;
        }

        try {
          await postPodcastData(podName, podRss);
          document.getElementById("pod-name-section").classList.add("hidden");
          document
            .getElementById("pod-profile-section")
            .classList.remove("hidden");
        } catch (error) {
          alert("Something went wrong. Please try again.");
        }
      });
    }

    if (goToProductionTeam) {
      goToProductionTeam.addEventListener("click", () => {
        document.getElementById("pod-profile-section").classList.add("hidden");
        document
          .getElementById("production-team-section")
          .classList.remove("hidden");
      });
    }

    if (backToPodName) {
      backToPodName.addEventListener("click", () => {
        document.getElementById("pod-profile-section").classList.add("hidden");
        document.getElementById("pod-name-section").classList.remove("hidden");
      });
    }

    if (backToProductionTeam) {
      backToProductionTeam.addEventListener("click", () => {
        document
          .getElementById("production-team-section")
          .classList.add("hidden");
        document
          .getElementById("pod-profile-section")
          .classList.remove("hidden");
      });
    }

    if (goToEmailSection) {
      goToEmailSection.addEventListener("click", async (event) => {
        event.preventDefault();
        await sendInvitations();
        document
          .getElementById("production-team-section")
          .classList.add("hidden");
        document.getElementById("email-section").classList.remove("hidden");
      });
    }

    if (podProfileForm) {
      podProfileForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(podProfileForm);
        const data = Object.fromEntries(formData.entries());

        try {
          const success = await savePodProfile(data);
          if (success) {
            document
              .getElementById("production-team-section")
              .classList.add("hidden");
            document.getElementById("email-section").classList.remove("hidden");
          } else {
            alert("Something went wrong. Please try again.");
          }
        } catch (error) {
          console.error("Error saving pod profile:", error);
          alert("Something went wrong. Please try again.");
        }
      });
    }

    // Fix Dark Mode Toggle
    if (darkModeToggle) {
      darkModeToggle.addEventListener("click", () => {
        document.body.classList.toggle("dark-mode");
      });
    }

    // Fix Add More Members Function
    if (addTeamMemberButton && teamMembersContainer) {
      addTeamMemberButton.addEventListener("click", () => {
        const newMember = document.createElement("div");
        newMember.classList.add("team-member");
        newMember.innerHTML = `
          <div class="form-group">
            <label>Name</label>
            <input type="text" class="team-name" required>
          </div>
          <div class="form-group">
            <label>Email</label>
            <input type="email" class="team-email" required>
          </div>
          <div class="form-group">
            <label>Role</label>
            <select class="team-role" required>
              <option value="" disabled selected>Select Role</option>
              <option value="user">User</option>
              <option value="host">Host</option>
            </select>
          </div>
        `;
        teamMembersContainer.appendChild(newMember);
      });
    }

    if (skipToDashboard) {
      skipToDashboard.addEventListener("click", () => {
        window.location.href = "dashboard"; // Redirect to dashboard
      });
    }
  }

  setupNavigation();
});

function setupAddTeamMember() {
  const addTeamMemberButton = document.getElementById("addTeamMember");
  if (addTeamMemberButton) {
    addTeamMemberButton.addEventListener("click", () => {
      const container = document.getElementById("teamMembersContainer");
      if (container) {
        const newMember = document.createElement("div");
        newMember.classList.add("team-member");
        newMember.innerHTML = `
                    <div class="form-group">
                        <label>Name</label>
                        <input type="text" class="team-name" required>
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" class="team-email" required>
                    </div>
                    <div class="form-group">
                        <label>Role</label>
                        <select class="team-role" required>
                            <option value="" disabled selected>Select Role</option>
                            <option value="user">User</option>
                            <option value="host">Host</option>
                        </select>
                    </div>
                `;
        container.appendChild(newMember);
      }
    });
  }
}

function setupInvitationEmails() {
  const goToPodProfile = document.getElementById("goToPodProfile");
  if (goToPodProfile) {
    goToPodProfile.addEventListener("click", sendInvitations);
  }
}

async function sendInvitations() {
  const teamMembers = document.querySelectorAll(".team-member");
  const podNameElement = document.getElementById("podName");
  const podName = podNameElement ? podNameElement.value : "your podcast";
  const joinLinkBase = "https://app.podmanager.ai/register"; // Updated base URL

  for (const member of teamMembers) {
    const email = member.querySelector(".team-email").value;
    const name = member.querySelector(".team-name").value;
    const role = member.querySelector(".team-role").value;
    if (email) {
      const joinLink = `${joinLinkBase}?email=${encodeURIComponent(
        email
      )}&name=${encodeURIComponent(name)}&role=${encodeURIComponent(role)}`;
      const subject = `Join the ${podName} team`;
      try {
        const response = await fetch("/beta-email/podmanager-beta-invite.html");
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        const body = await response.text();
        await sendInvitation(email, subject, body);
      } catch (error) {
        console.error("Error fetching invitation template:", error);
      }
    }
  }
}

function setupDarkMode() {
  const darkModeToggle = document.getElementById("dark-mode-toggle");
  const body = document.body;
  const isDarkMode = localStorage.getItem("darkMode") === "enabled";

  if (isDarkMode) {
    body.classList.add("dark-mode");
    darkModeToggle.textContent = "☀️";
  }

  if (darkModeToggle) {
    darkModeToggle.addEventListener("click", () => {
      body.classList.toggle("dark-mode");
      const darkModeEnabled = body.classList.contains("dark-mode");
      darkModeToggle.textContent = darkModeEnabled ? "☀️" : "🌙";
      localStorage.setItem(
        "darkMode",
        darkModeEnabled ? "enabled" : "disabled"
      );
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const savedLang = localStorage.getItem("selectedLanguage") || "en";
  if (window.i18n) {
    window.i18n.changeLanguage(savedLang);
  }

  const languageButton = document.getElementById("language-button");
  if (languageButton) {
    languageButton.addEventListener("click", () => {
      document.getElementById("language-list").classList.toggle("hidden");
    });
  }

  const languageList = document.getElementById("language-list");
  if (languageList) {
    languageList.addEventListener("click", (event) => {
      if (event.target.tagName === "LI") {
        const selectedLang = event.target.getAttribute("data-lang");
        if (window.i18n) {
          window.i18n.changeLanguage(selectedLang);
        }
        languageList.classList.add("hidden");
      }
    });
  }
});

async function fetchRSSData(rssUrl) {
  if (!rssUrl) return;
  try {
    const response = await fetch(
      `https://api.rss2json.com/v1/api.json?rss_url=${encodeURIComponent(
        rssUrl
      )}`
    );
    const data = await response.json(); // Directly parse JSON response

    if (data.status === "ok") {
      document.getElementById("podName").value = data.feed.title || "";
    } else {
      console.error("Error fetching RSS feed:", data);
    }
  } catch (error) {
    console.error("Error fetching RSS feed:", error);
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const goToProductionTeam = document.getElementById("goToProductionTeam");

  if (goToProductionTeam) {
    goToProductionTeam.addEventListener("click", async function () {
      const podName = document.getElementById("podName").value.trim();
      const podRss = document.getElementById("podRss").value.trim();

      if (!podName || !podRss) {
        alert("Please enter both Podcast Name and RSS URL.");
        return;
      }
    });
  }
});

document.addEventListener("DOMContentLoaded", function () {
  // Updated navigation: Only Pod Name and Email Sections are now active.
  const goToEmailSection = document.getElementById("goToEmailSection");
  const skipToDashboard = document.getElementById("skipToDashboard");
  const podNameForm = document.getElementById("podNameForm");

  if (goToEmailSection) {
    goToEmailSection.addEventListener("click", async () => {
      const podName = document.getElementById("podName").value.trim();
      const podRss = document.getElementById("podRss").value.trim();
      if (!podName || !podRss) {
        alert("Please enter both Podcast Name and RSS URL.");
        return;
      }
      try {
        await postPodcastData(podName, podRss);
        document.getElementById("pod-name-section").classList.add("hidden");
        document.getElementById("email-section").classList.remove("hidden");
      } catch (error) {
        alert("Something went wrong. Please try again.");
      }
    });
  }
});
