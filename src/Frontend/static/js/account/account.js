import {
    fetchProfile,
    updateProfile,
    updatePassword,
    deleteUserAccount
  } from "/static/requests/accountRequests.js";

document.addEventListener('DOMContentLoaded', function () {
  fetchProfile() // Fetch the current profile data
    .then(data => {
      if (data && data.full_name && data.email) {
        document.getElementById('full-name').value = data.full_name || '';
        document.getElementById('email').value = data.email || '';
        document.getElementById('phone').value = data.phone || '';
      } else {
        alert('Error fetching profile data');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      alert('Failed to fetch profile data');
    });
});

document.getElementById('profile-form').addEventListener('submit', function (event) {
  event.preventDefault(); // Prevent default form submission

  const fullName = document.getElementById('full-name').value;
  const email = document.getElementById('email').value;
  const phoneNumber = document.getElementById('phone').value;
  const password = document.getElementById('password').value;  // Current password
  const newPassword = document.getElementById('new-password').value;  // New password
  const confirmPassword = document.getElementById('confirm-password').value;  // Confirm new password

  // Validate that new password and confirm password match
  if (newPassword !== confirmPassword) {
    alert("New password and confirm password do not match!");
    return;
  }

  // Validate that passwords are not empty
  if (!password || !newPassword) {
    alert("Please fill in both current and new passwords.");
    return;
  }

  // First, update the profile details (if any details are changed)
  const profileData = {
    full_name: fullName,
    email: email,
    phone: phoneNumber
  };

  updateProfile(profileData)
    .then(data => {
      if (data.message) {
        alert('Profile updated successfully!');
      } else {
        alert('Failed to update profile!');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      alert('Failed to update profile');
    });

  // Then, if the password is updated, call the update_password route
  if (newPassword) {
    const passwordData = {
      current_password: password,
      new_password: newPassword
    };

    updatePassword(passwordData)
      .then(data => {
        if (data.message) {
          alert('Password updated successfully!');
        } else {
          alert('Failed to update password!');
        }
      })
      .catch(error => {
        console.error('Error:', error);
        alert('Failed to update password');
      });
  }
});

document.querySelectorAll(".sidebar-item").forEach((item) => {
    item.addEventListener("click", function () {
      // Remove active class from all items
      document
        .querySelectorAll(".sidebar-item")
        .forEach((i) => i.classList.remove("active"));
      // Add active class to selected item
      this.classList.add("active");
      // Hide all settings sections
      document
        .querySelectorAll(".settings-section")
        .forEach((section) => (section.style.display = "none"));
      // Show selected section
      const target = this.getAttribute("data-target");
      document.getElementById(target).style.display = "block";
      // Adjust the main content container's min-height to match the sidebar's height
      const sidebarHeight = document.querySelector(".sidebar").offsetHeight;
      document.querySelector(".main-content").style.minHeight =
        sidebarHeight + "px";
    });
  });

  // Ensure only the Profile settings are displayed when the page is loaded
document.addEventListener("DOMContentLoaded", function () {
  // Hide all settings sections
  document
    .querySelectorAll(".settings-section")
    .forEach((section) => (section.style.display = "none"));
  // Show the Profile section
  document.getElementById("profile-section").style.display = "block";
  // Set the Profile sidebar item as active
  document
    .querySelectorAll(".sidebar-item")
    .forEach((item) => item.classList.remove("active"));
  document
    .querySelector('.sidebar-item[data-target="profile-section"]')
    .classList.add("active");
});
