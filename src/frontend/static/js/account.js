document.addEventListener('DOMContentLoaded', function () {
    fetch('/get_profile') // Fetch the current profile data
    .then(response => response.json())
    .then(data => {
        if (data && data.full_name && data.email) {
            // Populate the fields with the current user data
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
  
  document.getElementById('profile-form').addEventListener('submit', function(event) {
    event.preventDefault();  // Prevent default form submission

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

    // Create a flag to track if the password needs to be updated
    let passwordUpdated = false;

    // First, update the profile details (if any details are changed)
    const profileData = {
        full_name: fullName,
        email: email,
        phone: phoneNumber
    };

    // Update the profile first
    fetch('/update_profile', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(profileData)
    })
    .then(response => response.json())
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

        // Call update_password only if new password is entered
        fetch('/update_password', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(passwordData)
        })
        .then(response => response.json())
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