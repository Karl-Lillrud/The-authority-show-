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
                window.location.href = "placeholder.html"; // Change this to the actual destination later
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
    }

    setupNavigation();
});

function setupAddTeamMember() {
    document.getElementById("addTeamMember").addEventListener("click", () => {
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

function setupInvitationEmails() {
    document.getElementById("goToPodProfile").addEventListener("click", sendInvitations);
}

function sendInvitations() {
    const teamMembers = document.querySelectorAll(".team-member");
    const podName = document.getElementById("podName").value || "your podcast";
    const joinLink = "https://www.podmanager.ai";

    teamMembers.forEach(member => {
        const email = member.querySelector(".team-email").value;
        if (email) {
            const subject = encodeURIComponent(`Join the ${podName} team`);
            const body = encodeURIComponent(`Hi.\n\nPlease join me in producing the ${podName}. We use www.podmanager.ai to organize all work. Click here to join the team: ${joinLink}\n\nJust enter your email address to join the team.`);
            window.open(`mailto:${email}?subject=${subject}&body=${body}`, '_blank');
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

    darkModeToggle.addEventListener("click", () => {
        body.classList.toggle("dark-mode");
        const darkModeEnabled = body.classList.contains("dark-mode");
        darkModeToggle.textContent = darkModeEnabled ? "☀️" : "🌙";
        localStorage.setItem("darkMode", darkModeEnabled ? "enabled" : "disabled");
    });
}
document.addEventListener("DOMContentLoaded", () => {
    const savedLang = localStorage.getItem("selectedLanguage") || "en";
    if (window.i18n) {
        window.i18n.changeLanguage(savedLang);
    }

    document.getElementById("language-button").addEventListener("click", () => {
        document.getElementById("language-list").classList.toggle("hidden");
    });

    document.getElementById("language-list").addEventListener("click", (event) => {
        if (event.target.tagName === "LI") {
            const selectedLang = event.target.getAttribute("data-lang");
            if (window.i18n) {
                window.i18n.changeLanguage(selectedLang);
            }
            document.getElementById("language-list").classList.add("hidden");
        }
    });
});
