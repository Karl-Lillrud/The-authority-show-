// Function to open the Email Config popup
function openEmailConfigPopup() {
  const popup = document.getElementById("email-config-popup");
  popup.style.display = "flex";
  fetchOutbox(); // Fetch and display the outbox when the popup opens
}

// Function to close the Email Config popup
function closeEmailConfigPopup() {
  const popup = document.getElementById("email-config-popup");
  popup.style.display = "none";
}

async function saveTriggerConfig() {
  const triggerSelect = document.getElementById("trigger-select");
  const triggerTime = document.getElementById("trigger-time");

  const triggerData = {
    trigger: triggerSelect.value,
    time: triggerTime.value,
  };

  try {
    const response = await fetch("/api/save-trigger", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(triggerData),
    });

    if (response.ok) {
      const result = await response.json();
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

async function fetchOutbox() {
  const outboxTable = document.getElementById("outbox-table");
  outboxTable.innerHTML = ""; // Clear existing rows

  try {
    const response = await fetch("/api/outbox");
    const data = await response.json();

    if (data.success) {
      data.data.forEach((email) => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${email.episode_id}</td>
          <td>${email.trigger_name}</td>
          <td>${email.guest_email}</td>
          <td>${email.subject}</td>
          <td>${new Date(email.timestamp).toLocaleString()}</td>
        `;
        outboxTable.appendChild(row);
      });
    } else {
      console.error("Failed to fetch outbox:", data.error);
    }
  } catch (error) {
    console.error("Error fetching outbox:", error);
  }
}

export function initEmailConfigFunctions() {
  // Open popup
  document
    .getElementById("email-config-btn")
    .addEventListener("click", openEmailConfigPopup);

  // Close popup
  document
    .getElementById("close-email-config-popup")
    .addEventListener("click", closeEmailConfigPopup);

  document
    .getElementById("close-email-config-btn")
    .addEventListener("click", closeEmailConfigPopup);

  // Save trigger configuration
  document
    .getElementById("save-trigger-btn")
    .addEventListener("click", saveTriggerConfig);
}