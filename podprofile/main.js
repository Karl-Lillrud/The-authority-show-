// main.js - Form Handling and UI Interaction

document.addEventListener("DOMContentLoaded", () => {
    initializeI18n();
    setupFormHandler();
    setupDarkMode();
});

function setupFormHandler() {
    const podProfileForm = document.getElementById("podProfileForm");
    podProfileForm?.addEventListener("submit", async (event) => {
        event.preventDefault();
        
        const podName = document.getElementById("podName").value.trim();
        const podRss = document.getElementById("podRss").value.trim();
        
        if (!podName || !podRss) {
            showToast("Please fill all required fields.");
            return;
        }

        try {
            await savePodProfile({ podName, podRss });
            showToast("Profile saved successfully.");
            podProfileForm.reset();
        } catch (error) {
            showToast("Error saving profile.");
            console.error("Profile submission error:", error);
        }
    });
}

async function savePodProfile(profileData) {
    return new Promise((resolve) => setTimeout(() => resolve(profileData), 1000));
}

function showToast(message) {
    const toast = document.getElementById("toast");
    const toastMessage = toast?.querySelector("span");
    if (toastMessage) {
        toastMessage.textContent = message;
        toast.classList.add("show");
        setTimeout(() => toast.classList.remove("show"), 3000);
    }
}

function setupDarkMode() {
    const toggle = document.getElementById("dark-mode-toggle");
    toggle?.addEventListener("click", () => {
        document.body.classList.toggle("dark-mode");
        localStorage.setItem("theme", document.body.classList.contains("dark-mode") ? "dark" : "light");
    });

    if (localStorage.getItem("theme") === "dark") {
        document.body.classList.add("dark-mode");
    }
}
