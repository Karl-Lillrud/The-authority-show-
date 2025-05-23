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
 * Shows a notification to the user
 * @param {string} title - The title of the notification
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (success, error, warning, info)
 * @param {Object} options - Additional options
 * @param {number} options.duration - Duration in milliseconds to show the notification
 * @param {Array} options.actions - Array of action buttons {text, onClick}
 */
export function showNotification(title, message, type = "info", options = {}) {
  const defaultOptions = {
    duration: 5000, // 5 seconds
    actions: [],
  };
  const settings = { ...defaultOptions, ...options };

  // Ensure notification container exists (it's also initialized in DOMContentLoaded)
  if (!notificationContainer) {
    notificationContainer = document.getElementById("notification-container");
    if (!notificationContainer) {
      notificationContainer = document.createElement("div");
      notificationContainer.id = "notification-container";
      document.body.appendChild(notificationContainer);
    }
  }
  // Apply styles to the container if they were missed during initial setup
  // These styles are from the new provided function
  notificationContainer.style.position = "fixed";
  notificationContainer.style.top = "20px";
  notificationContainer.style.right = "20px";
  notificationContainer.style.zIndex = "9999";
  notificationContainer.style.display = "flex";
  notificationContainer.style.flexDirection = "column";
  notificationContainer.style.gap = "10px";

  // Create notification element
  const notification = document.createElement("div");
  notification.className = `notification notification-${type}`; // Added base 'notification' class
  notification.style.backgroundColor = "#fff";
  notification.style.borderRadius = "8px";
  notification.style.boxShadow = "0 4px 12px rgba(0, 0, 0, 0.15)";
  notification.style.padding = "16px";
  notification.style.width = "320px";
  notification.style.maxWidth = "100%";
  notification.style.animation = "slideIn 0.3s ease-out forwards";
  notification.style.borderLeft = `4px solid ${getColorForType(type)}`;
  notification.style.position = "relative";
  notification.style.display = "flex"; // For icon and text alignment
  notification.style.alignItems = "flex-start"; // Align items to the top

  // Icon (optional, can be added here if desired, e.g., based on type)
  // For simplicity, the new version uses border color primarily.
  // If you want to re-add SVG icons:
  // const iconElement = document.createElement("div");
  // iconElement.className = "notification-icon-dynamic"; // New class for dynamic icon
  // iconElement.style.marginRight = "12px";
  // iconElement.style.flexShrink = "0";
  // switch (type) {
  //   case "success": iconElement.innerHTML = successSvg; break;
  //   case "error": iconElement.innerHTML = errorSvg; break;
  //   default: iconElement.innerHTML = infoSvg; break;
  // }
  // notification.appendChild(iconElement);

  const contentWrapper = document.createElement("div"); // Wrapper for title and message
  contentWrapper.style.flexGrow = "1";

  // Add title
  const titleElement = document.createElement("div");
  titleElement.className = "notification-title";
  titleElement.textContent = title;
  titleElement.style.fontWeight = "bold";
  titleElement.style.marginBottom = "8px";
  titleElement.style.color = "#333";
  contentWrapper.appendChild(titleElement);

  // Add message
  const messageElement = document.createElement("div");
  messageElement.className = "notification-message";
  messageElement.textContent = message;
  messageElement.style.color = "#666";
  messageElement.style.fontSize = "14px";
  messageElement.style.marginBottom = settings.actions.length ? "12px" : "0";
  contentWrapper.appendChild(messageElement);

  notification.appendChild(contentWrapper);

  // Add actions if any
  if (settings.actions.length) {
    const actionsContainer = document.createElement("div");
    actionsContainer.className = "notification-actions";
    actionsContainer.style.display = "flex";
    actionsContainer.style.justifyContent = "flex-end";
    actionsContainer.style.gap = "8px";
    actionsContainer.style.marginTop = "8px"; // Placed under message

    settings.actions.forEach((action) => {
      const button = document.createElement("button");
      button.textContent = action.text;
      button.onclick = () => {
        action.onClick();
        closeNotification(); // Optionally close notification on action
      };
      // Add basic styling for action buttons
      button.style.padding = "6px 12px";
      button.style.border = "1px solid #ccc";
      button.style.borderRadius = "4px";
      button.style.cursor = "pointer";
      button.style.backgroundColor = "#f0f0f0";
      actionsContainer.appendChild(button);
    });
    contentWrapper.appendChild(actionsContainer); // Add actions to content wrapper
  }

  // Add close button
  const closeButton = document.createElement("button");
  closeButton.innerHTML = "×"; // Using "×" character from new function
  closeButton.style.position = "absolute";
  closeButton.style.top = "8px";
  closeButton.style.right = "8px";
  closeButton.style.background = "none";
  closeButton.style.border = "none";
  closeButton.style.fontSize = "20px"; // Increased size for better clickability
  closeButton.style.cursor = "pointer";
  closeButton.style.color = "#999";
  closeButton.style.lineHeight = "1";
  closeButton.onclick = closeNotification;
  notification.appendChild(closeButton);

  // Add to container
  notificationContainer.appendChild(notification);

  // Set timeout to remove notification
  let timeoutId = null;
  if (settings.duration > 0) {
    timeoutId = setTimeout(closeNotification, settings.duration);
  }

  // Function to close notification
  function closeNotification() {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    notification.style.animation = "slideOut 0.3s ease-out forwards";
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 300); // Match animation duration
  }

  // Add CSS animations if not already present
  if (!document.getElementById("notification-styles")) {
    const style = document.createElement("style");
    style.id = "notification-styles";
    style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
    document.head.appendChild(style);
  }

  return {
    close: closeNotification,
  };
}

function getColorForType(type) {
  switch (type) {
    case "success":
      return "#10b981"; // Tailwind green-500
    case "error":
      return "#ef4444"; // Tailwind red-500
    case "warning":
      return "#f59e0b"; // Tailwind amber-500
    case "info":
    default:
      return "#3b82f6"; // Tailwind blue-500
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
