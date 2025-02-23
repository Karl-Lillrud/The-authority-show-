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

        if (goToProductionTeam) {
            goToProductionTeam.addEventListener("click", () => {
                document.getElementById("pod-name-section").classList.add("hidden");
                document.getElementById("production-team-section").classList.remove("hidden");
            });
        }

        if (goToPodProfile) {
            goToPodProfile.addEventListener("click", () => {
                sendInvitations();
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

        if (backToProductionTeam) {
            backToProductionTeam.addEventListener("click", () => {
                document.getElementById("pod-profile-section").classList.add("hidden");
                document.getElementById("production-team-section").classList.remove("hidden");
            });
        }

        if (podProfileForm) {
            podProfileForm.addEventListener("submit", (event) => {
                event.preventDefault();
                window.location.href = "dashboard"; // Change this to the actual destination later
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
        if (googleCalendarButton) {
            googleCalendarButton.addEventListener("click", () => {
                console.log("Google Calendar button clicked");
                const newTab = window.open("/connect_google_calendar", "_blank");
                if (newTab) {
                    newTab.focus();
                } else {
                    console.error("Failed to open new tab. Please check your browser settings.");
                }
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
    const podName = document.getElementById("podName") ? document.getElementById("podName").value : "your podcast";
    const joinLinkBase = "https://app.podmanager.ai/register"; // Updated base URL

    teamMembers.forEach(member => {
        const email = member.querySelector(".team-email").value;
        const name = member.querySelector(".team-name").value;
        const role = member.querySelector(".team-role").value;
        if (email) {
            const joinLink = `${joinLinkBase}?email=${encodeURIComponent(email)}&name=${encodeURIComponent(name)}&role=${encodeURIComponent(role)}`;
            const subject = `Join the ${podName} team`;x
            const body = `Hi ${name}!\n\nYou are hereby invited by PodManager.ai to join the team of ${podName}.\n\nClick here to join the team: <a href="${joinLink}">${joinLink}</a>\n\nWelcome to PodManager.ai!`;
            fetch('/send_invitation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, subject, body })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log(`Invitation sent to ${email}`);
                } else {
                    console.error(`Failed to send invitation to ${email}`);
                }
            })
            .catch(error => console.error('Error sending invitation:', error));
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
            localStorage.setItem("darkMode", darkModeEnabled ? "enabled" : "disabled");
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

    async function fetchRSSData(rssUrl) {
        if (!rssUrl) return;
        try {
            const response = await fetch(`https://api.rss2json.com/v1/api.json?rss_url=${encodeURIComponent(rssUrl)}`);
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
    

    function extractSocialMediaLink(description, platform) {
        const regex = new RegExp(`https?:\/\/www\.${platform}\.com\/[^\s]+`, "i");
        const match = description ? description.match(regex) : null;
        return match ? match[0] : "";
    }

    function extractEmail(description) {
        const regex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/;
        const match = description ? description.match(regex) : null;
        return match ? match[0] : "";
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
    
                try {
                    const response = await fetch("/register_podcast", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({ podName, podRss })
                    });
    
                    const result = await response.json();
    
                    if (response.ok) {
                        window.location.href = result.redirect_url; // Redirect to Production Team Page
                    } else {
                        alert("Error: " + result.error);
                    }
                } catch (error) {
                    console.error("Failed to register podcast:", error);
                    alert("Something went wrong. Please try again.");
                }
            });
        }
    });
    
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

