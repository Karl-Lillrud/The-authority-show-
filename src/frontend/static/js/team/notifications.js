// Notification system for team dashboard
export function showNotification(title, message, type = "info") {
  // Remove any existing notification
  const existingNotification = document.querySelector(".notification");
  if (existingNotification) {
    existingNotification.remove();
  }

  // Import SVG icons
  import("./teamSvg.js").then(({ successSvg, errorSvg, infoSvg, closeSvg }) => {
    // Create notification elements
    const notification = document.createElement("div");
    notification.className = `notification ${type}`;

    // Icon based on type
    let iconSvg = "";
    if (type === "success") {
      iconSvg = successSvg;
    } else if (type === "error") {
      iconSvg = errorSvg;
    } else {
      iconSvg = infoSvg;
    }

    notification.innerHTML = `
        <div class="notification-icon">${iconSvg}</div>
        <div class="notification-content">
          <div class="notification-title">${title}</div>
          <div class="notification-message">${message}</div>
        </div>
        <div class="notification-close">
          ${closeSvg}
        </div>
      `;

    // Add to DOM
    document.body.appendChild(notification);

    // Add event listener to close button
    notification
      .querySelector(".notification-close")
      .addEventListener("click", () => {
        notification.classList.remove("show");
        setTimeout(() => {
          notification.remove();
        }, 500);
      });

    // Show notification with animation
    setTimeout(() => {
      notification.classList.add("show");
    }, 10);

    // Auto hide after 5 seconds
    setTimeout(() => {
      if (document.body.contains(notification)) {
        notification.classList.remove("show");
        setTimeout(() => {
          if (document.body.contains(notification)) {
            notification.remove();
          }
        }, 500);
      }
    }, 5000);
  });
}

export function showConfirmationPopup(title, message, onConfirm, onCancel) {
  // Remove any existing popup
  const existingPopup = document.querySelector(".confirmation-popup");
  if (existingPopup) {
    existingPopup.remove();
  }

  // Create popup elements
  const popup = document.createElement("div");
  popup.className = "popup confirmation-popup show";

  popup.innerHTML = `
      <div class="form-box">
        <h2 class="form-title">${title}</h2>
        <p>${message}</p>
        <div class="form-actions">
          <button class="cancel-btn" id="cancelPopupBtn">Cancel</button>
          <button class="save-btn" id="confirmPopupBtn">Confirm</button>
        </div>
      </div>
    `;

  // Add to DOM
  document.body.appendChild(popup);

  // Add event listeners for buttons
  document.getElementById("confirmPopupBtn").addEventListener("click", () => {
    onConfirm();
    popup.remove();
  });

  document.getElementById("cancelPopupBtn").addEventListener("click", () => {
    if (onCancel) onCancel();
    popup.remove();
  });
}
