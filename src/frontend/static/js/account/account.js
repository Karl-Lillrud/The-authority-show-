import {
  fetchProfile,
  updateProfile,
  updatePassword,
  deleteUserAccount,
  subscribeUser,
} from "/static/requests/accountRequests.js"
import { showNotification } from "../components/notifications.js";

document.addEventListener("DOMContentLoaded", () => {
    // Hides the edit buttons when in non-edit mode
    const formActions = document.querySelector(".form-actions");
    if (formActions) {
      formActions.style.display = 'none'; 
    }
    const uploadBtn = document.getElementById("upload-pic");
    if (uploadBtn) {
      uploadBtn.style.display = 'none'; 
    }
    const profilePictureOverlay = document.querySelector(".profile-pic-overlay");
    if (profilePictureOverlay) {
      profilePictureOverlay.style.display = 'none'; 
    }

    const requiredFields = document.querySelectorAll(".required-profile");
    requiredFields.forEach(field => {
      field.style.display = 'none';
    });
    
    // Hide the edit profile button in view mode
    const editProfileBtn = document.getElementById("edit-profile-btn");
    if (editProfileBtn) {
      editProfileBtn.style.display = 'none';
    }
    
  // Initialize profile data
  fetchProfile()
    .then((data) => {
      if (data) {
        // Set profile picture
        const profilePic = document.getElementById("profile-pic");
        if (data.profile_picture_url) {
          profilePic.src = data.profile_picture_url; // Use the URL from the server
        } else {
          // Use a hardcoded path instead of Flask template variables
          profilePic.src = "/static/images/profilepic.png"; // Fix the default path
        }

        // Set other profile data
        document.getElementById("full-name").value = data.full_name || "";
        document.getElementById("email").value = data.email || "";
        document.getElementById("phone").value = data.phone || "";

        // Update the display values
        document.getElementById("display-full-name").textContent = data.full_name || "Not provided";
        document.getElementById("display-email").textContent = data.email || "Not provided";
        document.getElementById("display-phone").textContent = data.phone || "Not provided";
      } else {
        console.error("Error fetching profile data");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showNotification("Error", "Failed to load profile data", "error");
    });

  // Cancel edit button (switches back to view mode)
  const cancelEditBtn = document.getElementById("cancel-edit-btn");
  if (cancelEditBtn) {
    cancelEditBtn.addEventListener("click", function() {
      toggleProfileMode(false);
    });
  }

  // Handle the "Edit Profile" button in the profile view
  if (editProfileBtn) {
    editProfileBtn.addEventListener("click", function() {
      // Switch to edit mode
      toggleProfileEditMode(true);
    });
  }

  // Toggle submenu visibility
  document.querySelectorAll('.sidebar-item').forEach((item) => {
    item.addEventListener("click", function () {
      const submenu = this.nextElementSibling
      const allSubmenus = document.querySelectorAll(".submenu")
      const allToggleItems = document.querySelectorAll('.sidebar-item[data-toggle="submenu"]')
      document.querySelectorAll(".sidebar-item").forEach(sidebarItem => {
        sidebarItem.classList.remove('active');
      });
      // Toggle active state for the clicked item
      this.classList.toggle("active")

      // If submenu is already visible, hide it
      if (submenu.style.display === "block") {
        submenu.style.display = "none"
        return
      }

      // Hide all submenus
      allSubmenus.forEach((menu) => {
        menu.style.display = "none"
      })

      // Remove active class from all toggle items
      allToggleItems.forEach((toggleItem) => {
        if (toggleItem !== this) {
          toggleItem.classList.remove("active")
        }
      })

      // Show the clicked submenu
      if (submenu && submenu.classList.contains("submenu")) {
        submenu.style.display = "block"
      }
      
    })
  })

  // Handle sidebar item clicks
  document.querySelectorAll('.sidebar-item:not([data-toggle="submenu"])').forEach((item) => {
    item.addEventListener("click", function () {
      // Remove active class from all sidebar items
      document.querySelectorAll(".sidebar-item").forEach((sidebarItem) => {
        sidebarItem.classList.remove("active")
      })

      // Add active class to clicked item
      this.classList.add("active")
      // Hide all sections
      document.querySelectorAll(".settings-section").forEach((section) => {
        section.classList.remove("active")
      })

      // Show the selected section
      const targetId = this.getAttribute("data-target")
      const targetSection = document.getElementById(targetId)
      if (targetSection) {
        targetSection.classList.add("active")
      }
    })
  })

  // Handle submenu item clicks
  document.querySelectorAll(".submenu-item").forEach((item) => {
    item.addEventListener("click", function () {
      // Remove active class from all submenu items
      document.querySelectorAll(".submenu-item").forEach((submenuItem) => {
        submenuItem.classList.remove("active")
      })

      // Add active class to clicked item
      this.classList.add("active")

      // Hide all sections
      document.querySelectorAll(".settings-section").forEach((section) => {
        section.classList.remove("active")
      })

      // Show the selected section
      const targetId = this.getAttribute("data-target")
      const targetSection = document.getElementById(targetId)
      if (targetSection) {
        targetSection.classList.add("active")
      }
    })
  })

  // Toggle password visibility
  document.querySelectorAll(".toggle-password").forEach((button) => {
    button.addEventListener("click", function () {
      const input = this.previousElementSibling
      const type = input.getAttribute("type") === "password" ? "text" : "password"
      input.setAttribute("type", type)

      // Toggle icon (simplified for this example)
      this.innerHTML =
        type === "password"
          ? '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path><circle cx="12" cy="12" r="3"></circle></svg>'
          : '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"></path><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"></path><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"></path><line x1="2" x2="22" y1="2" y2="22"></line></svg>'
    })
  })

  // Password strength meter
  const newPasswordInput = document.getElementById("new-password")
  if (newPasswordInput) {
    newPasswordInput.addEventListener("input", function () {
      updatePasswordStrength(this.value)
    })
  }

  // Profile form submission
  const profileForm = document.getElementById("profile-form")
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
        phone: phone || null, // Allow phone to be null if not provided
      };

      updateProfile(profileData)
        .then((data) => {
          if (data.message) {
            showNotification("Success", "Profile updated successfully!", "success");
            // Update the display values in the read-only view
            document.getElementById("display-full-name").textContent = fullName || "Not provided";
            document.getElementById("display-email").textContent = email || "Not provided";
            document.getElementById("display-phone").textContent = phone || "Not provided";
            // Switch back to view mode
            toggleProfileMode(false);
          } else {
            showNotification("Error", "Failed to update profile", "error");
          }
        })
        .catch((error) => {
          console.error("Error:", error);
          showNotification("Error", "An error occurred while updating profile", "error");
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
    const formFields = profileForm.querySelectorAll("input, textarea"); // Get form fields from the form itself
    
    // Toggle between view and edit modes
    if (isEditMode) {
      // Switch to edit mode - show form and hide info card
      profileForm.style.display = 'block';
      profileInfoCard.style.display = 'none';
      profileActions.style.display = 'none';
      
      // IMPORTANT - Enable all form fields for editing (removing disabled attribute)
      formFields.forEach(field => {
        field.disabled = false; // Remove disabled attribute
      });
      
      // Show upload button and profile pic overlay
      if (uploadButton) uploadButton.style.display = 'inline-block';
      if (profilePicOverlay) profilePicOverlay.style.display = 'flex';
    } else {
      // Switch back to view mode code remains the same
      profileForm.style.display = 'none';
      profileInfoCard.style.display = 'block';
      profileActions.style.display = 'flex';
      
      // Update display values before switching back to view mode
      const fullNameInput = document.getElementById("full-name");
      const emailInput = document.getElementById("email");
      const phoneInput = document.getElementById("phone");
      
      if (fullNameInput && document.getElementById("display-full-name")) {
        document.getElementById("display-full-name").textContent = fullNameInput.value || "Not provided";
      }
      
      if (emailInput && document.getElementById("display-email")) {
        document.getElementById("display-email").textContent = emailInput.value || "Not provided";
      }
      
      if (phoneInput && document.getElementById("display-phone")) {
        document.getElementById("display-phone").textContent = phoneInput.value || "Not provided";
      }
      
      // Hide upload button and profile pic overlay
      if (uploadButton) uploadButton.style.display = 'none';
      if (profilePicOverlay) profilePicOverlay.style.display = 'none';
    }
    
    // Show or hide required indicators based on mode
    const requiredFields = profileSection.querySelectorAll(".required-profile");
    requiredFields.forEach(field => {
      field.style.display = isEditMode ? 'inline' : 'none';
    });
  }
  
  // Handle "Profile" button (non-edit mode)
  const profileButton = document.querySelector('.sidebar-item[data-target="profile-section"]');
  if (profileButton) {
    profileButton.addEventListener("click", function () {
      // Switch to non-edit mode
      toggleProfileEditMode(false);
    });
  }
  
  // Handle "Edit Profile" submenu item (editable mode)
  const editProfileButton = document.querySelector('.submenu-item[data-target="profile-section"]');
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
      document.querySelectorAll(".submenu-item").forEach(item => {
        item.classList.remove("active");
      });
      this.classList.add("active");
    });
  }

  // Password form submission
  const passwordForm = document.querySelector(".password-form")
  if (passwordForm) {
    passwordForm.addEventListener("submit", (event) => {
      event.preventDefault()

      const currentPassword = document.getElementById("password").value
      const newPassword = document.getElementById("new-password").value
      const confirmPassword = document.getElementById("confirm-password").value

      // Validate password fields
      if (!currentPassword) {
        showNotification("Error", "Current password is required", "error")
        return
      }

      if (!newPassword) {
        showNotification("Error", "New password is required", "error")
        return
      }

      if (newPassword !== confirmPassword) {
        showNotification("Error", "New passwords do not match", "error")
        return
      }

      // Check password strength
      const strength = calculatePasswordStrength(newPassword)
      if (strength < 2) {
        showNotification("Error", "Password is too weak. Please choose a stronger password.", "error")
        return
      }

      const passwordData = {
        current_password: currentPassword,
        new_password: newPassword,
      }

      updatePassword(passwordData)
        .then((data) => {
          if (data.message) {
            showNotification("Success", "Password updated successfully!", "success")
            passwordForm.reset()
          } else {
            showNotification("Error", "Failed to update password", "error")
          }
        })
        .catch((error) => {
          console.error("Error:", error)
          showNotification("Error", "An error occurred while updating password", "error")
        })
    })
  }

  // Delete account form submission
  const deleteForm = document.querySelector(".delete-form")
  if (deleteForm) {
    deleteForm.addEventListener("submit", (event) => {
      event.preventDefault()

      const confirmText = document.getElementById("delete-confirm").value
      const password = document.getElementById("delete-password").value
      const email = document.getElementById("delete-email").value

      if (confirmText !== "DELETE") {
        showNotification("Error", "Please type DELETE to confirm account deletion", "error")
        return
      }

      if (!password) {
        showNotification("Error", "Password is required to delete your account", "error")
        return
      }

      if (!email) {
        showNotification("Error", "Email is required to delete your account", "error")
        return
      }

      const confirmData = {
        deleteEmail: email,
        deletePassword: password,
        deleteConfirm: confirmText,
      }

      deleteUserAccount(confirmData)
        .then((data) => {
          if (data.message) {
            showNotification("Success", "Account deleted successfully", "success")
            // Redirect to logout or home page after successful deletion
            if (data.redirect) {
              setTimeout(() => {
                window.location.href = data.redirect
              }, 2000)
            } else {
              setTimeout(() => {
                window.location.href = "/logout"
              }, 2000)
            }
          } else {
            showNotification("Error", "Failed to delete account", "error")
          }
        })
        .catch((error) => {
          console.error("Error:", error)
          showNotification("Error", "An error occurred while deleting account", "error")
        })
    })
  }

  // Subscribe to newsletter
  const subscribeForm = document.querySelector(".subscription-form")
  if (subscribeForm) {
    subscribeForm.addEventListener("submit", (event) => {
      event.preventDefault()

      const email = document.getElementById("subscription-email").value

      if (!email) {
        showNotification("Error", "Email is required to subscribe", "error")
        return
      }

      subscribeUser(email)
        .then((data) => {
          if (data.message) {
            showNotification("Success", "Successfully subscribed to newsletter!", "success")
          } else {
            showNotification("Error", "Failed to subscribe", "error")
          }
        })
        .catch((error) => {
          console.error("Error:", error)
          showNotification("Error", "An error occurred while subscribing", "error")
        })
    })
  }

  // Profile picture upload
  const profilePicOverlay = document.querySelector(".profile-pic-overlay")
  const uploadButton = document.getElementById("upload-pic")

  if (profilePicOverlay) {
    profilePicOverlay.addEventListener("click", triggerFileUpload)
  }

  if (uploadButton) {
    uploadButton.addEventListener("click", triggerFileUpload)
  }

  // Initialize the first section as active
  const firstSection = document.querySelector(".settings-section")
  if (firstSection) {
    firstSection.classList.add("active")
  }

  const firstSidebarItem = document.querySelector('.sidebar-item:not([data-toggle="submenu"])')
  if (firstSidebarItem) {
    firstSidebarItem.classList.add("active")
  }

  // Calculate password strength
  function calculatePasswordStrength(password) {
    let strength = 0

    if (password.length >= 8) strength++
    if (password.match(/[A-Z]/)) strength++
    if (password.match(/[0-9]/)) strength++
    if (password.match(/[^A-Za-z0-9]/)) strength++

    return strength
  }
})

