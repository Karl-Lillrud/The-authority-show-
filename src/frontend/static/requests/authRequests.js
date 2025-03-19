export async function signin(email, password, remember) {
  try {
    const response = await fetch(`/signin`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, remember })
    });

    if (!response.ok) {
      throw new Error("Invalid email or password.");
    }

    const result = await response.json();
    return result.redirect_url || "/dashboard";
  } catch (error) {
    throw new Error(error.message);
  }
}

export async function register(email, password) {
  try {
    const response = await fetch(`/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    if (response.ok) {
      // Automatically log in the user
      const loginResponse = await fetch(`/signin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });

      if (!loginResponse.ok) {
        throw new Error("Registration successful, but failed to log in.");
      }

      const loginResult = await loginResponse.json();
      return loginResult.redirect_url || "/dashboard";
    } else {
      const result = await response.json();
      if (result.error === "User already exists") {
        throw new Error("User already exists");
      } else {
        throw new Error(result.error || "An error occurred. Please try again.");
      }
    }
  } catch (error) {
    throw new Error(error.message);
  }
}

export async function registerTeamMember(email, password, fullName, phone, inviteToken) {
  try {
    const response = await fetch(`/register-team-member`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, fullName, phone, inviteToken }) // Include invite token
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


