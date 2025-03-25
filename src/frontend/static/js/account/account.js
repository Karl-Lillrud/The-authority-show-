import {
  fetchProfile,
  updateProfile,
  updatePassword,
  deleteUserAccount,
  subscribeUser,
} from "/static/requests/accountRequests.js"

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

  // Initialize profile data
  fetchProfile()
    .then((data) => {
      if (data) {
        document.getElementById("full-name").value = data.full_name || ""
        document.getElementById("email").value = data.email || ""
        document.getElementById("phone").value = data.phone || ""

        // If name is missing, show a message
        if (!data.full_name) {
          showNotification("Please complete your profile by adding your full name", "warning")
        }

        // If phone is missing, show a message
        if (!data.phone) {
          showNotification("Please add your phone number to complete your profile", "warning")
        }
      } else {
        console.error("Error fetching profile data")
      }
    })
    .catch((error) => {
      console.error("Error:", error)
      showNotification("Failed to load profile data", "error")
    })

  // Toggle submenu visibility
  document.querySelectorAll('.sidebar-item[data-toggle="submenu"]').forEach((item) => {
    item.addEventListener("click", function () {
      const submenu = this.nextElementSibling
      const allSubmenus = document.querySelectorAll(".submenu")
      const allToggleItems = document.querySelectorAll('.sidebar-item[data-toggle="submenu"]')

      // Toggle active state for the clicked item
      this.classList.toggle("active")

      // If submenu is already visible, hide it
      if (submenu.style.display === "block") {
        submenu.style.display = "none"
        document.getElementById("back-to-main-menu").style.display = "none"
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
        document.getElementById("back-to-main-menu").style.display = "flex"
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

  // Back to Main Menu button functionality
  document.getElementById("back-to-main-menu").addEventListener("click", function () {
    // Hide all submenus
    document.querySelectorAll(".submenu").forEach((menu) => {
      menu.style.display = "none"
    })

    // Remove active class from all toggle items
    document.querySelectorAll('.sidebar-item[data-toggle="submenu"]').forEach((item) => {
      item.classList.remove("active")
    })

    // Hide the back button
    this.style.display = "none"
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
      event.preventDefault()

      const fullName = document.getElementById("full-name").value
      const email = document.getElementById("email").value
      const phone = document.getElementById("phone").value

      // Validate required fields
      if (!fullName.trim()) {
        showNotification("Full name is required", "error")
        return
      }

      if (!email.trim()) {
        showNotification("Email is required", "error")
        return
      }

      const profileData = {
        full_name: fullName,
        email: email,
        phone: phone,
      }

      updateProfile(profileData)
        .then((data) => {
          if (data.message) {
            // Changes back to non-edit mode
            document.querySelector('.sidebar-item[data-target="profile-section"]').click();
            const editProfileButton = document.querySelector('.submenu-item[data-target="profile-section"]');
            if (editProfileButton) {
              editProfileButton.classList.remove("active");
            }
            showNotification("Profile updated successfully!", "success")
          } else {
            showNotification("Failed to update profile", "error")
          }
        })
        .catch((error) => {
          console.error("Error:", error)
          showNotification("An error occurred while updating profile", "error")
        })
    })
  }

  const toggleProfileEditMode = (isEditMode) => {
    const profileSection = document.getElementById("profile-section");
    const formFields = profileSection.querySelectorAll("input, textarea");
    const formActions = profileSection.querySelector(".form-actions");
    const uploadButton = document.getElementById("upload-pic");
    const profilePicOverlay = document.querySelector(".profile-pic-overlay");
  
    formFields.forEach(field => field.disabled = !isEditMode);
    formActions.style.display = isEditMode ? 'flex' : 'none';
    uploadButton.style.display = isEditMode ? 'inline-block' : 'none';
    profilePicOverlay.style.display = isEditMode ? 'flex' : 'none';
  
    const formGroups = profileSection.querySelectorAll(".form-group");
    formGroups.forEach(group => {
      const requiredSpan = group.querySelector(".required");
      if (requiredSpan) {
        requiredSpan.style.display = isEditMode && group.querySelector("input").value === "" ? 'inline' : 'none';
      }
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
      // Switch to edit mode
      toggleProfileEditMode(true);
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
        showNotification("Current password is required", "error")
        return
      }

      if (!newPassword) {
        showNotification("New password is required", "error")
        return
      }

      if (newPassword !== confirmPassword) {
        showNotification("New passwords do not match", "error")
        return
      }

      // Check password strength
      const strength = calculatePasswordStrength(newPassword)
      if (strength < 2) {
        showNotification("Password is too weak. Please choose a stronger password.", "error")
        return
      }

      const passwordData = {
        current_password: currentPassword,
        new_password: newPassword,
      }

      updatePassword(passwordData)
        .then((data) => {
          if (data.message) {
            showNotification("Password updated successfully!", "success")
            passwordForm.reset()
          } else {
            showNotification("Failed to update password", "error")
          }
        })
        .catch((error) => {
          console.error("Error:", error)
          showNotification("An error occurred while updating password", "error")
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
      const email = document.getElementById("email").value

      if (confirmText !== "DELETE") {
        showNotification("Please type DELETE to confirm account deletion", "error")
        return
      }

      if (!password) {
        showNotification("Password is required to delete your account", "error")
        return
      }

      if (!email) {
        showNotification("Email is required to delete your account", "error")
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
            showNotification("Account deleted successfully", "success")
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
            showNotification("Failed to delete account", "error")
          }
        })
        .catch((error) => {
          console.error("Error:", error)
          showNotification("An error occurred while deleting account", "error")
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
        showNotification("Email is required to subscribe", "error")
        return
      }

      subscribeUser(email)
        .then((data) => {
          if (data.message) {
            showNotification("Successfully subscribed to newsletter!", "success")
          } else {
            showNotification("Failed to subscribe", "error")
          }
        })
        .catch((error) => {
          console.error("Error:", error)
          showNotification("An error occurred while subscribing", "error")
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

function triggerFileUpload() {
  const fileInput = document.createElement("input")
  fileInput.type = "file"
  fileInput.accept = "image/*"
  fileInput.style.display = "none"

  fileInput.addEventListener("change", function () {
    if (this.files && this.files[0]) {
      const reader = new FileReader()

      reader.onload = (e) => {
        document.getElementById("profile-pic").src = e.target.result

        // Here you would typically upload the file to your server
        // uploadProfilePicture(fileInput.files[0]);
      }

      reader.readAsDataURL(this.files[0])
    }
  })

  document.body.appendChild(fileInput)
  fileInput.click()
  document.body.removeChild(fileInput)
}

function showNotification(message, type) {
  // Create notification element
  const notification = document.createElement("div")
  notification.className = `notification ${type}`
  notification.textContent = message

  // Add notification to the DOM
  document.body.appendChild(notification)

  // Remove notification after 3 seconds
  setTimeout(() => {
    notification.classList.add("fade-out")
    setTimeout(() => {
      document.body.removeChild(notification)
    }, 300)
  }, 3000)
}
