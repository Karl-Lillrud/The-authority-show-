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

export async function registerTeamMember(
  email,
  fullName,
  phone,
  inviteToken
) {
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