// Function to toggle between view and edit modes
function toggleProfileMode(isEditMode) {
  const profileInfoCard = document.querySelector(".profile-info-card");
  const profileActions = document.querySelector(".profile-actions");
  const profileForm = document.getElementById("profile-form");
  const profilePicOverlay = document.querySelector(".profile-pic-overlay");
  const uploadButton = document.getElementById("upload-pic");
  
  if (isEditMode) {
    // Switch to edit mode
    profileInfoCard.style.display = "none";
    profileActions.style.display = "none"; // Hide the Edit Profile button
    profileForm.style.display = "block";
    
    // Show photo editing elements
    if (profilePicOverlay) profilePicOverlay.style.display = "flex";
    if (uploadButton) uploadButton.style.display = "inline-block";
  } else {
    // Switch to view mode
    profileInfoCard.style.display = "block";
    profileActions.style.display = "none"; // Keep the Edit Profile button hidden
    profileForm.style.display = "none";
    
    // Hide photo editing elements
    if (profilePicOverlay) profilePicOverlay.style.display = "none";
    if (uploadButton) uploadButton.style.display = "none";
  }
}

// Helper functions
function updatePasswordStrength(password) {
  let strength = 0
  const segments = document.querySelectorAll(".strength-segment")
  const strengthText = document.querySelector(".strength-text")

  if (password.length >= 8) strength++
  if (password.match(/[A-Z]/)) strength++
  if (password.match(/[0-9]/)) strength++
  if (password.match(/[^A-Za-z0-9]/)) strength++

  // Reset all segments
  segments.forEach((segment) => {
    segment.style.backgroundColor = "var(--border)"
  })

  // Update segments based on strength
  for (let i = 0; i < strength; i++) {
    if (segments[i]) {
      if (strength === 1) {
        segments[i].style.backgroundColor = "var(--destructive)"
      } else if (strength === 2) {
        segments[i].style.backgroundColor = "var(--warning)"
      } else if (strength === 3) {
        segments[i].style.backgroundColor = "var(--primary)"
      } else if (strength === 4) {
        segments[i].style.backgroundColor = "var(--success)"
      }
    }
  }

  // Update strength text
  if (strengthText) {
    if (strength === 0) {
      strengthText.textContent = "Too weak"
      strengthText.style.color = "var(--destructive)"
    } else if (strength === 1) {
      strengthText.textContent = "Weak"
      strengthText.style.color = "var(--destructive)"
    } else if (strength === 2) {
      strengthText.textContent = "Fair"
      strengthText.style.color = "var(--warning)"
    } else if (strength === 3) {
      strengthText.textContent = "Good"
      strengthText.style.color = "var(--primary)"
    } else {
      strengthText.textContent = "Strong"
      strengthText.style.color = "var(--success)"
    }
  }
}

