// Function to fetch account data
export async function fetchAccount() {
  try {
    // Use the correct endpoint: /api/account
    const response = await fetch("/api/account", { 
      method: "GET",
      headers: { 
        "Accept": "application/json" 
      },
      credentials: "same-origin"
    });

    const contentType = response.headers.get("content-type");
    if (!response.ok) {
      let errorMsg = `Failed to fetch account data: ${response.statusText}`;
      if (contentType && contentType.includes("application/json")) {
        try {
          const errorData = await response.json();
          errorMsg = errorData.error || errorMsg;
        } catch (e) {
          // Ignore if error response is not JSON
        }
      } else if (response.status === 401) {
         errorMsg = "Unauthorized: Please log in.";
      }
      throw new Error(errorMsg);
    }
    
    // Check content type before parsing JSON
    if (contentType && contentType.includes("application/json")) {
        const data = await response.json();
        return data; // Expecting { account: { ... } }
    } else {
        throw new Error("Received non-JSON response from server.");
    }

  } catch (error) {
    console.error("Error in fetchAccount:", error);
    throw new Error(error.message || "Failed to fetch account data");
  }
}

// Update profile data
export function updateProfile(profileData) {
  return fetch('/user/update_profile', {
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

// Function to delete account - Add export keyword
export async function deleteAccount(data) { // data should contain { email: 'user@example.com' }
  try {
    const response = await fetch("/api/account", {
      method: "DELETE",
      headers: { 
        "Content-Type": "application/json",
        "Accept": "application/json" 
      },
      // Send only the email in the body
      body: JSON.stringify({ email: data.email }), 
      credentials: "same-origin"
    });

    const contentType = response.headers.get("content-type");
     if (!response.ok) {
       let errorMsg = `Failed to delete account: ${response.statusText}`;
       if (contentType && contentType.includes("application/json")) {
         try {
           const errorData = await response.json();
           errorMsg = errorData.error || errorMsg;
         } catch (e) {}
       } else if (response.status === 401) {
          errorMsg = "Unauthorized: Please log in.";
       } else if (response.status === 400) {
          // Handle specific bad request errors like incorrect email
          try {
            const errorData = await response.json();
            errorMsg = errorData.error || "Incorrect email provided for deletion.";
          } catch (e) {
             errorMsg = "Incorrect email provided for deletion.";
          }
       }
       throw new Error(errorMsg);
    }
    
    if (contentType && contentType.includes("application/json")) {
       const responseData = await response.json();
       return responseData;
    } else {
        if (response.status === 204 || response.status === 200) {
            return { message: "Account deleted successfully" }; 
        }
       throw new Error("Received unexpected response format from server after delete.");
    }
  } catch (error) {
    console.error("Error deleting account:", error);
    throw error;
  }
}

// Function to upload profile picture
export async function uploadProfilePicture(file) {
  const formData = new FormData();
  formData.append('profilePic', file); // 'profilePic' should match the name expected by the backend

  try {
    const response = await fetch("/api/account/profile-picture", {
      method: "POST",
      body: formData,
      credentials: "same-origin",
      // Note: Don't set Content-Type header manually for FormData, 
      // the browser will set it correctly with the boundary.
      headers: {
        "Accept": "application/json" 
      }
    });

    const contentType = response.headers.get("content-type");
    if (!response.ok) {
      let errorMsg = `Failed to upload profile picture: ${response.statusText}`;
      if (contentType && contentType.includes("application/json")) {
        try {
          const errorData = await response.json();
          errorMsg = errorData.error || errorMsg;
        } catch (e) {}
      } else if (response.status === 401) {
         errorMsg = "Unauthorized: Please log in.";
      }
      throw new Error(errorMsg);
    }
    
    if (contentType && contentType.includes("application/json")) {
       const data = await response.json();
       return data; // Expecting { message: "...", profilePicUrl: "..." }
    } else {
       throw new Error("Received non-JSON response from server after upload.");
    }

  } catch (error) {
    console.error("Error uploading profile picture:", error);
    throw error; // Re-throw to be caught by the calling function in account.js
  }
}
