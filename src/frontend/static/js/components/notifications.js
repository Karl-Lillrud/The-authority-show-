// Import SVGs
import { successSvg, errorSvg, infoSvg, closeSvg } from "./notificationsSvg.js";

let notificationContainer = null;
let confirmationPopupTemplate = null;

// --- Simplified DOMContentLoaded ---
document.addEventListener("DOMContentLoaded", () => {
  // Create notification container if it doesn't exist
  if (!document.getElementById("notification-container")) {
    notificationContainer = document.createElement("div");
    notificationContainer.id = "notification-container";
    document.body.appendChild(notificationContainer);
  } else {
    notificationContainer = document.getElementById("notification-container");
  }

  // Find the confirmation popup template directly in the DOM
  const popupTemplateElement = document.getElementById(
    "confirmation-popup-template"
  );
  if (popupTemplateElement) {
    confirmationPopupTemplate = popupTemplateElement.outerHTML;
  } else {
    console.warn("Confirmation popup template not found in the DOM.");
  }
});
// --- End Simplified DOMContentLoaded ---

/**
 * Displays a notification message.
 * @param {string} title - The title of the notification.
 * @param {string} message - The message content.
 * @param {string} type - The type of notification ('success', 'error', 'info', 'warning').
 * @param {number} duration - Duration in milliseconds before auto-closing (0 for no auto-close).
 */
export function showNotification(
  title,
  message,
  type = "info",
  duration = 5000
) {
  // Ensure container exists (might run before DOMContentLoaded in some scenarios)
  if (!notificationContainer) {
    if (!document.getElementById("notification-container")) {
      notificationContainer = document.createElement("div");
      notificationContainer.id = "notification-container";
      document.body.appendChild(notificationContainer);
    } else {
      notificationContainer = document.getElementById("notification-container");
    }
  }

  // Find the template directly in the DOM
  const template = document.getElementById("notification-template");
  if (!template) {
    console.error("Notification template not found in the DOM!");
    return;
  }

  const notification = template.cloneNode(true);
  notification.removeAttribute("id"); // Remove ID from clone
  // Use specific class for type, remove generic 'notification-type'
  notification.classList.add(type, "show"); // Add type class directly (e.g., 'success', 'error')

  notification.querySelector(".notification-title").textContent = title;
  notification.querySelector(".notification-message").textContent = message;

  // Set SVG icon based on type
  const iconContainer = notification.querySelector(".notification-icon");
  switch (type) {
    case "success":
      iconContainer.innerHTML = successSvg;
      break;
    case "error":
      iconContainer.innerHTML = errorSvg;
      break;
    case "info":
    default:
      iconContainer.innerHTML = infoSvg;
      break;
  }

  const closeButton = notification.querySelector(".notification-close");
  // Set SVG for close button
  closeButton.innerHTML = closeSvg;
  closeButton.addEventListener("click", () => {
    notification.classList.remove("show");
    setTimeout(() => {
      notification.remove();
    }, 500);
  });

  notificationContainer.appendChild(notification);

  // Auto hide after specified duration
  if (duration > 0) {
    setTimeout(() => {
      if (notificationContainer.contains(notification)) {
        notification.classList.remove("show");
        setTimeout(() => {
          if (notificationContainer.contains(notification)) {
            notification.remove();
          }
        }, 500);
      }
    }, duration);
  }
}

// Confirmation popup system, see team/modals.js on how to use it
export function showConfirmationPopup(title, message, onConfirm, onCancel) {
  // Remove any existing popup
  const existingPopup = document.querySelector(".confirmation-popup");
  if (existingPopup) {
    existingPopup.remove();
  }

  if (!confirmationPopupTemplate) {
    console.error("Confirmation popup template not found in the DOM!");
    return;
  }

  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = confirmationPopupTemplate;

  const popup = tempDiv.firstElementChild;
  popup.className = "confirmation-popup show";

  popup.querySelector(".confirm-form-title").textContent = title;
  popup.querySelector(".confirm-form-message").textContent = message;

  document.body.appendChild(popup);

  popup.querySelector("#confirmPopupBtn").addEventListener("click", () => {
    onConfirm();
    popup.remove();
  });

  popup.querySelector("#cancelPopupBtn").addEventListener("click", () => {
    if (onCancel) onCancel();
    popup.remove();
  });
}
