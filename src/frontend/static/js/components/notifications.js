export function showNotification(title, message, type = "info") {
  // Remove any existing notification
  const existingNotification = document.querySelector(".notification");
  if (existingNotification) {
    existingNotification.remove();
  }

  // Import SVG icons
  import("./notificationsSvg.js").then(({ successSvg, errorSvg, infoSvg, closeSvg }) => {
    // Fetch the notification HTML
    fetch('../../templates/components/notification.html')
      .then((response) => response.text())
      .then((html) => {
        // Create notification element
        const notification = document.createElement("div");
        notification.className = `notification ${type}`;
        notification.innerHTML = html;

        // Set icon based on type
        const iconSvg = type === "success" ? successSvg : type === "error" ? errorSvg : infoSvg;
        notification.querySelector(".notification-icon").innerHTML = iconSvg;

        // Set title and message
        notification.querySelector(".notification-title").textContent = title;
        notification.querySelector(".notification-message").textContent = message;

        // Set close button icon
        notification.querySelector(".notification-close").innerHTML = closeSvg;

        // Add to DOM
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

  // Fetch the popup HTML
  fetch("../../templates/components/notification.html")
    .then((response) => response.text())
    .then((html) => {
      // Create popup element
      const popup = document.createElement("div");
      popup.className = "popup confirmation-popup show";
      popup.innerHTML = html;

      // Set title and message
      popup.querySelector(".form-title").textContent = title;
      popup.querySelector(".form-message").textContent = message;

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