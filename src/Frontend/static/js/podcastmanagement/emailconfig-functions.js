// emailconfig-functions.js
export function openEmailConfigPopup(podcastId) {
  const popup = document.getElementById("email-config-popup");
  popup.style.display = "flex";

  // Store the podcast ID for later use
  popup.setAttribute("data-podcast-id", podcastId);

  // Fetch the outbox emails for the selected podcast
  fetchOutbox(podcastId);
}

// Function to close the Email Config popup
function closeEmailConfigPopup() {
  const popup = document.getElementById("email-config-popup");
  popup.style.display = "none";
}

// Attach event listeners for the close buttons
document
  .getElementById("close-email-config-popup")
  .addEventListener("click", closeEmailConfigPopup);

document
  .getElementById("close-email-config-btn")
  .addEventListener("click", closeEmailConfigPopup);

async function saveTriggerConfig() {
  const triggerSelect = document.getElementById("trigger-select");
  const triggerTime = document.getElementById("trigger-time");

  const triggerData = {
    trigger: triggerSelect.value,
    time: triggerTime.value,
  };

  try {
    const response = await fetch("/save-trigger", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(triggerData),
    });

    if (response.ok) {
      alert("Trigger saved successfully!");
    } else {
      const error = await response.json();
      alert("Failed to save trigger: " + error.message);
    }
  } catch (error) {
    console.error("Error saving trigger:", error);
    alert("An error occurred while saving the trigger.");
  }
}

async function fetchOutbox(podcastId) {
  const outboxContainer = document.getElementById("outbox-container");
  outboxContainer.innerHTML = ""; // Clear existing emails

  try {
    const response = await fetch(`/outbox?podcastId=${podcastId}`);
    const data = await response.json();

    if (data.success) {
      if (data.data.length > 0) {
        data.data.forEach((email) => {
          const emailCard = document.createElement("div");
          emailCard.className = "email-card";

          const emailTime = new Date(email.timestamp).toLocaleString();

          emailCard.innerHTML = `
            <div class="email-header">
              <span class="email-recipient">To: ${email.guest_email}</span>
              <span class="email-time">${emailTime}</span>
            </div>
            <div class="email-body">
              <p class="email-subject"><strong>Subject:</strong> ${email.subject}</p>
              <p class="email-content">${email.content || "No content available."}</p>
            </div>
          `;

          outboxContainer.appendChild(emailCard);
        });
      } else {
        outboxContainer.innerHTML = `<p class="no-emails-message">No emails found for this podcast.</p>`;
      }
    } else {
      console.error("Failed to fetch outbox:", data.error);
    }
  } catch (error) {
    console.error("Error fetching outbox:", error);
  }
}

export function initEmailConfigFunctions() {
  const emailConfigButtons = document.querySelectorAll(".email-config-link");
  emailConfigButtons.forEach((button) => {
    button.addEventListener("click", (e) => {
      const podcastId = e.target.dataset.id; // Get the podcast ID from the button's data attribute
      openEmailConfigPopup(podcastId); // Open the email configuration popup
    });
  });
}

// Call this function after the DOM is fully loaded
document.addEventListener("DOMContentLoaded", initEmailConfigFunctions);