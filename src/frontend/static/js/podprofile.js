document.addEventListener("DOMContentLoaded", function () {
  function showSection(sectionId) {
    const sections = document.querySelectorAll("main > .container");
    sections.forEach(section => section.classList.add("hidden"));
    document.getElementById(sectionId).classList.remove("hidden");
  }

  // Event listener for goToPodProfile
  const goToPodProfile = document.getElementById("goToPodProfile");
  if (goToPodProfile) {
    goToPodProfile.addEventListener("click", async function () {
      const podName = document.getElementById("podName").value.trim();
      const podRss = document.getElementById("podRss").value.trim();

      if (!podName) {
        alert("Please enter Podcast Name.");
        return;
      }

      try {
        await postPodcastData(podName, podRss);
        showSection("pod-profile-section");
      } catch (error) {
        alert("Something went wrong. Please try again.");
      }
    });
  }

  // Event listener for goToProductionTeam
  const goToProductionTeam = document.getElementById("goToProductionTeam");
  if (goToProductionTeam) {
    goToProductionTeam.addEventListener("click", () => {
      showSection("production-team-section");
    });
  }

  // Event listener for goToEmail
  const goToEmail = document.getElementById("goToEmail");
  if (goToEmail) {
    goToEmail.addEventListener("click", () => {
      showSection("email-section");
    });
  }

  // Event listener for backToPodName
  const backToPodName = document.getElementById("backToPodName");
  if (backToPodName) {
    backToPodName.addEventListener("click", () => {
      showSection("pod-name-section");
    });
  }

  // Event listener for backToPodProfile
  const backToPodProfile = document.getElementById("backToPodProfile");
  if (backToPodProfile) {
    backToPodProfile.addEventListener("click", () => {
      showSection("pod-profile-section");
    });
  }

  // Event listener for backToProductionTeam
  const backToProductionTeam = document.getElementById("backToProductionTeam");
  if (backToProductionTeam) {
    backToProductionTeam.addEventListener("click", () => {
      showSection("production-team-section");
    });
  }

  const podProfileForm = document.getElementById("podProfileForm");
  if (podProfileForm) {
    podProfileForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(podProfileForm);
      const data = Object.fromEntries(formData.entries());

      try {
        const success = await savePodProfile(data);
        if (success) {
          window.location.href = "dashboard"; // Redirect to dashboard
        } else {
          alert("Something went wrong. Please try again.");
        }
      } catch (error) {
        console.error("Error saving pod profile:", error);
        alert("Something went wrong. Please try again.");
      }
    });
  }

  const emailForm = document.getElementById("emailForm");
  if (emailForm) {
    emailForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const email = document.getElementById("email").value;
      const subject = document.getElementById("emailSubject").value;
      const body = document.getElementById("emailBody").value;

      try {
        await sendInvitation(email, subject, body);
        alert("Email sent successfully!");
        window.location.href = "dashboard"; // Redirect to dashboard
      } catch (error) {
        console.error("Error sending email:", error);
        alert("Something went wrong. Please try again.");
      }
    });
  }

  // Dark Mode Toggle
  const darkModeToggle = document.getElementById("dark-mode-toggle");
  if (darkModeToggle) {
    darkModeToggle.addEventListener("click", () => {
      document.body.classList.toggle("dark-mode");
    });
  }

  // Add Team Member
  const addTeamMemberButton = document.getElementById("addTeamMember");
  const teamMembersContainer = document.getElementById("teamMembersContainer");
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

  // Google Calendar Integration: Remove the error log if button not found.
  const googleCalendarButton = document.getElementById("googleCalendar");
  if (googleCalendarButton) {
    googleCalendarButton.addEventListener("click", () => {
      const hostEmailElement = document.querySelector(".team-email");
      if (hostEmailElement) {
        const hostEmail = hostEmailElement.value;
        if (hostEmail.endsWith("@gmail.com")) {
          const oauth2Url = `https://accounts.google.com/o/oauth2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&response_type=code&scope=https://www.googleapis.com/auth/calendar`;
          window.open(oauth2Url, "_blank");
        } else {
          alert("Google Calendar integration is only available for Gmail accounts.");
        }
      } else {
        alert("Host email element not found.");
      }
    });
  }

  const skipToDashboard = document.getElementById("skipToDashboard");
  if (skipToDashboard) {
    skipToDashboard.addEventListener("click", () => {
      window.location.href = "dashboard"; // Redirect to dashboard
    });
  }

  setupDarkMode();
});

function setupDarkMode() {
  const darkModeToggle = document.getElementById("dark-mode-toggle");
  const body = document.body;
  const isDarkMode = localStorage.getItem("darkMode") === "enabled";

  if (isDarkMode) {
    body.classList.add("dark-mode");
    if (darkModeToggle) darkModeToggle.textContent = "☀️";
  }

  if (darkModeToggle) {
    darkModeToggle.addEventListener("click", () => {
      body.classList.toggle("dark-mode");
      const darkModeEnabled = body.classList.contains("dark-mode");
      darkModeToggle.textContent = darkModeEnabled ? "☀️" : "🌙";
      localStorage.setItem("darkMode", darkModeEnabled ? "enabled" : "disabled");
    });
  }
}

