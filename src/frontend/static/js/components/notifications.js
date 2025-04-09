// Notification system for team dashboard
export function showNotification(title, message, type = "info") {
  // Remove any existing notification
  const existingNotification = document.querySelector(".notification");
  if (existingNotification) {
    existingNotification.remove();
  }

  // Import SVG icons
  import("./notificationsSvg.js").then(({ successSvg, errorSvg, infoSvg, closeSvg }) => {
    // Fetch the notification HTML
    fetch('../../templates/components/notifications.html')
      .then((response) => response.text())
      .then((html) => {
        
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;

        // Select the notification template
        const notificationTemplate = tempDiv.querySelector('#notification-template');

        const cssLink = loadCssLink(tempDiv, '#notification-style'); // The css path is in the div
        document.head.appendChild(cssLink); 

        // Clone the template to create a new notification instance
        const notification = notificationTemplate.cloneNode(true);
        notification.id = ''; // Remove the ID to avoid duplicates

        notification.className = `notification ${type}`;

        // Set icon based on type
        const iconSvg = type === "success" ? successSvg : type === "error" ? errorSvg : infoSvg;
        notification.querySelector(".notification-icon").innerHTML = iconSvg;

        notification.querySelector(".notification-title").textContent = title;
        notification.querySelector(".notification-message").textContent = message;

        notification.querySelector(".notification-close").innerHTML = closeSvg;

        document.body.appendChild(notification);

        // Add event listener to close button
        notification.querySelector(".notification-close").addEventListener("click", () => {
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
  });
}

export function showConfirmationPopup(title, message, onConfirm, onCancel) {
  // Remove any existing popup
  const existingPopup = document.querySelector(".confirmation-popup");
  if (existingPopup) {
    existingPopup.remove();
  }

  fetch('../../templates/components/notifications.html')
    .then((response) => response.text())
    .then((html) => {
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = html;

      // Select the confirmation popup template
      const popupTemplate = tempDiv.querySelector('#confirmation-popup-template');

      const cssLink = loadCssLink(tempDiv, '#notification-style'); // The css path is in the div
      document.head.appendChild(cssLink); 

      // Clone the template to create a new confirmation popup instance
      const popup = popupTemplate.cloneNode(true);
      popup.id = ''; // Remove the ID to avoid duplicates

      popup.querySelector('.form-title').textContent = title;
      popup.querySelector('.form-message').textContent = message;

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
    });
}

function loadCssLink(container, templateElement) {
  const cssPath = container.querySelector(templateElement).dataset.css; // This is the CSS path from the template
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = cssPath;
  return link;
}