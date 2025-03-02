document.addEventListener("DOMContentLoaded", function () {
  function setupNavigation() {
    const goToProductionTeam = document.getElementById("goToProductionTeam");
    const goToPodProfile = document.getElementById("goToPodProfile");
    const backToPodName = document.getElementById("backToPodName");
    const backToProductionTeam = document.getElementById("backToProductionTeam");
    const podProfileForm = document.getElementById("podProfileForm");
    const darkModeToggle = document.getElementById("dark-mode-toggle");
    const addTeamMemberButton = document.getElementById("addTeamMember");
    const teamMembersContainer = document.getElementById("teamMembersContainer");
    const googleCalendarButton = document.getElementById("googleCalendar");
    const skipToDashboard = document.getElementById("skipToDashboard");
    const emailForm = document.getElementById("emailForm");
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
          document.getElementById("pod-profile-section").classList.remove("hidden");
        } catch (error) {
          alert("Something went wrong. Please try again.");
        }
      });
    }

    if (goToProductionTeam) {
      goToProductionTeam.addEventListener("click", () => {
        document.getElementById("pod-profile-section").classList.add("hidden");
        document.getElementById("production-team-section").classList.remove("hidden");
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
        document.getElementById("production-team-section").classList.add("hidden");
        document.getElementById("pod-profile-section").classList.remove("hidden");
      });
    }

    if (goToEmailSection) {
      goToEmailSection.addEventListener("click", () => {
        document.getElementById("production-team-section").classList.add("hidden");
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
            document.getElementById("production-team-section").classList.add("hidden");
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

    if (emailForm) {
      emailForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const emailSubject = document.getElementById("emailSubject").value.trim();
        const emailBody = document.getElementById("emailBody").value.trim();

        if (!emailSubject || !emailBody) {
          alert("Please enter both subject and body.");
          return;
        }

        try {
          await sendEmail(emailSubject, emailBody);
          alert("Email sent successfully!");
        } catch (error) {
          console.error("Error sending email:", error);
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

    // Handle Google Calendar connection
    console.log("Checking for Google Calendar button");
    console.log("googleCalendarButton:", googleCalendarButton);
    if (googleCalendarButton) {
      console.log("Google Calendar button found");
      googleCalendarButton.addEventListener("click", () => {
        console.log("Google Calendar button clicked");
        const hostEmailElement = document.querySelector(".team-email"); // Fetch the email entered by the host
        if (hostEmailElement) {
          const hostEmail = hostEmailElement.value;
          console.log("Host email:", hostEmail);
          if (hostEmail.endsWith("@gmail.com")) {
            console.log("Redirecting to Google Calendar OAuth2 connection");
            const oauth2Url = `https://accounts.google.com/o/oauth2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&response_type=code&scope=https://www.googleapis.com/auth/calendar`;
            window.open(oauth2Url, "_blank"); // Open Google Calendar OAuth2 in a new tab
          } else {
            alert(
              "Google Calendar integration is only available for Gmail accounts."
            );
          }
        } else {
          alert("Host email element not found.");
        }
      });
    } else {
      console.error("Google Calendar button not found");
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

function sendInvitations() {
  const teamMembers = document.querySelectorAll(".team-member");
  const podNameElement = document.getElementById("podName");
  const podName = podNameElement ? podNameElement.value : "your podcast";
  const joinLinkBase = "https://app.podmanager.ai/register"; // Updated base URL

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
  trackButtonClick(
    "googleCalendar",
    "googleCalendar",
    pointsSystem.googleCalendar
  );
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
      `https://api.rss2json.com/v1/api.json?rss_url=${encodeURIComponent(
        rssUrl
      )}`
    );
    const text = await response.text(); // Read response as text first

    try {
      const data = JSON.parse(text); // Attempt to parse JSON
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
