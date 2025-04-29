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

document
  .getElementById("save-trigger-btn")
  .addEventListener("click", saveTriggerConfig);

async function saveTriggerConfig() {
  const triggerSelect = document.getElementById("trigger-select");
  const triggerTime = document.getElementById("trigger-time");
  const podcastId = document
    .getElementById("email-config-popup")
    .getAttribute("data-podcast-id");

  if (!triggerSelect.value) {
    alert("Please select a trigger before saving.");
    return;
  }

  const timeValue = triggerTime.value;
  if (!timeValue || isNaN(timeValue) || timeValue <= 0) {
    alert("Please enter a valid time in hours (greater than 0).");
    return;
  }

  // Fetch the correct status from the backend
  const response = await fetch(`/get-trigger-config?podcastId=${podcastId}&triggerName=${triggerSelect.value}`);
  const data = await response.json();
  const status = data.success && data.data ? data.data.status : "Not Recorded"; // Default to "Not Recorded"

  const triggerData = {
    podcast_id: podcastId,
    trigger_name: triggerSelect.value,
    status: status, // Use the fetched status
    time_check: parseInt(timeValue, 10),
  };

  try {
    const saveResponse = await fetch("/save-trigger", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(triggerData),
    });

    const saveResult = await saveResponse.json();
    if (saveResult.success) {
      alert("Trigger saved successfully!");
    } else {
      alert(`Error saving trigger: ${saveResult.error}`);
    }
  } catch (error) {
    console.error("Error saving trigger:", error);
    alert("An error occurred while saving the trigger.");
  }
}

async function fetchOutbox(podcastId) {
  const outboxList = document.getElementById("outbox-list");
  outboxList.innerHTML = ""; // Clear existing emails

  try {
    const response = await fetch(`/outbox?podcastId=${podcastId}`);
    const data = await response.json();

    if (data.success) {
      if (data.data.length === 0) {
        outboxList.innerHTML = "<p>No emails found in the outbox.</p>";
      } else {
        data.data.forEach((email) => {
          const emailItem = document.createElement("div");
          emailItem.className = "email-item";
          emailItem.innerHTML = `
            <div class="email-header">${email.subject}</div>
            <div class="email-meta">
              <strong>To:</strong> ${email.guest_email} 
              <span style="margin-left: 1rem;"><strong>Sent:</strong> ${email.timestamp}</span>
            </div>
            <div class="email-content">${email.content}</div>
          `;
          outboxList.appendChild(emailItem);
        });
      }
    } else {
      outboxList.innerHTML = `<p>Error: ${data.error}</p>`;
    }
  } catch (error) {
    console.error("Error fetching outbox:", error);
    outboxList.innerHTML = "<p>Error loading outbox emails.</p>";
  }
}

// Function to toggle email content visibility
function toggleEmailContent(index) {
  const preview = document.getElementById(`email-preview-${index}`);
  const fullContent = document.getElementById(`email-full-content-${index}`);
  const button = document.querySelector(`.show-email-btn[data-index="${index}"]`);

  if (fullContent.classList.contains("hidden")) {
    fullContent.classList.remove("hidden");
    preview.classList.add("hidden");
    button.textContent = "Hide Email";
  } else {
    fullContent.classList.add("hidden");
    preview.classList.remove("hidden");
    button.textContent = "Read Email";
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

async function fetchTriggerConfig(podcastId, triggerName) {
  const triggerInfoBox = document.getElementById("trigger-info-box");
  triggerInfoBox.textContent = "Loading current configuration..."; // Show loading text

  try {
    const response = await fetch(`/get-trigger-config?podcastId=${podcastId}&triggerName=${triggerName}`);
    const data = await response.json();

    if (data.success && data.data) {
      const timeCheck = data.data.time_check;
      const status = data.data.status;
      triggerInfoBox.textContent = `Current Time: ${timeCheck} hours, Status: ${status}`;
    } else {
      triggerInfoBox.textContent = "No custom configuration found. Using default settings.";
    }
  } catch (error) {
    console.error("Error fetching trigger configuration:", error);
    triggerInfoBox.textContent = "Error loading configuration.";
  }
}

// Attach event listener to the trigger dropdown
document.getElementById("trigger-select").addEventListener("change", (event) => {
  const podcastId = document.getElementById("email-config-popup").getAttribute("data-podcast-id");
  const triggerName = event.target.value;
  fetchTriggerConfig(podcastId, triggerName);
});