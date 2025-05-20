import {
  fetchAccount,
  updateAccount,
  deleteAccount,
  uploadProfilePicture,
  deleteUserAccount,
  updateProfile
} from "/static/requests/accountRequests.js";
import { showNotification } from "../components/notifications.js";
import { fetchPurchases } from "/static/js/billing/billing.js";
import {
  fetchStoreCredits,
  updateSubscriptionUI
} from "/static/js/account/subscription.js";

document.addEventListener("DOMContentLoaded", () => {
  // Hides the edit buttons when in non-edit mode
  const formActions = document.querySelector(".form-actions");
  const uploadBtn = document.getElementById("upload-pic");
  if (uploadBtn) {
    uploadBtn.style.display = "none";
  }
  const profilePictureOverlay = document.querySelector(".profile-pic-overlay");
  if (profilePictureOverlay) {
    profilePictureOverlay.style.display = "none";
  }

  const requiredFields = document.querySelectorAll(".required-profile");
  requiredFields.forEach((field) => {
    field.style.display = "none";
  });

  // Hide the edit profile button in view mode
  const editProfileBtn = document.getElementById("edit-profile-btn");
  if (editProfileBtn) {
    editProfileBtn.style.display = "none";
  }

  const profilePic = document.getElementById("profile-pic");
  const profilePicInput = document.getElementById("profile-pic-input"); // Verify this ID matches HTML
  const profilePicOverlay = document.querySelector(".profile-pic-overlay"); // Verify this selector
  const uploadButton = document.getElementById("upload-pic"); // Verify this ID matches HTML

  // --- Define triggerFileUpload function ---
  function triggerFileUpload() {
    if (profilePicInput) {
      profilePicInput.click(); // Programmatically click the hidden file input
    }
  }
  // --- End define triggerFileUpload function ---

  // --- Define handleFileSelect function ---
  function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file && profilePic) {
      // Store the current profile picture URL
      const currentProfilePicUrl = profilePic.src;

      // --- Call the upload function ---
      uploadProfilePicture(file)
        .then((data) => {
          if (data.profilePicUrl) {
            // Create a new Image object to preload the new image
            const img = new Image();
            img.onload = function() {
              profilePic.src = data.profilePicUrl;
              // Store the new URL in localStorage as a backup
              localStorage.setItem('lastProfilePicUrl', data.profilePicUrl);
            };
            img.onerror = function() {
              profilePic.src = currentProfilePicUrl;
            };
            img.src = data.profilePicUrl;

            showNotification(
              "Success",
              "Profile picture updated successfully!",
              "success"
            );
          } else {
            showNotification(
              "Error",
              data.error || "Failed to upload profile picture.",
              "error"
            );
            profilePic.src = currentProfilePicUrl;
          }
        })
        .catch((error) => {
          showNotification(
            "Error",
            `Upload failed: ${error.message}`,
            "error"
          );
          profilePic.src = currentProfilePicUrl;
        });
    }
  }
  // --- End define handleFileSelect function ---

  // Function to load account data
  async function loadAccountData(preserveProfilePic = false) {
    try {
      // Explicitly call fetchAccount
      const wrapper = await fetchAccount();
      const account = wrapper.account;

      // Set profile picture only if not preserving current one
      if (profilePic) {
        const currentSrc = profilePic.src;
        if (!preserveProfilePic) {
          if (account.profile_pic_url) {
            profilePic.src = account.profile_pic_url;
          } else {
            profilePic.src = "/static/images/profilepic.png";
          }
        }
      }

      // Set form field values
      const fullNameInput = document.getElementById("full-name");
      const emailInput = document.getElementById("email");
      const phoneInput = document.getElementById("phone");

      if (fullNameInput) fullNameInput.value = account.full_name || "";
      if (emailInput) emailInput.value = account.email || "";
      if (phoneInput) phoneInput.value = account.phone || "";

      // Update the display values
      const displayFullName = document.getElementById("display-full-name");
      const displayEmail = document.getElementById("display-email");
      const displayPhone = document.getElementById("display-phone");

      if (displayFullName) displayFullName.textContent = account.full_name || "Not provided";
      if (displayEmail) displayEmail.textContent = account.email || "Not provided";
      if (displayPhone) displayPhone.textContent = account.phone || "Not provided";
    } catch (error) {
      showNotification(
        "Error",
        `Failed to load account data: ${error.message}`,
        "error"
      );
      if (profilePic && !preserveProfilePic) {
        profilePic.src = "/static/images/profilepic.png";
      }
    }
  }

  // Function to load purchase history
  async function loadPurchaseHistory() {
    const purchasesList = document.getElementById("purchases-list");
    const noPurchasesMessage = document.getElementById("no-purchases-message");
    if (!purchasesList || !noPurchasesMessage) return;

    try {
      // Call the imported fetchPurchases function
      const purchases = await fetchPurchases();

      purchasesList.innerHTML = ""; // Clear previous list

      if (purchases && purchases.length > 0) {
        noPurchasesMessage.style.display = "none"; // Hide 'no purchases' message
        purchases.forEach((purchase) => {
          const li = document.createElement("li");
          li.className = "purchase-item";

          const purchaseDate = new Date(
            purchase.created * 1000
          ).toLocaleDateString();
          const amount = (purchase.amount_total / 100).toFixed(2); // Convert cents to dollars
          const currency = purchase.currency.toUpperCase();
          const status = purchase.payment_status;
          const description =
            purchase.line_items && purchase.line_items.length > 0
              ? purchase.line_items[0].description
              : "N/A"; // Get description from first line item

          li.innerHTML = `
            <div class="purchase-details">
              <span class="purchase-date">${purchaseDate}</span>
              <span class="purchase-description">${description}</span>
            </div>
            <div class="purchase-info">
              <span class="purchase-amount">${amount} ${currency}</span>
              <span class="purchase-status status-${status}">${status}</span>
            </div>
          `;
          purchasesList.appendChild(li);
        });
      } else {
        noPurchasesMessage.style.display = "block"; // Show 'no purchases' message
      }
    } catch (error) {
      console.error("Error loading purchase history:", error);
      showNotification(
        "Error",
        `Failed to load purchase history: ${error.message}`,
        "error"
      );
      noPurchasesMessage.textContent = "Error loading purchase history.";
      noPurchasesMessage.style.display = "block";
    }
  }

  // Function to load credit history
  async function loadCreditHistory() {
    const historyContainer = document.getElementById("billing-history-rows");
    const noHistoryMessage = document.getElementById("no-purchases-message");

    if (!historyContainer || !noHistoryMessage) return;

    try {
      const response = await fetch("/api/purchases/history", {
        credentials: "same-origin"
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch purchase history: ${response.status}`);
      }

      const data = await response.json();
      const purchases = data.purchases || [];

      historyContainer.innerHTML = ""; // Clear existing rows

      if (purchases.length === 0) {
        noHistoryMessage.style.display = "block"; // Show 'no history' message
        return;
      }

      noHistoryMessage.style.display = "none"; // Hide 'no history' message

      // Populate the billing history table
      purchases.forEach((purchase) => {
        const date = new Date(purchase.date).toLocaleDateString("en-US", {
          year: "numeric",
          month: "short",
          day: "numeric"
        });

        const statusClass = purchase.status?.toLowerCase() || "unknown";

        const row = document.createElement("div");
        row.className = "billing-row";
        row.innerHTML = `
          <div class="billing-cell">${date}</div>
          <div class="billing-cell">${purchase.description || "N/A"}</div>
          <div class="billing-cell">$${parseFloat(purchase.amount).toFixed(
            2
          )}</div>
          <div class="billing-cell">
            <span class="status-${statusClass}">
              ${purchase.status || "Unknown"}
            </span>
          </div>
          <div class="billing-cell">
            ${
              purchase.details
                ? `<button class="details-btn" data-details='${JSON.stringify(
                    purchase.details
                  )}'>Details</button>`
                : "N/A"
            }
          </div>
        `;
        historyContainer.appendChild(row);
      });

      // Add event listeners to "Details" buttons
      document.querySelectorAll(".details-btn").forEach((button) => {
        button.addEventListener("click", function () {
          const details = JSON.parse(this.getAttribute("data-details"));
          showPurchaseDetails(details);
        });
      });
    } catch (error) {
      console.error("Error loading purchase history:", error);
      noHistoryMessage.textContent = "Error loading purchase history.";
      noHistoryMessage.style.display = "block";
    }
  }

  // Function to show purchase details in a modal
  function showPurchaseDetails(details) {
    const modal = document.getElementById("details-modal");
    const modalContent = document.getElementById("details-modal-content");

    if (!modal || !modalContent) return;

    // Clear previous details
    modalContent.innerHTML = "";

    if (details.length === 0) {
      modalContent.innerHTML = "<p>No details available for this purchase.</p>";
    } else {
      const list = document.createElement("ul");
      details.forEach((item) => {
        const listItem = document.createElement("li");
        listItem.textContent = `${item.product} - Quantity: ${
          item.quantity
        }, Price: $${item.price.toFixed(2)}`;
        list.appendChild(listItem);
      });
      modalContent.appendChild(list);
    }

    // Show the modal
    modal.style.display = "block";
  }

  // Close modal when clicking outside or on close button
  document.addEventListener("click", (event) => {
    const modal = document.getElementById("details-modal");
    if (
      modal &&
      (event.target === modal || event.target.classList.contains("close-modal"))
    ) {
      modal.style.display = "none";
    }
  });

  function displayPurchaseHistory(purchases) {
    const historyContainer = document.getElementById("billing-history-rows");
    const noHistoryMessage = document.getElementById("no-purchases-message");

    if (!historyContainer) return;

    // Clear loading message
    historyContainer.innerHTML = "";

    if (!purchases || purchases.length === 0) {
      // Show no history message
      noHistoryMessage.style.display = "block";
      return;
    }

    // Hide no history message if we have purchases
    noHistoryMessage.style.display = "none";

    // Sort purchases by date, newest first
    purchases.sort((a, b) => new Date(b.date) - new Date(a.date));

    // Add each purchase to the table
    purchases.forEach((purchase) => {
      const date = new Date(purchase.date);
      const formattedDate =
        date.toLocaleDateString("en-US", {
          year: "numeric",
          month: "short",
          day: "numeric"
        }) +
        " " +
        date.toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit"
        });

      const row = document.createElement("div");
      row.className = "billing-row";
      row.innerHTML = `
        <div class="billing-cell">${formattedDate}</div>
        <div class="billing-cell">${purchase.description || "N/A"}</div>
        <div class="billing-cell">$${parseFloat(purchase.amount).toFixed(
          2
        )}</div>
        <div class="billing-cell">
          <span class="status-${purchase.status.toLowerCase()}">${
        purchase.status
      }</span>
        </div>
        <div class="billing-cell">
          ${
            purchase.details
              ? `<button class="details-btn" data-details='${JSON.stringify(
                  purchase.details
                )}'>View Details</button>`
              : "N/A"
          }
        </div>
      `;

      historyContainer.appendChild(row);
    });

    // Add event listeners to "Details" buttons
    document.querySelectorAll(".details-btn").forEach((button) => {
      button.addEventListener("click", function () {
        const details = JSON.parse(this.getAttribute("data-details"));
        showPurchaseDetails(details);
      });
    });
  }

  // Function to show purchase details in a modal
  function showPurchaseDetails(details) {
    const modal = document.getElementById("details-modal");
    const modalContent = document.getElementById("details-modal-content");

    if (!modal || !modalContent) return;

    // Clear previous details
    modalContent.innerHTML = "";

    if (details.length === 0) {
      modalContent.innerHTML = "<p>No details available for this purchase.</p>";
    } else {
      const list = document.createElement("ul");
      details.forEach((item) => {
        const listItem = document.createElement("li");
        listItem.textContent = `${item.product} - Quantity: ${
          item.quantity
        }, Price: $${item.price.toFixed(2)}`;
        list.appendChild(listItem);
      });
      modalContent.appendChild(list);
    }

    // Show the modal
    modal.style.display = "block";
  }

  // Close modal when clicking outside or on close button
  document.addEventListener("click", (event) => {
    const modal = document.getElementById("details-modal");
    if (
      modal &&
      (event.target === modal || event.target.classList.contains("close-modal"))
    ) {
      modal.style.display = "none";
    }
  });

  // Initialize profile data with preserved profile picture
  loadAccountData(true);
  
  // Try to restore profile picture from localStorage
  restoreProfilePicture();

  // Cancel edit button (switches back to view mode)
  const cancelEditBtn = document.getElementById("cancel-edit-btn");
  if (cancelEditBtn) {
    cancelEditBtn.addEventListener("click", function () {
      toggleProfileMode(false);
    });
  }

  // Handle the "Edit Profile" button in the profile view
  if (editProfileBtn) {
    editProfileBtn.addEventListener("click", function () {
      // Switch to edit mode
      toggleProfileEditMode(true);
    });
  }

  // Toggle submenu visibility
  document.querySelectorAll(".sidebar-item").forEach((item) => {
    item.addEventListener("click", function () {
      const submenu = this.nextElementSibling;
      const allSubmenus = document.querySelectorAll(".submenu");
      const allToggleItems = document.querySelectorAll(
        '.sidebar-item[data-toggle="submenu"]'
      );
      document.querySelectorAll(".sidebar-item").forEach((sidebarItem) => {
        sidebarItem.classList.remove("active");
      });
      // Toggle active state for the clicked item
      this.classList.toggle("active");

      // If submenu is already visible, hide it
      if (submenu.style.display === "block") {
        submenu.style.display = "none";
        return;
      }

      // Hide all submenus
      allSubmenus.forEach((menu) => {
        menu.style.display = "none";
      });

      // Remove active class from all toggle items
      allToggleItems.forEach((toggleItem) => {
        if (toggleItem !== this) {
          toggleItem.classList.remove("active");
        }
      });

      // Show the clicked submenu
      if (submenu && submenu.classList.contains("submenu")) {
        submenu.style.display = "block";
      }
    });
  });

  // Handle sidebar item clicks
  document
    .querySelectorAll('.sidebar-item:not([data-toggle="submenu"])')
    .forEach((item) => {
      item.addEventListener("click", function () {
        // Remove active class from all sidebar items
        document.querySelectorAll(".sidebar-item").forEach((sidebarItem) => {
          sidebarItem.classList.remove("active");
        });

        // Add active class to clicked item
        this.classList.add("active");
        // Hide all sections
        document.querySelectorAll(".settings-section").forEach((section) => {
          section.classList.remove("active");
        });

        // Show the selected section
        const targetId = this.getAttribute("data-target");
        const targetSection = document.getElementById(targetId);
        if (targetSection) {
          targetSection.classList.add("active");
        }
      });
    });

  // Handle submenu item clicks
  document.querySelectorAll(".submenu-item").forEach((item) => {
    item.addEventListener("click", function () {
      // Remove active class from all submenu items
      document.querySelectorAll(".submenu-item").forEach((submenuItem) => {
        submenuItem.classList.remove("active");
      });

      // Add active class to clicked item
      this.classList.add("active");

      // Hide all sections
      document.querySelectorAll(".settings-section").forEach((section) => {
        section.classList.remove("active");
      });

      // Show the selected section
      const targetId = this.getAttribute("data-target");
      const targetSection = document.getElementById(targetId);
      if (targetSection) {
        targetSection.classList.add("active");
      }
    });
  });

  // Profile form submission
  const profileForm = document.getElementById("profile-form");
  if (profileForm) {
    profileForm.addEventListener("submit", (event) => {
      event.preventDefault();

      const fullName = document.getElementById("full-name").value;
      const email = document.getElementById("email").value;
      const phone = document.getElementById("phone").value; // Optional field

      // Validate required fields
      if (!fullName.trim()) {
        showNotification("Error", "Full name is required", "error");
        return;
      }

      if (!email.trim()) {
        showNotification("Error", "Email is required", "error");
        return;
      }

      const profileData = {
        full_name: fullName,
        email: email,
        phone: phone || null // Allow phone to be null if not provided
      };

      updateProfile(profileData)
        .then((data) => {
          if (data.message) {
            showNotification(
              "Success",
              "Profile updated successfully!",
              "success"
            );
            
            // Update the display values in the read-only view
            document.getElementById("display-full-name").textContent =
              fullName || "Not provided";
            document.getElementById("display-email").textContent =
              email || "Not provided";
            document.getElementById("display-phone").textContent =
              phone || "Not provided";
            
            // Switch back to view mode
            toggleProfileEditMode(false);
            
            // Ensure profile section is active and visible
            document.querySelectorAll(".settings-section").forEach((section) => {
              section.classList.remove("active");
            });
            const profileSection = document.getElementById("profile-section");
            if (profileSection) {
              profileSection.classList.add("active");
              profileSection.style.display = "block";
            }
            
            // Update sidebar active state
            document.querySelectorAll(".sidebar-item").forEach((item) => {
              item.classList.remove("active");
            });
            const profileButton = document.querySelector('.sidebar-item[data-target="profile-section"]');
            if (profileButton) {
              profileButton.classList.add("active");
            }
            
            // Hide form and show profile info
            const profileForm = document.getElementById("profile-form");
            const profileInfoCard = document.querySelector(".profile-info-card");
            const profileActions = document.querySelector(".profile-actions");
            
            if (profileForm) profileForm.style.display = "none";
            if (profileInfoCard) profileInfoCard.style.display = "block";
            if (profileActions) profileActions.style.display = "flex";
            
            // Hide upload button and profile pic overlay
            const uploadButton = document.getElementById("upload-pic");
            const profilePicOverlay = document.querySelector(".profile-pic-overlay");
            if (uploadButton) uploadButton.style.display = "none";
            if (profilePicOverlay) profilePicOverlay.style.display = "none";
            
            // Hide required field indicators
            const requiredFields = document.querySelectorAll(".required-profile");
            requiredFields.forEach((field) => {
              field.style.display = "none";
            });
          } else {
            showNotification("Error", "Failed to update profile", "error");
          }
        })
        .catch((error) => {
          console.error("Error:", error);
          showNotification(
            "Error",
            "An error occurred while updating profile",
            "error"
          );
        });
    });
  }

  const toggleProfileEditMode = (isEditMode) => {
    const profileSection = document.getElementById("profile-section");
    const profileForm = document.getElementById("profile-form");
    const profileInfoCard = document.querySelector(".profile-info-card");
    const profileActions = document.querySelector(".profile-actions");
    const uploadButton = document.getElementById("upload-pic");
    const profilePicOverlay = document.querySelector(".profile-pic-overlay");
    const formFields = profileForm.querySelectorAll("input, textarea");

    // Toggle between view and edit modes
    if (isEditMode) {
      // Switch to edit mode - show form and hide info card
      profileForm.style.display = "block";
      profileInfoCard.style.display = "none";
      profileActions.style.display = "none";

      formFields.forEach((field) => {
        field.disabled = false;
      });

      // Show upload button and profile pic overlay
      if (uploadButton) uploadButton.style.display = "inline-block";
      if (profilePicOverlay) profilePicOverlay.style.display = "flex";

      // Load account data but preserve profile picture
      loadAccountData(true);
    } else {
      // Switch back to view mode
      profileForm.style.display = "none";
      profileInfoCard.style.display = "block";
      profileActions.style.display = "flex";

      // Update display values before switching back to view mode
      const fullNameInput = document.getElementById("full-name");
      const emailInput = document.getElementById("email");
      const phoneInput = document.getElementById("phone");

      if (fullNameInput && document.getElementById("display-full-name")) {
        document.getElementById("display-full-name").textContent =
          fullNameInput.value || "Not provided";
      }

      if (emailInput && document.getElementById("display-email")) {
        document.getElementById("display-email").textContent =
          emailInput.value || "Not provided";
      }

      if (phoneInput && document.getElementById("display-phone")) {
        document.getElementById("display-phone").textContent =
          phoneInput.value || "Not provided";
      }

      // Hide upload button and profile pic overlay
      if (uploadButton) uploadButton.style.display = "none";
      if (profilePicOverlay) profilePicOverlay.style.display = "none";

      // Load account data but preserve profile picture
      loadAccountData(true);
    }

    // Show or hide required indicators based on mode
    const requiredFields = profileSection.querySelectorAll(".required-profile");
    requiredFields.forEach((field) => {
      field.style.display = isEditMode ? "inline" : "none";
    });
  };

  // Handle "Profile" button (non-edit mode)
  const profileButton = document.querySelector(
    '.sidebar-item[data-target="profile-section"]'
  );
  if (profileButton) {
    profileButton.addEventListener("click", function () {
      // Switch to non-edit mode
      toggleProfileEditMode(false);
    });
  }

  // Handle "Edit Profile" submenu item (editable mode)
  const editProfileButton = document.querySelector(
    '.submenu-item[data-target="profile-section"]'
  );
  if (editProfileButton) {
    editProfileButton.addEventListener("click", function () {
      // Make sure the profile section is active
      document.querySelectorAll(".settings-section").forEach((section) => {
        section.classList.remove("active");
      });
      const profileSection = document.getElementById("profile-section");
      if (profileSection) {
        profileSection.classList.add("active");
      }

      // Switch to edit mode
      toggleProfileEditMode(true);

      // Mark this submenu item as active
      document.querySelectorAll(".submenu-item").forEach((item) => {
        item.classList.remove("active");
      });
      this.classList.add("active");
    });
  }
  
  async function redirect_to_login()
  {
    try {
      const response = await fetch("/logout", { method: "GET" });
      const result = await response.json();
      if (response.ok) {
        window.location.href = result.redirect_url || "/signin";
      } else {
        console.error("Logout failed:", result.message);
        alert("Failed to log out. Please try again.");
      }
    } catch (error) {
      console.error("Error during logout:", error);
      alert("An error occurred. Please try again.");
    }
  }

  // Delete account form submission
  const deleteForm = document.querySelector(".delete-form");
  if (deleteForm) {
    deleteForm.addEventListener("submit", (event) => {
      event.preventDefault();

      const confirmText = document.getElementById("delete-confirm").value;
      const email = document.getElementById("delete-email").value;

      if (confirmText !== "DELETE") {
        showNotification(
          "Error",
          "Please type DELETE to confirm account deletion",
          "error"
        );
        return;
      }

      if (!email) {
        showNotification(
          "Error",
          "Email is required to delete your account",
          "error"
        );
        return;
      }

      const confirmData = {
        deleteConfirm: confirmText,
        deleteEmail: email,
      };

      console.log("Confirm data:", confirmData); // debugging log

      deleteUserAccount(confirmData)
        .then((data) => {
          if (data.message) {
            showNotification(
              "Success",
              "Account deleted successfully",
              "success"
            );
            // Redirect to logout or home page after successful deletion
            if (data.redirect) {
              redirect_to_login();
            }
          } else {
            showNotification("Error", "Failed to delete account", "error");
          }
        })
        .catch((error) => {
          console.error("Error:", error);
          showNotification(
            "Error",
            "An error occurred while deleting account",
            "error"
          );
        });
    });
  }

  // Function to handle account deletion
  async function handleDeleteAccount(event) {
    event.preventDefault();
    const email = deleteEmailInput ? deleteEmailInput.value : null; // Get email from input

    if (!email) {
      showNotification(
        "Error",
        "Please enter your email to confirm deletion.",
        "error"
      );
      return;
    }

    // Show loading state on confirm button
    if (confirmDeleteBtn) {
      confirmDeleteBtn.disabled = true;
      confirmDeleteBtn.innerHTML =
        '<i class="fas fa-spinner fa-spin"></i> Deleting...';
    }

    try {
      // Call the imported deleteAccount function
      const response = await deleteAccount({ email: email });
      showNotification(
        "Success",
        response.message || "Account deleted successfully.",
        "success"
      );

      // Redirect to signin page after successful deletion
      setTimeout(() => {
        window.location.href = "/signin";
      }, 2000);
    } catch (error) {
      console.error("Error deleting account:", error);
      showNotification(
        "Error",
        `Error deleting account: ${error.message}`,
        "error"
      );
      // Restore button state on error
      if (confirmDeleteBtn) {
        confirmDeleteBtn.disabled = false;
        confirmDeleteBtn.innerHTML = "Confirm Deletion";
      }
    } finally {
      // Ensure popup is hidden even if redirect fails or takes time
      if (deleteConfirmationPopup)
        deleteConfirmationPopup.style.display = "none";
      if (deleteEmailInput) deleteEmailInput.value = ""; // Clear email input
    }
  }

  // Subscribe to newsletter
  const subscribeForm = document.querySelector(".subscription-form");
  if (subscribeForm) {
    subscribeForm.addEventListener("submit", (event) => {
      event.preventDefault();

      const email = document.getElementById("subscription-email").value;

      if (!email) {
        showNotification("Error", "Email is required to subscribe", "error");
        return;
      }

      subscribeUser(email)
        .then((data) => {
          if (data.message) {
            showNotification(
              "Success",
              "Successfully subscribed to newsletter!",
              "success"
            );
          } else {
            showNotification("Error", "Failed to subscribe", "error");
          }
        })
        .catch((error) => {
          console.error("Error:", error);
          showNotification(
            "Error",
            "An error occurred while subscribing",
            "error"
          );
        });
    });
  }

  // Profile picture upload
  if (profilePicOverlay) {
    profilePicOverlay.addEventListener("click", triggerFileUpload);
  } else {
    console.warn("Profile picture overlay not found."); // Add warning
  }

  if (uploadButton) {
    uploadButton.addEventListener("click", triggerFileUpload);
  } else {
    console.warn("Upload button not found."); // Add warning
  }

  // Add event listener for the file input change
  if (profilePicInput) {
    profilePicInput.addEventListener("change", handleFileSelect);
  } else {
    console.error(
      "Profile picture input element not found for change listener!"
    ); // Add error log
  }

  // Initialize the first section as active
  const firstSection = document.querySelector(".settings-section");
  if (firstSection) {
    firstSection.classList.add("active");
  }

  const firstSidebarItem = document.querySelector(
    '.sidebar-item:not([data-toggle="submenu"])'
  );
  if (firstSidebarItem) {
    firstSidebarItem.classList.add("active");
  }

  // Add this function to fetch and update credits
  fetchStoreCredits();

  // Load purchases when the purchases section is opened
  const purchasesNavItem = document.querySelector(
    'li[data-target="settings-purchases"]'
  );
  if (purchasesNavItem) {
    purchasesNavItem.addEventListener("click", () => {
      loadPurchaseHistory(); // Changed from fetchPurchaseHistory to loadPurchaseHistory
    });
  }

  // Also add this to check if we're already on the purchases page and need to load data
  if (
    document.getElementById("settings-purchases") &&
    document.getElementById("settings-purchases").classList.contains("active")
  ) {
    loadPurchaseHistory(); // Changed from fetchPurchaseHistory to loadPurchaseHistory
  }

  // Function to handle section activation
  function activateSection(sectionId) {
    // Hide all sections and remove active class from all sidebar items
    document
      .querySelectorAll(".settings-section")
      .forEach((section) => section.classList.remove("active"));
    document
      .querySelectorAll(".sidebar-item")
      .forEach((item) => item.classList.remove("active"));

    // Show the target section and mark the corresponding sidebar item as active
    const targetSection = document.getElementById(sectionId);
    const targetSidebarItem = document.querySelector(
      `.sidebar-item[data-target="${sectionId}"]`
    );

    if (targetSection && targetSidebarItem) {
      targetSection.classList.add("active");
      targetSidebarItem.classList.add("active");

      // Fetch purchase history if the "Purchases" section is activated
      if (sectionId === "settings-purchases") {
        loadPurchaseHistory(); // Changed from fetchPurchaseHistory to loadPurchaseHistory
        loadCreditHistory(); // Fetch and display credit history
      }
    }
  }

  // Automatically open the section specified in localStorage
  const activeSection = localStorage.getItem("activeAccountSection");
  if (activeSection) {
    activateSection(activeSection);
    localStorage.removeItem("activeAccountSection");
  }

  // Handle sidebar item clicks
  document
    .querySelectorAll('.sidebar-item:not([data-toggle="submenu"])')
    .forEach((item) => {
      item.addEventListener("click", function () {
        const targetId = this.getAttribute("data-target");
        activateSection(targetId);
      });
    });

  // Add a function to restore profile picture if needed
  function restoreProfilePicture() {
    const savedUrl = localStorage.getItem('lastProfilePicUrl');
    if (savedUrl && profilePic) {
      profilePic.src = savedUrl;
    }
  }
});

// Function to toggle between view and edit modes
function toggleProfileMode(isEditMode) {
  const profileInfoCard = document.querySelector(".profile-info-card");
}
