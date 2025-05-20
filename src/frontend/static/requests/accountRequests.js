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

// Function to fetch profile (user) data
export async function getProfile() {
  try {
    const response = await fetch("/user/get_profile", { 
      method: "GET",
      headers: { 
        "Accept": "application/json" 
      },
      credentials: "same-origin"
    });

    const contentType = response.headers.get("content-type");
    if (!response.ok) {
      let errorMsg = `Failed to get profile data: ${response.statusText}`;
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
        return data; // Expecting { user: { ... } }
    } else {
        throw new Error("Received non-JSON response from server.");
    }

  } catch (error) {
    console.error("Error in getProfile:", error);
    throw new Error(error.message || "Failed to get profile data");
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
  return fetch('/api/account', { // Corrected endpoint
    method: 'PUT',
    headers: { 
      'Content-Type': 'application/json',
      // Add any necessary auth headers like CSRF tokens if your app uses them
    },
    body: JSON.stringify(accountData),
  })
  .then(async response => {
    if (!response.ok) {
      // Attempt to get more detailed error message from response body
      let errorMsg = `HTTP error! status: ${response.status}`;
      try {
        // Try to parse as JSON first, as backend might send structured errors
        const errorData = await response.json();
        errorMsg = errorData.error || errorData.message || errorMsg;
      } catch (e) {
        // If not JSON, try to read as text (e.g., for HTML error pages)
        try {
          const textError = await response.text();
          // Avoid setting a very long HTML page as the error message
          errorMsg = textError.length < 200 ? textError : errorMsg; 
        } catch (textE) {
          // Fallback if reading text also fails
        }
      }
      console.error('Error updating profile (response not ok):', errorMsg);
      throw new Error(errorMsg); // Throw an error with a more descriptive message
    }
    // If response is OK, then parse JSON
    return response.json();
  })
  .catch(error => {
    // This catch block handles network errors or errors thrown from the .then block
    console.error('Error updating profile (network or parsing error):', error);
    // Re-throw the error so the calling function can also catch it
    // Ensure the error is an Error object
    if (error instanceof Error) {
        throw error;
    } else {
        throw new Error(String(error));
    }
  });
}

export async function incrementUpdateAccount(accountData) {
  return await fetch('/api/account/edit_account/increment', {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(accountData)
  })
    .then(response => response.json())
    .catch(error => {
      console.error('Error updating account:', error);
      throw new Error('Failed to update account');
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
  return fetch("/user/delete_user", {
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
