document.addEventListener("DOMContentLoaded", function () {
    /* ==================================================
       COMMON FUNCTIONS (Used Across Sections)
    ================================================== */
    function getEmailProviderUrl(hostEmail, toEmail, subject, body) {
      const domain = hostEmail.split("@")[1].toLowerCase();
      if (domain.includes("gmail")) {
        return `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(
          toEmail
        )}&su=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      } else if (
        domain.includes("outlook") ||
        domain.includes("hotmail") ||
        domain.includes("live")
      ) {
        return `https://outlook.live.com/mail/0/deeplink/compose?to=${encodeURIComponent(
          toEmail
        )}&subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      } else if (domain.includes("yahoo")) {
        return `https://compose.mail.yahoo.com/?to=${encodeURIComponent(
          toEmail
        )}&subj=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      }
      return `mailto:${encodeURIComponent(toEmail)}?subject=${encodeURIComponent(
        subject
      )}&body=${encodeURIComponent(body)}`;
    }
  
    function generateInvitationLink(inviteeEmail, podcastName, hostEmail) {
      // In production, include a secure token in the link.
      return `https://app.podmanager.ai/invite?invitee=${encodeURIComponent(
        inviteeEmail
      )}&podcast=${encodeURIComponent(podcastName)}&host=${encodeURIComponent(hostEmail)}`;
    }
  
    function sendInvitations() {
      const teamMembers = document.querySelectorAll(".team-member");
      const podcastName = document.getElementById("podName").value || "your podcast";
      const hostName = document.getElementById("hostName").value || "the host";
      // Ensure window.hostEmail is set via a script tag in your template:
      // <script>window.hostEmail = "{{ session.email }}";</script>
      const hostEmail = window.hostEmail || "";
  
      teamMembers.forEach(member => {
        const inviteeNameField = member.querySelector(".team-name");
        const inviteeEmailField = member.querySelector(".team-email");
        if (inviteeNameField && inviteeEmailField) {
          const inviteeName = inviteeNameField.value.trim();
          const inviteeEmail = inviteeEmailField.value.trim();
          if (inviteeEmail) {
            const invitationLink = generateInvitationLink(inviteeEmail, podcastName, hostEmail);
            const emailBody = `Dear ${inviteeName}!
  
  You are hereby invited to the production team page of PodManager for your PodCast ${podcastName} by the PodCast host ${hostName}!
  
  Click this link to accept the invitation and join the wonderful world of PodManager!
  ${invitationLink}
  
  Thank you for choosing PodManager!
  
  PodManager Crew`;
            const subject = `Invitation to join the ${podcastName} Production Team`;
            let composeUrl;
            if (hostEmail) {
              composeUrl = getEmailProviderUrl(hostEmail, inviteeEmail, subject, emailBody);
            } else {
              composeUrl = `mailto:${encodeURIComponent(inviteeEmail)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(emailBody)}`;
            }
            window.open(composeUrl, "_blank");
          }
        }
      });
    }
  
    /* ==================================================
       POD NAME SECTION
       - Handles RSS feed fetching and auto-generates Pod Name and Website.
       - Handles podcast registration.
    ================================================== */
    async function fetchRSSData(rssUrl) {
      if (!rssUrl) return;
      try {
        const response = await fetch(`https://api.rss2json.com/v1/api.json?rss_url=${encodeURIComponent(rssUrl)}`);
        const data = await response.json();
        if (data.status === "ok") {
          if (data.feed && data.feed.title) {
            const podNameInput = document.getElementById("podName");
            if (podNameInput) {
              podNameInput.value = data.feed.title;
            }
          }
          if (data.feed && data.feed.link) {
            const websiteInput = document.getElementById("website");
            if (websiteInput) {
              websiteInput.value = data.feed.link;
            }
          }
        } else {
          console.error("RSS API returned an error:", data);
        }
      } catch (error) {
        console.error("Error fetching RSS feed:", error);
      }
    }
  
    // RSS input listener for the Pod Name Section.
    const podRssInput = document.getElementById("podRss");
    if (podRssInput) {
      podRssInput.addEventListener("input", function () {
        const rssUrl = this.value.trim();
        if (rssUrl) {
          fetchRSSData(rssUrl);
        }
      });
    }
  
    // Podcast registration (Go button) in the Pod Name Section.
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
            // Use the redirect URL returned from the backend (make sure it matches your app routes)
            window.location.href = result.redirect_url;
          } else {
            alert("Error: " + result.error);
          }
        } catch (error) {
          console.error("Failed to register podcast:", error);
          alert("Something went wrong. Please try again.");
        }
      });
    }
  
    /* ==================================================
       PRODUCTION TEAM SECTION
       - Handles navigation and invitation functionality.
    ================================================== */
    function setupProductionTeamSection() {
      const goToPodProfile = document.getElementById("goToPodProfile");
      const backToPodName = document.getElementById("backToPodName");
      const addTeamMemberButton = document.getElementById("addTeamMember");
      const teamMembersContainer = document.getElementById("teamMembersContainer");
  
      if (goToPodProfile) {
        goToPodProfile.addEventListener("click", () => {
          sendInvitations();
          // Hide Production Team Section and show Pod Profile Section.
          document.getElementById("production-team-section").classList.add("hidden");
          document.getElementById("pod-profile-section").classList.remove("hidden");
        });
      }
  
      if (backToPodName) {
        backToPodName.addEventListener("click", () => {
          document.getElementById("production-team-section").classList.add("hidden");
          document.getElementById("pod-name-section").classList.remove("hidden");
        });
      }
  
      // This function adds a new team member form group.
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
    }
  
    /* ==================================================
       POD PROFILE SECTION
       - Handles pod profile form submission and navigation.
    ================================================== */
    function setupPodProfileSection() {
      const backToProductionTeam = document.getElementById("backToProductionTeam");
      const podProfileForm = document.getElementById("podProfileForm");
  
      if (backToProductionTeam) {
        backToProductionTeam.addEventListener("click", () => {
          document.getElementById("pod-profile-section").classList.add("hidden");
          document.getElementById("production-team-section").classList.remove("hidden");
        });
      }
  
      if (podProfileForm) {
        podProfileForm.addEventListener("submit", (event) => {
          event.preventDefault();
          window.location.href = "/dashboard";
        });
      }
    }
  
    /* ==================================================
       SETUP FOR ADDING TEAM MEMBERS (if not already defined)
    ================================================== */
    function setupAddTeamMember() {
      const addButton = document.getElementById("addTeamMember");
      if (addButton) {
        addButton.addEventListener("click", () => {
          const container = document.getElementById("teamMembersContainer");
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
        });
      }
    }
  
    /* ==================================================
       GENERAL UI SETUP (Dark Mode, Language, Points, etc.)
    ================================================== */
    function setupDarkMode() {
      const darkModeToggle = document.getElementById("dark-mode-toggle");
      const body = document.body;
      const isDarkMode = localStorage.getItem("darkMode") === "enabled";
      if (isDarkMode) {
        body.classList.add("dark-mode");
        darkModeToggle.textContent = "☀️";
      }
      darkModeToggle.addEventListener("click", () => {
        body.classList.toggle("dark-mode");
        const darkModeEnabled = body.classList.contains("dark-mode");
        darkModeToggle.textContent = darkModeEnabled ? "☀️" : "🌙";
        localStorage.setItem("darkMode", darkModeEnabled ? "enabled" : "disabled");
      });
    }
  
    function setupLanguageSettings() {
      const savedLang = localStorage.getItem("selectedLanguage") || "en";
      if (window.i18n) {
        window.i18n.changeLanguage(savedLang);
      }
      const languageButton = document.getElementById("language-button");
      const languageList = document.getElementById("language-list");
      if (languageButton && languageList) {
        languageButton.addEventListener("click", () => {
          languageList.classList.toggle("hidden");
        });
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
    }
  
    function setupPointsSystem() {
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
  
    /* ==================================================
       INITIALIZE GENERAL UI SETUPS
    ================================================== */
    setupDarkMode();
    setupLanguageSettings();
    setupPointsSystem();
  
    /* ==================================================
       INITIALIZE SECTION-SPECIFIC SETUPS
    ================================================== */
    setupProductionTeamSection();
    setupPodProfileSection();
    setupAddTeamMember();
  });
  