function uploadProfilePicture(file) {
  const formData = new FormData();
  formData.append("profile_picture", file);

  fetch("/user/upload_profile_picture", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.url) {
        // Update the profile picture on the page
        const profilePic = document.getElementById("profile-pic");
        profilePic.src = data.url;
        showNotification("Success", "Profile picture updated successfully!", "success");
      } else {
        showNotification("Error", data.error || "Failed to upload profile picture", "error");
      }
    })
    .catch((error) => {
      console.error("Error uploading profile picture:", error);
      showNotification("Error", "An error occurred while uploading profile picture", "error");
    });
}

function triggerFileUpload() {
  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.accept = "image/*";
  fileInput.style.display = "none";

  fileInput.addEventListener("change", function () {
    if (this.files && this.files[0]) {
      uploadProfilePicture(this.files[0]);
    }
  });

  document.body.appendChild(fileInput);
  fileInput.click();
  document.body.removeChild(fileInput);
}

// Attach event listeners to the upload button and overlay
const profilePicOverlay = document.querySelector(".profile-pic-overlay");
const uploadButton = document.getElementById("upload-pic");

if (profilePicOverlay) {
  profilePicOverlay.addEventListener("click", triggerFileUpload);
}

if (uploadButton) {
  uploadButton.addEventListener("click", triggerFileUpload);
}

// Add this to your HTML, inside the profile-pic-container
const profilePicContainer = document.querySelector(".profile-pic-container");
if (profilePicContainer) {
  profilePicContainer.innerHTML = `
    <div class="profile-pic-wrapper">
      <img id="profile-pic" src="{{ url_for('static', filename='images/profilepic.png') }}" alt="Profile Picture">
      <div class="profile-pic-overlay">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="edit-icon">
          <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"></path>
          <path d="M12 20h9"></path>
        </svg>
      </div>
    </div>
    <button id="upload-pic" class="secondary-button">Change Photo</button>
  `;
}