function sendInvitations() {
  const teamMembers = document.querySelectorAll(".team-member");
  const podNameElement = document.getElementById("podName");
  const podName = podNameElement ? podNameElement.value : "your podcast";
  const joinLinkBase = "https://app.podmanager.ai/register";

  teamMembers.forEach((member) => {
    const email = member.querySelector(".team-email").value;
    const name = member.querySelector(".team-name").value;
    const role = member.querySelector(".team-role").value;
    if (email) {
      const joinLink = `${joinLinkBase}?email=${encodeURIComponent(
        email
      )}&name=${encodeURIComponent(name)}&role=${encodeURIComponent(role)}`;
      const subject = `Join the ${podName} team`;
      const body = `Hi ${name}!\n\nYou are hereby invited by PodManager.ai to join the team of ${podName}.\n\nClick here to join the team: <a href="${joinLink}">${joinLink}</a>\n\nWelcome to PodManager.ai!`;
      sendInvitation(email, subject, body);
    }
  });
}

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
    goToPodProfile.addEventListener("click", () => {
      sendInvitations();
      showSection("email-section");
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

document.addEventListener("DOMContentLoaded", function () {
  const pointsSystem = {
    podName: 10,
    podRss: 10,
    podLogo: 10,
    hostName: 10,
    googleCalendar: 10,
    calendarUrl: 10,
    guestForm: 100,
    facebook: 10,
    instagram: 10,
    linkedin: 10,
    twitter: 10,
    tiktok: 10,
    pinterest: 10,
    website: 10,
    email: 10,
    inviteUser: 50,
    inviteHost: 50,
    blockUser: 10
  };

  function getStoredPoints() {
    return JSON.parse(localStorage.getItem("userPoints")) || 0;
  }

  function addPoints(field, points) {
    let userPoints = getStoredPoints();
    if (!localStorage.getItem(`points_${field}`)) {
      userPoints += points;
      localStorage.setItem("userPoints", JSON.stringify(userPoints));
      localStorage.setItem(`points_${field}`, "true");
    }
  }

  function trackInputField(fieldId, pointValue) {
    const field = document.getElementById(fieldId);
    if (field) {
      field.addEventListener("input", function () {
        addPoints(fieldId, pointValue);
      });
    }
  }

  function trackButtonClick(buttonId, fieldKey, pointValue) {
    const button = document.getElementById(buttonId);
    if (button) {
      button.addEventListener("click", function () {
        addPoints(fieldKey, pointValue);
      });
    }
  }

  const podRssInput = document.getElementById("podRss");
  if (podRssInput) {
    podRssInput.addEventListener("input", function () {
      const rssUrl = this.value.trim();
      if (rssUrl) {
        fetchRSSData(rssUrl);
      }
    });
  }

  trackInputField("podName", pointsSystem.podName);
  trackInputField("podRss", pointsSystem.podRss);
  trackInputField("podLogo", pointsSystem.podLogo);
  trackInputField("hostName", pointsSystem.hostName);
  trackButtonClick("googleCalendar", "googleCalendar", pointsSystem.googleCalendar);
  trackInputField("calendarUrl", pointsSystem.calendarUrl);
  trackInputField("guestForm", pointsSystem.guestForm);
  trackInputField("facebook", pointsSystem.facebook);
  trackInputField("instagram", pointsSystem.instagram);
  trackInputField("linkedin", pointsSystem.linkedin);
  trackInputField("twitter", pointsSystem.twitter);
  trackInputField("tiktok", pointsSystem.tiktok);
  trackInputField("pinterest", pointsSystem.pinterest);
  trackInputField("website", pointsSystem.website);
  trackInputField("email", pointsSystem.email);

  trackButtonClick("goToPodProfile", "inviteUser", pointsSystem.inviteUser);
  trackButtonClick("goToPodProfile", "inviteHost", pointsSystem.inviteHost);
  trackButtonClick("blockUser", "blockUser", pointsSystem.blockUser);
});

async function fetchRSSData(rssUrl) {
  if (!rssUrl) return;
  try {
    const response = await fetch(
      `https://api.rss2json.com/v1/api.json?rss_url=${encodeURIComponent(rssUrl)}`
    );
    const text = await response.text();

    try {
      const data = JSON.parse(text);
      if (data.status === "ok") {
        document.getElementById("podName").value = data.feed.title || "";
        document.getElementById("website").value = data.feed.link || "";
      }
    } catch (jsonError) {
      console.error("Invalid JSON:", text);
    }
  } catch (error) {
    console.error("Error fetching RSS feed:", error);
  }
}
