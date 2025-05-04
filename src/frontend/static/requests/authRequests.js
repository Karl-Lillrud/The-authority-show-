export async function signin(email, remember) {
  try {
    const response = await fetch(`/signin`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, remember })
    });

    const result = await response.json();
    return result.redirect_url || "/podprofile"; // Redirect to /podprofile
  } catch (error) {
    throw new Error(error.message);
  }
}

export async function registerTeamMember(email, fullName, phone, inviteToken) {
  try {
    const response = await fetch(`/register-team-member`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, fullName, phone, inviteToken }) // Include invite token
    });

    if (!response.ok) {
      const result = await response.json();
      throw new Error(result.error || "Failed to register.");
    }

    const result = await response.json();

    // If registration is successful, automatically redirect
    return result.redirect_url || "/dashboard";
  } catch (error) {
    throw new Error(error.message);
  }
}

/**
 * Sends the activation token to the backend API to activate the user.
 * @param {string} token - The activation token from the URL.
 * @returns {Promise<object>} - The result from the backend API.
 */
async function activateUserWithToken(token) {
  console.log(
    "Attempting to activate user with token:",
    token ? token.substring(0, 10) + "..." : "null"
  );
  try {
    const response = await fetch("/auth/activate-user", {
      // Ensure this matches your backend route
      method: "POST",
      headers: {
        "Content-Type": "application/json"
        // Add any other necessary headers (like CSRF token if applicable)
      },
      body: JSON.stringify({ token: token })
    });

    const result = await response.json();
    console.log("Activation API response:", result);

    if (!response.ok) {
      // Log the error but return the result for the caller to handle
      console.error(
        `Activation failed: ${response.status} ${response.statusText}`,
        result.error || ""
      );
      // Optionally throw an error here if preferred
      // throw new Error(result.error || `HTTP error! status: ${response.status}`);
    }

    return result; // Return the JSON result (contains message/error and potentially redirect_url)
  } catch (error) {
    console.error("Network or other error during activation:", error);
    // Return an error object consistent with the API response structure
    return { error: `Activation request failed: ${error.message}` };
  }
}

// Add other auth-related request functions here (e.g., login, logout)
// async function loginUser(email) { ... }
// async function logoutUser() { ... }
