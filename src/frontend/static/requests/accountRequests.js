// Fetch profile data
export function fetchProfile() {
  return fetch('/get_profile')
    .then(response => response.json())
    .catch(error => {
      console.error('Error fetching profile data:', error);
      throw new Error('Failed to fetch profile data');
    });
}

// Update profile data
export function updateProfile(profileData) {
  return fetch('/update_profile', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(profileData),
  })
    .then(response => response.json())
    .catch(error => {
      console.error('Error updating profile:', error);
      throw new Error('Failed to update profile');
    });
}

// Fetch account data
export function fetchAccount() {
  return fetch('/get_account')
    .then(response => response.json())
    .catch(error => {
      console.error('Error fetching account data:', error);
      throw new Error('Failed to fetch account data');
    });
}

// Update account data
export function updateAccount(accountData) {
  return fetch('/edit_account', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(accountData),
  })
    .then(response => response.json())
    .catch(error => {
      console.error('Error updating profile:', error);
      throw new Error('Failed to update profile');
    });
}

// Update password
export function updatePassword(passwordData) {
  return fetch('/update_password', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(passwordData),
  })
    .then(response => response.json())
    .catch(error => {
      console.error('Error updating password:', error);
      throw new Error('Failed to update password');
    });
}

// Subscribe user to mailing list
export function subscribeUser(email) {
  return fetch('/subscribe', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  })
    .then(response => response.json())
    .catch(error => {
      console.error('Error subscribing user:', error);
      throw new Error('Failed to subscribe');
    });
}

// Delete user account
export function deleteUserAccount(payload) {
  return fetch("/delete_user", {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
    .then((response) => response.json())
    .catch((error) => {
      console.error("Error deleting user account:", error)
      throw new Error("Failed to delete account")
    })
}
