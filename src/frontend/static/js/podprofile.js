// Use require instead of import
const { postPodcastData, savePodProfile, sendInvitation, fetchRSSData } = require('./podprofileRequests.js');

document.addEventListener("DOMContentLoaded", () => {
  // Points System
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
    blockUser: 10,
  };

  // Utility functions for points tracking
  const getStoredPoints = () =>
    JSON.parse(localStorage.getItem("userPoints")) || 0;

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
      field.addEventListener("input", () => addPoints(fieldId, pointValue));
    }
  }

  function trackButtonClick(buttonId, fieldKey, pointValue) {
    const button = document.getElementById(buttonId);
    if (button) {
      button.addEventListener("click", () => addPoints(fieldKey, pointValue));
    }
  }

  // Setup navigation and event handlers
  function setupNavigation() {
    // DOM Elements
    const elements = {
      goToProductionTeam: document.getElementById("goToProductionTeam"),
      goToPodProfile: document.getElementById("goToPodProfile"),
      backToPodName: document.getElementById("backToPodName"),
      backToProductionTeam: document.getElementById("backToProductionTeam"),
      podProfileForm: document.getElementById("podProfileForm"),
      darkModeToggle: document.getElementById("dark-mode-toggle"),
      addTeamMemberButton: document.getElementById("addTeamMember"),
      teamMembersContainer: document.getElementById("teamMembersContainer"),
      googleCalendarButton: document.getElementById("googleCalendar"),
      skipToDashboard: document.getElementById("skipToDashboard"),
      goToPodcastSocial: document.getElementById("goToPodcastSocial"),
      goToPodcastCalendar: document.getElementById("goToPodcastCalendar"),
      goToPodcastTeam: document.getElementById("goToPodcastTeam"),
      backToPodcastInfo: document.getElementById("backToPodcastInfo"),
      backToPodcastSocial: document.getElementById("backToPodcastSocial"),
      backToPodcastCalendar: document.getElementById("backToPodcastCalendar"),
      goToDashboard: document.getElementById("goToDashboard"),
      inviteTeamMembers: document.getElementById("inviteTeamMembers"),
      podRssInput: document.getElementById("podRss"),
    };

    console.log("Setting up navigation");

    // Production team navigation
    elements.goToProductionTeam &&
      elements.goToProductionTeam.addEventListener("click", async () => {
        const podName = document.getElementById("podName").value.trim();
        const podRss = document.getElementById("podRss").value.trim();
        if (!podName || !podRss) {
          alert("Please enter both Podcast Name and RSS URL.");
          return;
        }
        try {
          await postPodcastData(podName, podRss);
          document
            .getElementById("pod-name-section")
            .classList.add("hidden");
          document
            .getElementById("production-team-section")
            .classList.remove("hidden");
        } catch (error) {
          alert("Something went wrong. Please try again.");
        }
      });

    // Podcast profile navigation
    elements.goToPodProfile &&
      elements.goToPodProfile.addEventListener("click", () => {
        sendInvitations();
        document
          .getElementById("production-team-section")
          .classList.add("hidden");
        document
          .getElementById("pod-profile-section")
          .classList.remove("hidden");
      });

    // Back navigation
    elements.backToPodName &&
      elements.backToPodName.addEventListener("click", () => {
        document
          .getElementById("production-team-section")
          .classList.add("hidden");
        document
          .getElementById("pod-name-section")
          .classList.remove("hidden");
      });

    elements.backToProductionTeam &&
      elements.backToProductionTeam.addEventListener("click", () => {
        document
          .getElementById("pod-profile-section")
          .classList.add("hidden");
        document
          .getElementById("production-team-section")
          .classList.remove("hidden");
      });

    // Form submission
    elements.podProfileForm &&
      elements.podProfileForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(elements.podProfileForm);
        const data = Object.fromEntries(formData.entries());
        try {
          const success = await savePodProfile(data);
          success
            ? (window.location.href = "dashboard")
            : alert("Something went wrong. Please try again.");
        } catch (error) {
          console.error("Error saving pod profile:", error);
          alert("Something went wrong. Please try again.");
        }
      });

    // Dark Mode Toggle
    elements.darkModeToggle &&
      elements.darkModeToggle.addEventListener("click", () => {
        document.body.classList.toggle("dark-mode");
      });

    // Add Team Member
    elements.addTeamMemberButton &&
      elements.teamMembersContainer &&
      elements.addTeamMemberButton.addEventListener("click", () => {
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
        elements.teamMembersContainer.appendChild(newMember);
      });

    // Google Calendar integration
    if (elements.googleCalendarButton) {
      elements.googleCalendarButton.addEventListener("click", () => {
        const podcastEmail = document.getElementById("podEmail").value;
        if (podcastEmail.endsWith("@gmail.com")) {
          const oauth2Url = `https://accounts.google.com/o/oauth2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&response_type=code&scope=https://www.googleapis.com/auth/calendar`;
          window.open(oauth2Url, "_blank");
        } else {
          alert("Google Calendar integration is only available for Gmail accounts.");
        }
      });
    } else {
      console.error("Google Calendar button not found");
    }

    // Skip to Dashboard
    elements.skipToDashboard &&
      elements.skipToDashboard.addEventListener("click", () => {
        window.location.href = "dashboard";
      });

    // Podcast Social navigation
    elements.goToPodcastSocial &&
      elements.goToPodcastSocial.addEventListener("click", () => {
        const podName = document.getElementById("podName").value.trim();
        if (!podName) {
          alert("Please enter the Podcast Name.");
          return;
        }
        document
          .getElementById("podcastinfo-section")
          .classList.add("hidden");
        document
          .getElementById("podcastsocial-section")
          .classList.remove("hidden");
      });

    // Podcast Calendar navigation
    elements.goToPodcastCalendar &&
      elements.goToPodcastCalendar.addEventListener("click", () => {
        document
          .getElementById("podcastsocial-section")
          .classList.add("hidden");
        document
          .getElementById("podcastcalendar-section")
          .classList.remove("hidden");
      });

    // Podcast Team navigation
    elements.goToPodcastTeam &&
      elements.goToPodcastTeam.addEventListener("click", async () => {
        const podcastInfoForm = document.getElementById("podcastInfoForm");
        const formData = new FormData(podcastInfoForm);
        const data = Object.fromEntries(formData.entries());
        try {
          const success = await savePodProfile(data);
          if (success) {
            document
              .getElementById("podcastcalendar-section")
              .classList.add("hidden");
            document
              .getElementById("podcastteam-section")
              .classList.remove("hidden");
          } else {
            alert("Something went wrong. Please try again.");
          }
        } catch (error) {
          console.error("Error saving pod profile:", error);
          alert("Something went wrong. Please try again.");
        }
      });

    // Back navigation for podcast sections
    elements.backToPodcastInfo &&
      elements.backToPodcastInfo.addEventListener("click", () => {
        document
          .getElementById("podcastsocial-section")
          .classList.add("hidden");
        document
          .getElementById("podcastinfo-section")
          .classList.remove("hidden");
      });

    elements.backToPodcastSocial &&
      elements.backToPodcastSocial.addEventListener("click", () => {
        document
          .getElementById("podcastcalendar-section")
          .classList.add("hidden");
        document
          .getElementById("podcastsocial-section")
          .classList.remove("hidden");
      });

    elements.backToPodcastCalendar &&
      elements.backToPodcastCalendar.addEventListener("click", () => {
        document
          .getElementById("podcastteam-section")
          .classList.add("hidden");
        document
          .getElementById("podcastcalendar-section")
          .classList.remove("hidden");
      });

    // Dashboard navigation
    elements.goToDashboard &&
      elements.goToDashboard.addEventListener("click", () => {
        window.location.href = "dashboard";
      });

    // Invite team members and redirect to dashboard
    elements.inviteTeamMembers &&
      elements.inviteTeamMembers.addEventListener("click", () => {
        sendInvitations();
        window.location.href = "dashboard";
      });

    // Auto-fetch podcast data from RSS feed
    elements.podRssInput &&
      elements.podRssInput.addEventListener("input", async function () {
        const rssUrl = this.value.trim();
        if (rssUrl) {
          try {
            const feedData = await fetchRSSData(rssUrl);
            if (feedData && feedData.title) {
              const podNameInput = document.getElementById("podName");
              if (podNameInput) {
                podNameInput.value = feedData.title;
              }
            }
          } catch (error) {
            console.error("Failed to fetch RSS data:", error);
          }
        }
      });
  }

  // Setup dark mode with persistent state
  function setupDarkMode() {
    const darkModeToggle = document.getElementById("dark-mode-toggle");
    const body = document.body;
    if (localStorage.getItem("darkMode") === "enabled") {
      body.classList.add("dark-mode");
      if (darkModeToggle) darkModeToggle.textContent = "☀️";
    }
    if (darkModeToggle) {
      darkModeToggle.addEventListener("click", () => {
        body.classList.toggle("dark-mode");
        const darkEnabled = body.classList.contains("dark-mode");
        darkModeToggle.textContent = darkEnabled ? "☀️" : "🌙";
        localStorage.setItem("darkMode", darkEnabled ? "enabled" : "disabled");
      });
    }
  }

  // Setup language selection
  function setupLanguage() {
    const savedLang = localStorage.getItem("selectedLanguage") || "en";
    if (window.i18n) window.i18n.changeLanguage(savedLang);

    const languageButton = document.getElementById("language-button");
    const languageList = document.getElementById("language-list");

    languageButton &&
      languageButton.addEventListener("click", () =>
        languageList.classList.toggle("hidden")
      );

    languageList &&
      languageList.addEventListener("click", (event) => {
        if (event.target.tagName === "LI") {
          const selectedLang = event.target.getAttribute("data-lang");
          if (window.i18n) window.i18n.changeLanguage(selectedLang);
          languageList.classList.add("hidden");
        }
      });
  }

  // Send invitations to team members
  function sendInvitations() {
    const teamMembers = document.querySelectorAll(".team-member");
    const podName =
      (document.getElementById("podName") &&
        document.getElementById("podName").value) ||
      "your podcast";
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
        const body = `
          <p>Hi ${name}!</p>
          <p>You are hereby invited by PodManager.ai to join the team of ${podName}.</p>
          <p>Click here to join the team: <a href="${joinLink}">${joinLink}</a></p>
          <p>Welcome to PodManager.ai!</p>
        `;
        sendInvitation(email, subject, body);
      }
    });
  }

  // Points tracking setup for input fields and buttons
  function setupPointsTracking() {
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
  }

  // Initialize all setups
  setupNavigation();
  setupDarkMode();
  setupLanguage();
  setupPointsTracking();
});
