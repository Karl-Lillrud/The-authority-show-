document.addEventListener("DOMContentLoaded", function () {
    /* -----------------------
       Utility: Show Only One Section
    ------------------------- */
    function showSection(sectionId) {
      const sections = ["pod-name-section", "production-team-section", "pod-profile-section"];
      sections.forEach(id => {
        const section = document.getElementById(id);
        if (section) {
          section.classList.toggle("hidden", id !== sectionId);
        }
      });
    }

    /* -----------------------
       Fetch User's Podcasts & Fix Undefined URL
    ------------------------- */
    async function fetchUserPodcasts() {
      try {
          console.log("Fetching podcasts from /get_user_podcasts...");
          const response = await fetch("/get_user_podcasts");
  
          if (!response.ok) {
              throw new Error(`HTTP error! Status: ${response.status}`);
          }
  
          const data = await response.json();
          console.log("API Response:", data);
  
          if (!data || data.length === 0) {
              console.warn("No podcasts found.");
              return;
          }
  
          const podcastListContainer = document.getElementById("podcastList");
          if (!podcastListContainer) {
              console.error("Podcast list container not found.");
              return;
          }
  
          podcastListContainer.innerHTML = "";
          data.forEach(podcast => {
              const podLogo = podcast.podLogo && podcast.podLogo !== "undefined" ? podcast.podLogo : "/static/images/PodManagerLogo.png";
              const podName = podcast.podName ? podcast.podName : "Unknown Podcast";
  
              podcastListContainer.innerHTML += `
                  <div class="podcast-item">
                      <img src="${podLogo}" alt="${podName}" />
                      <h3>${podName}</h3>
                  </div>
              `;
          });
      } catch (error) {
          console.error("Error fetching user podcasts:", error);
      }
  }
  
  
  // Run this after the page loads
  document.addEventListener("DOMContentLoaded", fetchUserPodcasts);
  
  
    /* -----------------------
       Prevent Default Form Submissions
    ------------------------- */
    const podNameForm = document.getElementById("podNameForm");
    if (podNameForm) podNameForm.addEventListener("submit", e => e.preventDefault());
  
    const productionTeamForm = document.getElementById("productionTeamForm");
    if (productionTeamForm) productionTeamForm.addEventListener("submit", e => e.preventDefault());
  
    /* -----------------------
       COMMON FUNCTIONS
    ------------------------- */
    function generateInvitationLink(inviteeEmail, podcastName, hostEmail) {
      return `https://app.podmanager.ai/invite?invitee=${encodeURIComponent(inviteeEmail)}&podcast=${encodeURIComponent(podcastName)}&host=${encodeURIComponent(hostEmail)}`;
    }
  
    function sendInvitations() {
      const teamMembers = document.querySelectorAll(".team-member");
      const podcastName = document.getElementById("podName").value.trim() || "your podcast";
      const hostName = document.getElementById("hostName").value.trim() || "the host";
      const fromEmail = "theauthorityshow@gmail.com";
  
      teamMembers.forEach(member => {
        const inviteeNameField = member.querySelector(".team-name");
        const inviteeEmailField = member.querySelector(".team-email");
        if (inviteeNameField && inviteeEmailField) {
          const inviteeName = inviteeNameField.value.trim();
          const inviteeEmail = inviteeEmailField.value.trim();
          if (inviteeEmail) {
            const invitationLink = generateInvitationLink(inviteeEmail, podcastName, fromEmail);
            const emailBody = `Dear ${inviteeName}!
  
  You are hereby invited to the production team page of PodManager for your podcast ${podcastName} by your podcast's host!
  
  Click this link to accept the invitation and join the wonderful world of PodManager!
  ${invitationLink}
  
  Thank you for choosing PodManager!
  
  The PodManager Crew`;
            const subject = `Invitation to join the ${podcastName} Production Team`;
  
            fetch("/send_invite", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ from: fromEmail, to: inviteeEmail, subject, body: emailBody })
            })
              .then(response => response.json())
              .then(data => {
                if (data.success) {
                  console.log(`Invitation sent to ${inviteeEmail}`);
                } else {
                  console.error(`Failed to send invitation to ${inviteeEmail}: ${data.error}`);
                }
              })
              .catch(error => console.error("Error sending invitation:", error));
          }
        }
      });
    }
  
    async function fetchRSSData(rssUrl) {
      if (!rssUrl) return;
      try {
        const response = await fetch(`https://api.rss2json.com/v1/api.json?rss_url=${encodeURIComponent(rssUrl)}`);
        const data = await response.json();
        if (data.status === "ok") {
          if (data.feed?.title) {
            const podNameInput = document.getElementById("podName");
            if (podNameInput) podNameInput.value = data.feed.title;
          }
          if (data.feed?.link) {
            const websiteInput = document.getElementById("website");
            if (websiteInput) websiteInput.value = data.feed.link;
          }
        } else {
          console.error("RSS API error:", data);
        }
      } catch (error) {
        console.error("Error fetching RSS feed:", error);
      }
    }
  
    const podRssInput = document.getElementById("podRss");
    if (podRssInput) {
      podRssInput.addEventListener("input", function () {
        const rssUrl = this.value.trim();
        if (rssUrl) fetchRSSData(rssUrl);
      });
    }
  
    /* -----------------------
       Navigation: Pod Name -> Production Team
    ------------------------- */
    const goToProductionTeam = document.getElementById("goToProductionTeam");
    if (goToProductionTeam) {
      goToProductionTeam.addEventListener("click", async function () {
        const podName = document.getElementById("podName").value.trim();
        const podRss = document.getElementById("podRss").value.trim();
        if (!podName || !podRss) {
          alert("Please enter both Podcast Name and RSS URL.");
          return;
        }
        try {
          const response = await fetch("/register_podcast", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ podName, podRss })
          });
          const result = await response.json();
          if (response.ok) {
            showSection("production-team-section");
          } else {
            alert("Error: " + result.error);
          }
        } catch (error) {
          console.error("Failed to register podcast:", error);
          alert("Something went wrong. Please try again.");
        }
      });
    }
  
    /* -----------------------
       Production Team Section Setup
    ------------------------- */
    function setupProductionTeamSection() {
      const goToPodProfile = document.getElementById("goToPodProfile");
      const backToPodName = document.getElementById("backToPodName");
      const addTeamMemberButton = document.getElementById("addTeamMember");
      const teamMembersContainer = document.getElementById("teamMembersContainer");
  
      if (goToPodProfile) {
        goToPodProfile.addEventListener("click", () => {
          sendInvitations();
          showSection("pod-profile-section");
        });
      }
      if (backToPodName) {
        backToPodName.addEventListener("click", () => showSection("pod-name-section"));
      }
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
            </div>`;
          teamMembersContainer.appendChild(newMember);
        });
      }
    }
  
    /* -----------------------
       Pod Profile Section Setup
    ------------------------- */
    function setupPodProfileSection() {
      const backToProductionTeam = document.getElementById("backToProductionTeam");
      const podProfileForm = document.getElementById("podProfileForm");
  
      if (backToProductionTeam) {
        backToProductionTeam.addEventListener("click", () => showSection("production-team-section"));
      }
      if (podProfileForm) {
        podProfileForm.addEventListener("submit", event => {
          event.preventDefault();
          window.location.href = "/dashboard";
        });
      }
    }
  
    /* -----------------------
       Google Calendar Integration Setup
    ------------------------- */
    function setupGoogleCalendarIntegration() {
      const calendarConnectButton = document.getElementById("calendarConnectButton");
      if (calendarConnectButton) {
        calendarConnectButton.addEventListener("click", function () {
          window.open("/calendar_connect", "_blank");
        });
      }
    }
  
    /* -----------------------
       General UI Setup: Dark Mode, Language, Points System
    ------------------------- */
    function setupDarkMode() {
      const darkModeToggle = document.getElementById("dark-mode-toggle");
      const body = document.body;
      if (localStorage.getItem("darkMode") === "enabled") {
        body.classList.add("dark-mode");
        darkModeToggle.textContent = "☀️";
      }
      darkModeToggle.addEventListener("click", () => {
        body.classList.toggle("dark-mode");
        const enabled = body.classList.contains("dark-mode");
        darkModeToggle.textContent = enabled ? "☀️" : "🌙";
        localStorage.setItem("darkMode", enabled ? "enabled" : "disabled");
      });
    }
  
    function setupLanguageSettings() {
      const savedLang = localStorage.getItem("selectedLanguage") || "en";
      if (window.i18n) window.i18n.changeLanguage(savedLang);
      const languageButton = document.getElementById("language-button");
      const languageList = document.getElementById("language-list");
      if (languageButton && languageList) {
        languageButton.addEventListener("click", () => languageList.classList.toggle("hidden"));
        languageList.addEventListener("click", event => {
          if (event.target.tagName === "LI") {
            const selectedLang = event.target.getAttribute("data-lang");
            if (window.i18n) window.i18n.changeLanguage(selectedLang);
            languageList.classList.add("hidden");
          }
        });
      }
    }
  
    function setupPointsSystem() {
      const pointsSystem = {
        podName: 10,
        podRss: 10,
        podLogo: 10,
        hostName: 10,
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
        if (field) field.addEventListener("input", () => addPoints(fieldId, pointValue));
      }
  
      function trackButtonClick(buttonId, fieldKey, pointValue) {
        const button = document.getElementById(buttonId);
        if (button) button.addEventListener("click", () => addPoints(fieldKey, pointValue));
      }
  
      trackInputField("podName", pointsSystem.podName);
      trackInputField("podRss", pointsSystem.podRss);
      trackInputField("podLogo", pointsSystem.podLogo);
      trackInputField("hostName", pointsSystem.hostName);
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
      // Note: Ensure there is an element with id "blockUser" if you're tracking that.
    }
  
    /* -----------------------
       Initialize Setups & Show First Section
    ------------------------- */
    setupDarkMode();
    setupLanguageSettings();
    setupPointsSystem();
    setupProductionTeamSection();
    setupPodProfileSection();
    setupGoogleCalendarIntegration();
  
    // Start by showing only the Pod Name section.
    showSection("pod-name-section");
  });
  